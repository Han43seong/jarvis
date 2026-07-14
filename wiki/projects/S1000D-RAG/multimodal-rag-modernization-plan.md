# S1000D-RAG Multimodal Modernization Plan

> Created for JARVIS planning. Target repo: `$HOME/projects/S1000D-RAG`.

## Goal

Modernize S1000D-RAG from a text-only XML RAG prototype into a local multimodal technical-manual assistant optimized for an RTX 4080 SUPER 16GB VRAM workstation.

## Hardware assumption

- GPU: NVIDIA RTX 4080 SUPER
- VRAM: 16GB
- Practical target: keep the primary runtime below ~13-14GB VRAM to leave room for KV cache, projector, embeddings/reranker, Chroma, web server, and image preprocessing.

## Recommended model stack

### Default production stack, balanced

- Text / main reasoning LLM: `unsloth/Qwen3.6-27B-GGUF`
  - Preferred quant for first bake-off: `Qwen3.6-27B-IQ4_XS.gguf` or `Qwen3.6-27B-IQ4_NL.gguf`
  - Why: better chance to fit 16GB than `Q4_K_M`; strong multilingual/technical capability; natural upgrade from current Qwen3-14B.
  - Caution: `Qwen3.6-27B-Q4_K_M.gguf` is ~15.66 GiB before KV cache, so it is too tight for 16GB full-GPU operation.

- Multimodal vision-language model: `Qwen/Qwen3-VL-8B-Instruct-GGUF` or `unsloth/Qwen3-VL-8B-Instruct-GGUF`
  - Main file: `Qwen3VL-8B-Instruct-Q4_K_M.gguf` or `Qwen3-VL-8B-Instruct-Q4_K_M.gguf` (~4.68 GiB)
  - Projector: `mmproj-Qwen3VL-8B-Instruct-Q8_0.gguf` (~0.70 GiB) or F16 projector (~1.08 GiB)
  - Why: fits 16GB comfortably; can caption/understand figures, diagrams, tables captured as images, and page screenshots.

- Text embedding model: `BAAI/bge-m3`
  - Keep as primary baseline for English S1000D + Korean questions.
  - Alternative bake-off: `Qwen/Qwen3-Embedding-0.6B` for lower memory / Qwen-family consistency.
  - Avoid starting with 4B/8B embedding models on 16GB unless retrieval quality is clearly insufficient.

- Reranker: `BAAI/bge-reranker-v2-m3`
  - Keep as baseline multilingual reranker.
  - Alternative bake-off: `Qwen/Qwen3-Reranker-0.6B`.

### Multimodal-first alternative

- `unsloth/gemma-4-26B-A4B-it-GGUF`
  - `UD-IQ4_NL` ~12.68 GiB, `UD-Q4_K_M` ~15.78 GiB, projector ~1.11 GiB.
  - Good candidate if prioritizing one multimodal family, but `UD-Q4_K_M` is too tight for 16GB with projector/KV cache.
  - If tested, use `UD-IQ4_NL` first.

### Fallback lightweight stack

- Main LLM: `unsloth/Qwen3.5-9B-GGUF` Q5/Q6 or Q8
- VLM: `Qwen3-VL-4B-Instruct-GGUF` or `Qwen3-VL-8B-Instruct-GGUF`
- Use this if 27B IQ quant is too slow or unstable.

## Architecture direction

Do not make the VLM the only model. Use a two-lane architecture:

1. Text lane
   - Parse S1000D XML deterministically.
   - Preserve DMC, issue, language, security, applicability, SNS code, title, structure path, role distribution.
   - Chunk and index text into Chroma.

2. Visual lane
   - Extract or render visual assets from S1000D content:
     - figures / graphics references from XML
     - images in CSDB folders
     - table snapshots or rendered tables if useful
     - optional full-page screenshots/PDF renders later
   - Use VLM to generate structured captions and OCR-like descriptions.
   - Store visual captions as searchable text chunks with `modality=image` and asset metadata.
   - Keep original image paths in metadata for UI evidence display.

3. Fusion retrieval
   - Retrieve text chunks and visual-caption chunks from a single collection or two collections.
   - Rerank combined candidates.
   - Build final context with explicit modality headers.
   - Answer with citations to DMC + chunk + image path when visual evidence is used.

## Known current-code blockers

