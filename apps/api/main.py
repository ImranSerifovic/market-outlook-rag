import os
import json
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    # Normalize: browsers send Origin without a trailing slash
    allowed_origins = [o.rstrip("/") for o in raw_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return {
        "status": "ok",
        "chroma_dir": CHROMA_DIR,
        "allowed_origins": allowed_origins,
        "allowed_origins_env": os.getenv("ALLOWED_ORIGINS"),
    }

@app.post("/ask", response_model=AskResponse)
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
        include=["documents", "metadatas"]
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]

    context_blocks = []
    for d, m in zip(docs, metas):
        context_blocks.append(f"[{m['chunk_id']} | page {m['page']}]\n{d}")

    # 3) Ask LLM (strict grounding + JSON output)
    system = (
        "You are a careful analyst. Use ONLY the provided context from the report. "
        "If the answer is not clearly in the context, set not_found=true and say you cannot find it in the report. "
        "Always provide citations using the given chunk_id and page. "
        "Return ONLY valid JSON matching the schema."
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
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
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