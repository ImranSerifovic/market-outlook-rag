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
    
    # Sample some documents to see page range
    sample_results = col.get(limit=min(100, count))
    pages_in_index = set()
    if sample_results.get("metadatas"):
        for meta in sample_results["metadatas"]:
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
    print(f"[DEBUG] Retrieved {len(docs)} chunks from pages: {sorted(set(retrieved_pages))}")
    print(f"[DEBUG] Page range: {min(retrieved_pages) if retrieved_pages else 'N/A'} - {max(retrieved_pages) if retrieved_pages else 'N/A'}")

    context_blocks = []
    for d, m in zip(docs, metas):
        context_blocks.append(f"[{m['chunk_id']} | page {m['page']}]\n{d}")

    # 3) Ask LLM (strict grounding + JSON output)
    system = (
    "You are a senior investment analyst at a venture capital firm. "
    "Your task is to answer questions using ONLY the provided report excerpts. "

    "Think like an investor: focus on implications, drivers, constraints, "
    "concentration, growth dynamics, risks, and decision-relevant facts. "

    "You MUST ground every claim in the provided context. "
    "If the answer requires synthesizing information across multiple excerpts, "
    "do so explicitly. "

    "If the report does NOT clearly contain the answer, "
    "set not_found=true and state that the information is not available in the report. "
    "Do NOT infer, estimate, or use outside knowledge. "

    "Always include citations with chunk_id and page number for every factual claim. "
    "Citations must correspond exactly to the provided context. "

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
        "- quote must be a short snippet copied from the context (<= 25 words)\n"
        "- citations must reference only chunk_ids shown in Context\n"
        "- If not_found=true, citations should be an empty array\n"
    )

    llm = oai.chat.completions.create(
        model="gpt-5-mini",  # Fastest model - 2-3x faster than gpt-4.1-mini
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
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

    return AskResponse(**data)