1. Data path mismatch
   - Current code default: `docs/S1000D Issue 6 Bike Sample Data Set/Bike Data Set for Release number 6 R2`
   - Actual data path: `docs/S1000D Issue 6/Bike Data Set for Release number 6 R2`

2. Extension mismatch
   - Current `LocalCsdbAdapter` scans only `DMC-*.xml`.
   - Actual files are uppercase `.XML`.

3. Text-only data model
   - `ContentBlock` and `S1000DChunk` do not model image references, media assets, modality, or asset paths.

4. Current `langchain_community.llms.LlamaCpp` integration is text-only oriented.
   - Multimodal GGUF requires direct `llama_cpp.Llama` or an OpenAI-compatible llama.cpp server with model + mmproj.

## Implementation phases

### Phase 0: Baseline repair and inventory

Files:
- Modify: `src/config.py`
- Modify: `src/csdb/local_adapter.py`
- Test: `tests/test_csdb.py` or new `tests/test_local_adapter.py`

Tasks:
1. Add `S1000D_DATA_DIR` config defaulting to `docs/S1000D Issue 6/Bike Data Set for Release number 6 R2`.
2. Make `LocalCsdbAdapter.list_data_modules()` scan both `DMC-*.xml` and `DMC-*.XML`.
3. Make `get_data_module_xml()` resolve actual filename case safely.
4. Add tests for uppercase `.XML` and the new default path.
5. Run parser coverage on the 116 Bike Data Set DM files.

Verification:
- `python -m pytest tests/test_local_adapter.py -v`
- `python ingest.py --dry-run` after adding dry-run, or a small parser inventory script.

### Phase 1: Model configuration abstraction

Files:
- Modify: `src/config.py`
- Modify: `src/rag/models.py`
- Create: `src/models_config.py` or `src/runtime/model_registry.py`
- Test: `tests/test_model_config.py`

Tasks:
1. Replace hard-coded single model names with named profiles:
   - `qwen36_27b_iq4`
   - `qwen3_vl_8b_q4`
   - `gemma4_26b_iq4`
   - `light_qwen35_9b`
2. Add env vars:
   - `S1000D_TEXT_MODEL_PROFILE`
   - `S1000D_VLM_MODEL_PROFILE`
   - `S1000D_EMBEDDING_MODEL`
   - `S1000D_RERANKER_MODEL`
   - `S1000D_MODEL_BACKEND` = `llama_cpp_python` or `llama_server`
3. Keep current `.env` ignored; provide `.env.example` with no secrets.
4. Add startup status endpoint fields for model profile, quant, projector, embedding, reranker.

Verification:
- Unit tests parse profiles without loading huge models.
- `/api/status` returns selected profiles.

### Phase 2: Text RAG modernization

Files:
- Modify: `ingest.py`
- Modify: `src/chunker/indexer.py`
- Modify: `src/rag/retriever.py`
- Modify: `src/rag/pipeline.py`
- Test: `tests/test_ingest.py`, `tests/test_rag.py`, `tests/test_e2e.py`

Tasks:
1. Add `--reset-index`, `--dry-run`, `--limit`, and `--include-pattern` to `ingest.py`.
2. Add `source_path`, `filename`, `modality=text`, and `content_role` metadata to documents.
3. Add index manifest JSON with model IDs, embedding model, dimensions, data path, file count, chunk count, timestamp.
4. Add a repeatable evaluation question set under `eval/questions/s1000d_bike.yaml`.
5. Run text-only bake-off: current Qwen3-14B vs Qwen3.6-27B IQ4 vs Gemma4-26B IQ4 if available.

Verification:
- `python ingest.py --dry-run` sees 116 DM files.
- `python ingest.py --reset-index` builds non-empty Chroma index.
- Evaluation report includes answer, citations, retrieved DMCs, latency.

### Phase 3: Visual asset extraction

Files:
- Create: `src/media/asset_extractor.py`
- Create: `src/types/media.py`
- Modify: `src/parser/dm_parser.py`
- Modify: `src/types/dm.py`
- Test: `tests/test_media_extractor.py`, `tests/test_dm_visual_refs.py`

Tasks:
1. Extend parser to collect graphic/figure/table references from XML.
2. Resolve referenced asset files relative to the CSDB directory.
3. Create `VisualAsset` type with:
   - `asset_id`, `dmc`, `source_xml`, `href`, `path`, `mime_type`, `caption`, `title`, `structure_path`.
