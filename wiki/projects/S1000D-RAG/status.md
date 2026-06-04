# S1000D-RAG Status

## Registry

- Status: active
- Local path: `/home/hskim/projects/S1000D-RAG`
- Remote: `https://github.com/Han43seong/S1000D-RAG.git`
- Default executor: `omx-ralph`

## Purpose

Originally, this project parsed S1000D Data Module XML for structured chunking, vector indexing, and LangChain-based local RAG over manual/MRO data.

As of 2026-06-04, the target direction changed: use the current RAG/ontology work as a reference for a closed-network internal general-employee chatbot focused on past business-document search, company information lookup, source-grounded summaries, comparisons, and drafting support.

Transition plan: `internal-business-chatbot-transition-plan.md`.

## Current snapshot

- Language/runtime: Python >=3.11,<3.13
- Package manager metadata: Poetry (`pyproject.toml`, `poetry.lock`)
- Main components: XML parsing, CSDB adapter, chunker/indexer, retriever/reranker, RAG pipeline, Streamlit/web entrypoints
- Local LLM direction: GGUF/LlamaCpp + HuggingFace embeddings
- Multimodal modernization has local commits through offline model verification, env helper, and runtime smoke/eval stabilization.
- Ontology MVP snapshot/export layer is implemented and independently reviewed as PASS.

## Recent local implementation checkpoints

- Added dependency-light S1000D ingest/model-registry/text-RAG/visual asset/VLM captioning/multimodal routing/context/evidence/model-bakeoff scaffolds.
- Downloaded first-pass local stack under repo-local ignored `models/`:
  - Qwen3.6 27B IQ4_NL text GGUF
  - Qwen3-VL 8B Q4_K_M GGUF + Q8_0 mmproj
  - BGE-M3 embedding model
  - BGE reranker v2 m3
- Added `scripts/verify_local_models.py` and `docs/local_model_stack.md` to verify the local files without loading weights.
- Added `scripts/local_model_env.py` to emit env vars for local runtime smoke/eval.
- Completed runtime smoke/eval and documented results in `/home/hskim/projects/S1000D-RAG/docs/runtime_smoke_eval_report.md`.
- Completed Graph-first retrieval QA and autonomous 500-question validation loop: final `500/500` passed, with 10 mid-loop fixes/rechecks resolved.
- Added ontology MVP exports:
  - `src/rag/ontology.py`
  - `scripts/build_ontology_exports.py`
  - `tests/test_s1000d_ontology.py`
  - `ontology/s1000d_ontology_graph.json`
  - `ontology/s1000d_ontology.jsonld`
  - `ontology/s1000d_ontology.ttl`
- Ontology export snapshot verified at 995 nodes / 1918 edges, including Reference, Warning, Caution, Figure, GraphicAsset, and Hotspot nodes.
- Latest local commits include:
  - `d40babd chore: ignore executor workdirs`
  - `74b22f2 fix: stabilize runtime smoke eval`
  - `d102169 feat: add local model env helper`
  - `58b140f feat: verify local model stack`

## Current gate

- Latest v4 RDF/AnswerPlan implementation was committed and pushed to `origin/main` as `353b64f feat: add v4 RDF graph answer planning`.
- Commit scope excluded local untracked `uv.lock` by user request.
- Latest implementation verification:
  - Full test suite: `300 passed, 5 warnings`.
  - Focused v4/app/UI tests: `52 passed, 2 warnings`.
  - `/api/health` smoke: PASS.
  - `/api/chat` v4 RDFLib smoke: PASS with source-grounded `related` / `deterministic_fallback` behavior.
- Product direction has changed away from strict S1000D/MRO expert operation toward an internal business-document chatbot. The next implementation should not keep adding MRO-specific guards; it should pivot data, metadata, ontology, retrieval, and answer policies to enterprise document search.
- Remaining blockers/gaps for the new direction:
  - Need representative business-document corpus and metadata manifest.
  - Need general document loaders for Korean enterprise formats, especially HWP/HWPX, PDF, DOCX, PPTX, and XLSX.
  - Need hybrid retrieval: vector + BM25/full-text + metadata filters + graph/entity search.
  - Need permission-aware retrieval before answer generation.
  - Need new AnswerPlan intents for document search, fact lookup, summarization, comparison, and drafting.
  - Existing FastAPI `on_event` deprecation warnings and Chroma relevance-score warnings remain cleanup candidates.

## Operating notes

- Application source stays in `/home/hskim/projects/S1000D-RAG`, not in the JARVIS control-plane repo.
- Do not edit secrets or local model files.
- For implementation work, route medium/large changes through `omx-ralph` unless the user asks otherwise.
