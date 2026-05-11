# JARVIS Status

## Current state

- WSL environment cleaned and ready.
- Codex CLI and OMX installed and smoke-tested.
- Codex OAuth/ChatGPT Pro Personal workspace verified previously.
- Bubblewrap installed and Codex sandbox warning removed.
- Hermes approval policy set to smart.
- Secret redaction enabled for future sessions.
- JARVIS control-plane root created at `/home/hskim/jarvis`.
- Project root created at `/home/hskim/projects`.

## Active operating model

- Hermes is the control-plane/orchestrator/verifier/memory manager.
- OMX `$ralph` is the default medium/large implementation executor.
- Codex `/goal` is available for repo-local iterative cleanup when useful.
- Harness documents define automatic routing and completion rules.

## Recent changes

- 2026-05-06: Created user-local JARVIS Hermes skills:
  - `jarvis-core`
  - `jarvis-executor-router`
  - `jarvis-codex-omx-executor`
  - `jarvis-wiki-manager`
- 2026-05-07: Initialized ontology-informed LLM Wiki structure under `wiki/` with `SCHEMA.md`, `index.md`, `log.md`, entity/concept/comparison pages, and skill catalog/lifecycle pages.
- 2026-05-11: Reviewed current JARVIS progress with the user and confirmed the control-plane repo had been pushed to GitHub with local `main` synchronized to `origin/main`.
- 2026-05-11: Clarified the ontology-informed wiki model: pages act as graph nodes, YAML frontmatter acts as node metadata/properties, typed `relations` act as graph edges, and `SCHEMA.md` defines the allowed vocabulary.
- 2026-05-11: Recorded the rationale for using markdown-native lightweight ontology now instead of full RDF/OWL: lower operational overhead, better human/agent editability, git-friendly diffs, flexible schema evolution, and possible future RDF/JSON-LD export.
- 2026-05-11: Added `hermes-background` to the routing pipeline for long research/analysis/review work, documented that synchronous `delegate_task` must not be treated as durable background execution, and added an acceptance test matrix plus `scripts/check_executor_routing_policy.py`.

## Next steps

1. Register the first real project in `config/projects.yaml`.
2. Promote or refine JARVIS skills after a few real routing/executor runs.
3. Consider a future RDF/JSON-LD export path only after the markdown ontology schema stabilizes and graph queries become necessary.
