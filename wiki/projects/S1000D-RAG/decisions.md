# S1000D-RAG Decisions

## 2026-06-03 - Ontology MVP as snapshot/export layer

- Decision: Keep S1000D-RAG retrieval as Graph-first + Chroma vector hybrid, and add the ontology work as a deterministic lightweight snapshot/export layer rather than replacing runtime retrieval with ontology-only search.
- Rationale: S1000D maintenance support needs structured DMC/procedure/fault/figure/reference relationships, but vector retrieval remains useful for natural-language grounding and fallback. A dependency-light property graph/JSON-LD/Turtle-like export gives a practical path toward future Neo4j/RDF/OWL integration without adding closed-network runtime scope now.
- Consequences: The MVP exports first-class nodes/relations for DataModule, Component, Procedure, Action, Fault, Reference, Figure, GraphicAsset, Hotspot, Warning, and Caution. Full GraphDB/RDF/OWL server integration remains future work.
- Verification/source: Producer implemented `src/rag/ontology.py`, `scripts/build_ontology_exports.py`, `tests/test_s1000d_ontology.py`, and generated `ontology/s1000d_ontology_*` artifacts. Hermes reran focused and broader suites with `/home/hskim/miniforge3/bin/python`: `12 passed` for ontology/graph tests and `96 passed` for ontology + graph + RAG/model/query suites. Independent read-only Reviewer returned `PASS` with no blocking findings.
