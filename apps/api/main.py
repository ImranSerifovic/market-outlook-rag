import os
import json
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

import chromadb
from openai import OpenAI

# Load .env from repo root when present (platform deploys typically inject env vars)
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=False)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY. Set it in the environment (or locally in ROOT/.env).")

oai = OpenAI(api_key=OPENAI_API_KEY)

CHROMA_DIR = os.getenv("CHROMA_DIR", str(ROOT / "storage" / "chroma"))
ch = chromadb.PersistentClient(path=CHROMA_DIR)
col = ch.get_or_create_collection(name="market_outlook")

app = FastAPI(title="Market Outlook RAG API")

# CORS: allow the Next.js frontend (localhost + Vercel). Provide a comma-separated
# list via ALLOWED_ORIGINS, e.g. "http://localhost:3000,https://your-app.vercel.app".
_default_origins = ["http://localhost:3000"]
_allowed = os.getenv("ALLOWED_ORIGINS")

if _allowed and _allowed.strip() == "*":
    allowed_origins = ["*"]
else:
    raw_origins = (
        [o.strip() for o in _allowed.split(",") if o.strip()] if _allowed else _default_origins
    )
    # Normalize: browsers send Origin without a trailing slash, and ensure no extra spaces
    allowed_origins = [o.rstrip("/").strip() for o in raw_origins if o.strip()]

# Debug: log allowed origins (remove in production if sensitive)
print(f"[CORS] Allowed origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["*"],
    max_age=3600,
)

class AskRequest(BaseModel):
    question: str
    top_k: int = Field(default=8, ge=1, le=20)

class Citation(BaseModel):
    chunk_id: str
    page: int
    quote: str

class AskResponse(BaseModel):
    answer: str
    key_points: List[str]
    citations: List[Citation]
    not_found: bool

@app.get("/health")
def health():
    # Get collection stats
    count = col.count()
    
    # Get all documents to see complete page range (may be slow for large indexes)
    all_results = col.get(limit=count)
    pages_in_index = set()
    if all_results.get("metadatas"):
        for meta in all_results["metadatas"]:
            if "page" in meta:
                pages_in_index.add(meta["page"])
    
    return {
        "status": "ok",
        "chroma_dir": CHROMA_DIR,
        "allowed_origins": allowed_origins,
        "allowed_origins_env": os.getenv("ALLOWED_ORIGINS"),
        "collection_count": count,
        "pages_in_index": sorted(list(pages_in_index)) if pages_in_index else [],
        "page_range": f"{min(pages_in_index)}-{max(pages_in_index)}" if pages_in_index else "none",
        "total_pages_indexed": len(pages_in_index),
    }

@app.options("/ask")
@app.options("/api/ask")
async def options_ask():
    """Handle preflight OPTIONS requests - CORS middleware should handle this, but this ensures it works"""
    # Return empty 200 - CORS middleware will add the headers
    return Response(status_code=200)

