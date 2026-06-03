# S1000D-RAG Status

## Registry

- Status: active
- Local path: `/home/hskim/projects/S1000D-RAG`
- Remote: `https://github.com/Han43seong/S1000D-RAG.git`
- Default executor: `omx-ralph`

## Purpose

S1000D Data Module XML을 파싱하여 구조적 청킹, 벡터 인덱싱, LangChain 기반 RAG 파이프라인을 구성하는 로컬 LLM 프로젝트.

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

- S1000D-RAG repo is locally ahead of `origin/main`; push is not approved yet.
- Runtime smoke/eval is complete on the current WSL environment:
  - Model file/env check: PASS (`15/15` required artifacts present)
  - Embedding load: PASS (`bge-m3`, CPU)
  - Reranker load: PASS (`bge-reranker-v2-m3`, CPU)
  - Chroma ingest/retrieval smoke: PASS
  - Text LLM load/generation: PASS with CPU-only `llama-cpp-python`
  - End-to-end RAG+LLM smoke: PASS, but slow (~108s for one short answer on CPU)
  - Full tests from the runtime-smoke checkpoint: `148 passed, 3 warnings`
- Latest ontology/Graph-first verification:
  - Autonomous 500 QA loop: final `500/500` passed.
  - Focused ontology + graph retrieval tests: `12 passed`.
  - Broader ontology/graph/RAG/query/model suite: `96 passed`.
  - Ontology exports rebuilt successfully with 995 nodes and 1918 edges.
  - Independent Reviewer: `PASS`, no blocking findings.
- Remaining blockers/gaps:
  - GPU offload is not active because installed `llama-cpp-python 0.3.23` reports CPU-only backend.
  - Qwen3-VL files and mmproj are present, but image inference adapter is not yet implemented/executed.
  - Chroma score normalization still emits warnings for negative distance-like scores; pipeline now has a safe fallback but retrieval score semantics should be normalized later.
  - Ontology Turtle export is currently Turtle-like; strict RDF import should later normalize IDs/namespaces to declared prefixes or absolute IRIs.

## Operating notes

- Application source stays in `/home/hskim/projects/S1000D-RAG`, not in the JARVIS control-plane repo.
- Do not edit secrets or local model files.
- For implementation work, route medium/large changes through `omx-ralph` unless the user asks otherwise.
