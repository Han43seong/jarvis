# InternalDocRAG Status

## Registry

- Status: active
- Local path: `/home/hskim/projects/InternalDocRAG`
- Remote: `https://github.com/Han43seong/InternalDocRAG.git`
- Visibility: private
- Default executor: `omx-ralph`

## Purpose

Closed-network internal general-employee chatbot for searching past business documents and company information, producing source-grounded summaries, comparisons, and drafting support.

This project starts fresh rather than refactoring `S1000D-RAG`, while reusing its architectural lessons: AnswerPlan, citations, support levels, ontology/graph traces, deterministic fallback, and UI/API metadata exposure.

## Initial implementation

- Created project repo at `/home/hskim/projects/InternalDocRAG`.
- Created private GitHub remote: `https://github.com/Han43seong/InternalDocRAG`.
- Added first TDD slice for business-document metadata validation:
  - `src/internal_doc_rag/metadata.py`
  - `tests/test_document_metadata.py`
- Initial tests: `3 passed`.

## Next work order

1. Add `documents.jsonl` manifest loader and duplicate/required-field validation.
2. Add sample corpus layout and `.env.example` without secrets.
3. Implement enterprise document loaders in priority order: PDF, DOCX, PPTX, XLSX, HWPX/HWP.
4. Add BM25/full-text search alongside future vector search.
5. Add metadata filter store and permission-aware retrieval.
6. Define AnswerPlan intents: `document_search`, `fact_lookup`, `summarization`, `comparison`, `drafting`.

## Operating notes

- Do not commit real internal documents, secrets, private model files, or generated indexes.
- Use sanitized sample documents unless the user explicitly approves real corpus use in the closed-network environment.
- Route medium/large implementation through `omx-ralph` unless the user asks otherwise.