@app.post("/ask", response_model=AskResponse)
@app.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest):
    # 1) Embed query
    q_emb = oai.embeddings.create(
        model="text-embedding-3-small",
        input=req.question
    ).data[0].embedding

    # 2) Retrieve chunks
    results = col.query(
        query_embeddings=[q_emb],
        n_results=req.top_k,
        include=["documents", "metadatas", "distances"]
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0] if "distances" in results else []

    # Debug: log retrieved pages
    retrieved_pages = [m["page"] for m in metas]
    unique_pages = sorted(set(retrieved_pages))
    print(f"[DEBUG] Retrieved {len(docs)} chunks from pages: {unique_pages}")
    if retrieved_pages:
        print(f"[DEBUG] Retrieved page range: {min(retrieved_pages)} - {max(retrieved_pages)} (out of all indexed pages)")

    context_blocks = []
    for d, m in zip(docs, metas):
        context_blocks.append(f"[{m['chunk_id']} | page {m['page']}]\n{d}")

    # 3) Ask LLM (strict grounding + JSON output)
    system = (
        "You are a senior investment analyst at a venture capital firm. "
        "Answer questions using ONLY the provided report excerpts. "

        "IMPORTANT: Your answer can paraphrase and synthesize information naturally. "
        "The 'answer' field can paraphrase or synthesize for readability, but every factual claim must be grounded in citations. "
        "Citations are required to show sources - the 'quote' field can be a brief summary or reference to the relevant content, not necessarily an exact quote. "

        "Write in a crisp, investor-ready style with analytical depth. "
        "Imagine the reader is an experienced investor who is familiar with the report and the industry. "
        "The 'answer' should be structured to: lead with the main finding, provide reasoning and causal drivers, "
        "include concrete specifics (numbers, trends, mechanisms), and synthesize across excerpts when relevant. "
        "Aim for 3–6 sentences that balance conciseness with depth. "
        "Avoid vague filler (e.g., 'significantly', 'rapidly') unless the context uses it. "

        "The 'key_points' should complement the answer with discrete, actionable insights. "

        "You MUST ground every factual claim in the provided context. "
        "If synthesizing across multiple excerpts, do so explicitly (e.g., 'Across excerpts A and B...'). "

        "CRITICAL CITATION REQUIREMENTS: "
        "You MUST provide citations for EVERY factual claim, statistic, number, or specific detail mentioned in your answer. "
        "If your answer mentions multiple facts from different parts of the context, you MUST cite ALL of them. "
        "Examples: If you mention '$56 billion', '40% increase', 'H1 2025', 'release valve', or any specific concept, "
        "each of these MUST have a corresponding citation pointing to where it appears in the context. "
        "Do NOT cite only one source if your answer synthesizes information from multiple chunks. "
        "Include separate citations for each distinct factual claim or statistic. "

        "Citation format requirements: "
        "- chunk_id must match EXACTLY a chunk_id shown in the Context blocks "
        "- page number must match EXACTLY the page number shown for that chunk_id in Context "
        "- quote can be a brief summary or reference (<= 25 words) describing the relevant content from that chunk "
        "- quote does NOT need to be an exact quote - it can paraphrase or summarize the key point "
        "- Include multiple citations if your answer draws from multiple chunks "

        "If the report does NOT clearly contain the answer, set not_found=true and say you cannot find it in the report. "
        "Do NOT infer, estimate, or use outside knowledge. "
        "Return ONLY valid JSON matching the provided schema." 
    )

    user = (
        f"Question: {req.question}\n\n"
        "Context:\n" + "\n\n".join(context_blocks) + "\n\n"
        "Schema:\n"
        "{"
        "\"answer\": string, "
        "\"key_points\": array of strings, "
        "\"citations\": array of {\"chunk_id\": string, \"page\": number, \"quote\": string}, "
        "\"not_found\": boolean"
        "}\n\n"
        "Constraints:\n"
        "- quote can be a brief summary or reference (<= 25 words) - does NOT need to be exact quote\n"
        "- chunk_id must match EXACTLY a chunk_id shown in the Context blocks above\n"
        "- page number must match EXACTLY the page number shown for that chunk_id in Context\n"
        "- citations must reference only chunk_ids and pages shown in Context\n"
        "- CRITICAL: Every number, statistic, specific fact, or claim in your answer MUST have a citation\n"
        "- If your answer mentions multiple facts from different chunks, include multiple citations (one per fact)\n"
        "- If not_found=true, citations should be an empty array\n"
        "- answer must be 3-6 sentences with structure: main finding → reasoning → specifics\n"
        "- answer should synthesize key_points with analytical depth, not just list facts\n"
    )

    # Use GPT-4o-mini (fastest, most cost-effective available model)
    # Set OPENAI_MODEL env var to override (e.g., "gpt-5-mini" if you have access)
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = oai.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.0,  # Use 0.0 for maximum determinism and to prevent hallucinations
        response_format={"type": "json_object"},  # Forces JSON, faster parsing
    )

    raw = llm.choices[0].message.content.strip()

    # 4) Parse + validate JSON (fail loudly if not JSON)
    try:
        data = json.loads(raw)
    except Exception:
        # If model returns non-JSON, return a safe fallback
        return AskResponse(
            answer="I could not format a valid JSON response.",
            key_points=["Try re-asking the question."],
            citations=[],
            not_found=True,
        )

    # 5) Validate citations: verify chunk_id and page match (quote can be paraphrased)
    if "citations" in data and isinstance(data["citations"], list):
        # Build lookup: chunk_id -> (page, document_text)
        chunk_lookup = {}
        for d, m in zip(docs, metas):
            chunk_lookup[m["chunk_id"]] = (m["page"], d)
        
        validated_citations = []
        for cit in data["citations"]:
            if not isinstance(cit, dict):
                continue
            chunk_id = cit.get("chunk_id")
            page = cit.get("page")
            quote = cit.get("quote", "").strip()
            
            # Verify chunk_id exists and page matches (quote can be paraphrased, so we don't validate it)
            if chunk_id in chunk_lookup:
                expected_page, doc_text = chunk_lookup[chunk_id]
                if page == expected_page:
                    validated_citations.append(cit)
                else:
                    print(f"[WARN] Page mismatch for chunk_id {chunk_id}: expected {expected_page}, got {page}")
            else:
                print(f"[WARN] Invalid chunk_id in citation: {chunk_id}")
        
        data["citations"] = validated_citations

    return AskResponse(**data)