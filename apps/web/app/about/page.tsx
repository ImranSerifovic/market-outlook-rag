"use client";

import Link from "next/link";

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="mx-auto max-w-4xl px-6 py-12">
        <div className="mb-8">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-zinc-400 hover:text-zinc-200 transition-colors mb-6"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              className="w-5 h-5"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"
              />
            </svg>
            Back to Q&A
          </Link>
          <h1 className="text-5xl font-semibold tracking-tight mb-4">
            How It Works
          </h1>
          <p className="text-lg text-zinc-300">
            A technical overview of the Market Outlook RAG system
          </p>
        </div>

        <div className="space-y-8">
          <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-7">
            <h2 className="text-2xl font-semibold mb-4">Architecture Overview</h2>
            <p className="text-zinc-300 leading-7 mb-4">
              This is a Retrieval-Augmented Generation (RAG) system that allows users to ask
              questions about a PDF document and receive grounded answers with citations.
            </p>
            <div className="space-y-3 text-zinc-300">
              <div className="flex gap-3">
                <span className="text-zinc-500">•</span>
                <span>
                  <strong className="text-zinc-200">Frontend:</strong> Next.js 16 with React 19,
                  deployed on Vercel
                </span>
              </div>
              <div className="flex gap-3">
                <span className="text-zinc-500">•</span>
                <span>
                  <strong className="text-zinc-200">Backend:</strong> FastAPI (Python), deployed on
                  Render
                </span>
              </div>
              <div className="flex gap-3">
                <span className="text-zinc-500">•</span>
                <span>
                  <strong className="text-zinc-200">Vector Database:</strong> ChromaDB for
                  persistent storage of document embeddings
                </span>
              </div>
              <div className="flex gap-3">
                <span className="text-zinc-500">•</span>
                <span>
                  <strong className="text-zinc-200">LLM:</strong> OpenAI GPT-4o-mini for answer
                  generation
                </span>
              </div>
              <div className="flex gap-3">
                <span className="text-zinc-500">•</span>
                <span>
                  <strong className="text-zinc-200">Embeddings:</strong> OpenAI text-embedding-3-small
                  for semantic search
                </span>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-7">
            <h2 className="text-2xl font-semibold mb-4">How It Works</h2>
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-zinc-200 mb-2">1. Document Processing</h3>
                <p className="text-zinc-300 leading-7">
                  The PDF is parsed page-by-page using PyPDF. Each page is then chunked into
                  overlapping segments (~1200 characters) to preserve context across boundaries.
                  These chunks are embedded using OpenAI&apos;s embedding model and stored in
                  ChromaDB with metadata (page number, chunk ID).
                </p>
              </div>

              <div>
                <h3 className="text-lg font-medium text-zinc-200 mb-2">2. Query Processing</h3>
                <p className="text-zinc-300 leading-7">
                  When a user asks a question, the query is embedded using the same embedding model.
                  ChromaDB performs a vector similarity search to retrieve the most relevant chunks
                  (typically 6 chunks). Results are filtered by distance threshold to ensure
                  relevance.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-medium text-zinc-200 mb-2">3. Answer Generation</h3>
                <p className="text-zinc-300 leading-7">
                  The retrieved chunks are sent to GPT-4o-mini along with the user&apos;s question.
                  The model is instructed to ground its answer strictly in the provided context and
                  return structured JSON with citations. Each citation includes the page number and
                  a quote from the source.
                </p>
              </div>

              <div>
                <h3 className="text-lg font-medium text-zinc-200 mb-2">4. Response Display</h3>
                <p className="text-zinc-300 leading-7">
                  The frontend displays the answer, key points, and citations. Users can click on
                  citations to view the relevant page in the PDF viewer, which automatically jumps
                  to the cited page.
                </p>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-7">
            <h2 className="text-2xl font-semibold mb-4">Key Features</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
                <h4 className="font-medium text-zinc-200 mb-2">Grounded Answers</h4>
                <p className="text-sm text-zinc-400">
                  All answers are strictly grounded in the document. If information isn&apos;t found,
                  the system explicitly states so.
                </p>
              </div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
                <h4 className="font-medium text-zinc-200 mb-2">Page-Level Citations</h4>
                <p className="text-sm text-zinc-400">
                  Every answer includes citations with page numbers and direct quotes from the
                  source material.
                </p>
              </div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
                <h4 className="font-medium text-zinc-200 mb-2">Semantic Search</h4>
                <p className="text-sm text-zinc-400">
                  Uses vector embeddings to find semantically similar content, not just keyword
                  matches.
                </p>
              </div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4">
                <h4 className="font-medium text-zinc-200 mb-2">Fast Responses</h4>
                <p className="text-sm text-zinc-400">
                  Optimized for speed with distance filtering, chunk truncation, and efficient
                  model selection.
                </p>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-7">
            <h2 className="text-2xl font-semibold mb-4">Technical Stack</h2>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-zinc-200 mb-2">Frontend</h4>
                <ul className="text-sm text-zinc-400 space-y-1 ml-4">
                  <li>• Next.js 16 (App Router)</li>
                  <li>• React 19</li>
                  <li>• TypeScript</li>
                  <li>• Tailwind CSS</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-zinc-200 mb-2">Backend</h4>
                <ul className="text-sm text-zinc-400 space-y-1 ml-4">
                  <li>• FastAPI (Python)</li>
                  <li>• ChromaDB (vector database)</li>
                  <li>• OpenAI API (GPT-4o-mini, text-embedding-3-small)</li>
                  <li>• PyPDF (PDF parsing)</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-zinc-200 mb-2">Deployment</h4>
                <ul className="text-sm text-zinc-400 space-y-1 ml-4">
                  <li>• Vercel (frontend)</li>
                  <li>• Render (backend)</li>
                  <li>• Docker (containerization)</li>
                </ul>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}

