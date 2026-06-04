# S1000D-RAG Decisions

## 2026-06-03 - Ontology MVP as snapshot/export layer

- Decision: Keep S1000D-RAG retrieval as Graph-first + Chroma vector hybrid, and add the ontology work as a deterministic lightweight snapshot/export layer rather than replacing runtime retrieval with ontology-only search.
- Rationale: S1000D maintenance support needs structured DMC/procedure/fault/figure/reference relationships, but vector retrieval remains useful for natural-language grounding and fallback. A dependency-light property graph/JSON-LD/Turtle-like export gives a practical path toward future Neo4j/RDF/OWL integration without adding closed-network runtime scope now.
- Consequences: The MVP exports first-class nodes/relations for DataModule, Component, Procedure, Action, Fault, Reference, Figure, GraphicAsset, Hotspot, Warning, and Caution. Full GraphDB/RDF/OWL server integration remains future work.
- Verification/source: Producer implemented `src/rag/ontology.py`, `scripts/build_ontology_exports.py`, `tests/test_s1000d_ontology.py`, and generated `ontology/s1000d_ontology_*` artifacts. Hermes reran focused and broader suites with `/home/hskim/miniforge3/bin/python`: `12 passed` for ontology/graph tests and `96 passed` for ontology + graph + RAG/model/query suites. Independent read-only Reviewer returned `PASS` with no blocking findings.

## 2026-06-04 - Pivot from S1000D expert manual chatbot to internal business-document chatbot

- Decision: Change the product target from a strict S1000D/MRO expert chatbot to a closed-network internal general-employee chatbot for past business-document search and company information Q&A.
- Rationale: The intended users are general employees working with historical proposals, RFPs, reports, meeting notes, project materials, and internal knowledge. For this use case, document discovery, source-grounded summarization, comparison, drafting assistance, permissions, and usability matter more than deterministic maintenance-procedure execution.
- Consequences: Future work should pivot away from S1000D-specific data, DMC/procedure ontology, and per-procedure guard expansion. The new direction needs a business-document corpus, metadata manifest, enterprise document loaders, hybrid retrieval, permission-aware filtering, and an enterprise AnswerPlan policy for document search, fact lookup, summarization, comparison, and drafting. The current v4 RDF/AnswerPlan/citation work remains a useful architectural reference but should be adapted to business-document knowledge graphs.
- Verification/source: User explicitly changed purpose in the 2026-06-04 Telegram session. Transition plan recorded in `internal-business-chatbot-transition-plan.md`. Latest pushed implementation before the pivot is `353b64f feat: add v4 RDF graph answer planning`, with full tests `300 passed, 5 warnings` and focused v4/app/UI tests `52 passed, 2 warnings`.

## 2026-06-05 - Close S1000D-RAG v4 as reference-complete

- Decision: Finish S1000D-RAG as a reference-complete RDF/AnswerPlan Graph RAG project and stop adding S1000D/MRO-specific product features.
- Rationale: The v4 core is implemented and verified: RDF/Turtle/JSON-LD export, RDFLib backend, SPARQL-compatible endpoint routing, shape validation, AnswerPlan citation/support policy, graph-path explainability, API/UI metadata exposure, and a final local fallback slice for unavailable SPARQL endpoints. Further GraphDB/OWL/SHACL/product hardening would not match the pivot to internal business-document search.
- Consequences: Treat this repo as an architecture seed and portfolio reference. New implementation should start in a separate business-document chatbot repo with document metadata, loaders, BM25/full-text, permission filters, enterprise graph schema, and AnswerPlan intents for document search, fact lookup, summarization, comparison, and drafting.
- Verification/source: Final local closure slice tests SPARQL endpoint failure fallback and records fallback in `ontology_trace.graph_paths`; focused fallback smoke succeeded with `S1000D_SPARQL_ENDPOINT=http://127.0.0.1:9/repositories/s1000d`.