4. Add CLI command `python ingest.py --extract-assets-only` that writes `chroma_db/assets_manifest.json`.
5. Do not fail ingestion if an asset is missing; record missing assets in manifest.

Verification:
- Asset manifest records found and missing references.
- Tests use small XML fixtures with graphic refs.

### Phase 4: VLM captioning / visual indexing

Files:
- Create: `src/vlm/client.py`
- Create: `src/vlm/captioner.py`
- Create: `scripts/caption_assets.py`
- Modify: `src/chunker/indexer.py`
- Test: `tests/test_visual_documents.py`

Tasks:
1. Implement VLM client abstraction:
   - local `llama_cpp.Llama` path for model + mmproj
   - optional OpenAI-compatible llama.cpp server path
2. Implement deterministic caption prompt for technical-manual images:
   - identify component, labels, warnings, procedures, table values, visible text
   - output JSON with `summary`, `ocr_text`, `components`, `safety_notes`, `keywords`.
3. Store caption outputs under `artifacts/visual_captions/*.json` or `chroma_db/visual_captions/`.
4. Convert visual captions to LangChain Documents with `modality=image`.
5. Index visual caption chunks into Chroma.

Verification:
- Run captioning on 5-10 assets only first.
- Visual chunks are retrievable by Korean and English queries.
- Evidence includes original image path.

### Phase 5: Multimodal query routing and fusion

Files:
- Create: `src/rag/query_router.py`
- Modify: `src/rag/retriever.py`
- Modify: `src/rag/pipeline.py`
- Modify: `src/rag/prompt.py`
- Test: `tests/test_query_router.py`, `tests/test_multimodal_rag.py`

Tasks:
1. Detect visual-intent queries:
   - Korean: `그림`, `도면`, `이미지`, `표`, `사진`, `위치`, `모양`, `라벨`
   - English: `figure`, `diagram`, `image`, `table`, `shown`, `label`.
2. Retrieve both text and visual chunks for all queries, but boost visual chunks when visual intent is detected.
3. Build final prompt with modality headers:
   - `[TEXT DMC=... CHUNK=...]`
   - `[IMAGE_CAPTION DMC=... ASSET=... PATH=...]`
4. Require answers to cite both text and image evidence when image evidence contributed.

Verification:
- Query: “브레이크 관련 그림이나 도면에서 확인할 수 있는 구성품은?” returns image-caption evidence if available.
- Query: “브레이크 패드 교체 절차는?” remains text-first.

### Phase 6: UI/API evidence display

Files:
- Modify: `app_web.py`
- Modify: `static/*` or Streamlit UI files under `src/ui/`
- Test: API tests and manual browser check

Tasks:
1. Extend evidence schema with `modality`, `asset_path`, `asset_thumbnail`, `structure_path`.
2. Add endpoint to serve local visual evidence files safely under an allowlisted data root.
3. Show visual evidence cards in the UI.
4. Add model/status panel showing text model, VLM model, embedding, reranker, chunk counts by modality.

Verification:
- `/api/status` shows text and image chunk counts.
- Chat response can include visual evidence without exposing arbitrary filesystem paths.

### Phase 7: Bake-off and acceptance gate

Files:
- Create: `eval/questions/s1000d_bike.yaml`
- Create: `scripts/eval_rag.py`
- Create: `docs/model-selection-report.md`

Tasks:
1. Evaluate at least these stacks:
   - Qwen3.6-27B IQ4 + BGE-M3 + BGE reranker + Qwen3-VL-8B
   - Gemma4-26B IQ4 + BGE-M3 + BGE reranker + Gemma4 VLM path if stable
   - Lightweight Qwen3.5-9B + Qwen3-VL-8B
2. Measure:
   - answer correctness
   - citation quality
   - Korean answer quality
   - refusal / hallucination rate
   - latency
   - VRAM usage
3. Choose default profile based on evidence.

Verification:
- `docs/model-selection-report.md` contains concrete outputs and recommendation.

## Immediate recommended next action

Implement Phase 0 and Phase 1 first. Do not download models until the ingestion path and model profile abstraction are fixed. After that, download only two candidates for bake-off:

1. `Qwen3.6-27B-IQ4_NL` or `IQ4_XS`
2. `Qwen3-VL-8B-Instruct-Q4_K_M` + projector

Then run evaluation before deciding whether Gemma4-26B should replace Qwen as the default.
