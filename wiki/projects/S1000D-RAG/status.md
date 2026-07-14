# S1000D-RAG Status

> **Historical snapshot:** 이 문서는 just-chill 운영 기록이다. 현재 프로젝트 설명과 검증 수치는 [S1000D-RAG 저장소](https://github.com/Han43seong/S1000D-RAG) 및 [공식 검증 리포트](https://github.com/Han43seong/S1000D-RAG/blob/main/docs/rag_quality_evidence_report.md)를 기준으로 한다.

## Registry

- Status: reference-complete
- Local path: `$HOME/projects/S1000D-RAG`
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
- Completed runtime smoke/eval and documented results in `$HOME/projects/S1000D-RAG/docs/runtime_smoke_eval_report.md`.
- Completed automated regression loop: 100 base scripted questions × 5 cycles = 500 total checks, final `500/500` passed, with 3 fixes recorded during the run. This was not a human answer-quality evaluation.
- Added ontology MVP exports:
  - `src/rag/ontology.py`
  - `scripts/build_ontology_exports.py`
  - `tests/test_s1000d_ontology.py`
  - `ontology/s1000d_ontology_graph.json`
  - `ontology/s1000d_ontology.jsonld`
  - `ontology/s1000d_ontology.ttl`
- Ontology export snapshot verified at 995 nodes / 1918 edges, including Reference, Warning, Caution, Figure, GraphicAsset, and Hotspot nodes.
- Latest pushed commits (origin/main synced):
  - `075c879 [verified] add grounded v4 symptom answers`
  - `7f1209c [verified] preserve longer v4 procedure drafts`
  - `28aaba6 [verified] split v4 Korean composer`
  - `353b64f feat: add v4 RDF graph answer planning`

## Current gate

- All v4 closure commits, including the SPARQL-endpoint failure fallback to local RDF store and README/wiki reference-complete status, are committed and pushed. `main` tracks `origin/main` at `075c879 [verified] add grounded v4 symptom answers` with `ahead/behind = 0/0` (verified 2026-06-14).
- Commit scope continues to exclude local untracked `uv.lock` by user request.
- Latest implementation verification:
  - Full test suite: `321 passed, 5 warnings` (verified 2026-06-14 with miniforge python 3.12).
  - Focused v4/app/UI/runtime-router tests: `88 passed, 2 warnings`.
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

- Application source stays in `$HOME/projects/S1000D-RAG`, not in the JARVIS control-plane repo.
- Do not edit secrets or local model files.
- For implementation work, route medium/large changes through `omx-ralph` unless the user asks otherwise.
