---
title: Project Repository Model
created: 2026-05-07
updated: 2026-05-07
type: concept
concept_type: repository-model
status: active
tags: [jarvis, repository-model, project-registry, github, safety]
sources: [README.md, config/projects.yaml, wiki/projects/jarvis/decisions.md]
confidence: high
relations:
  - type: configured_by
    target: projects-yaml
  - type: documented_in
    target: projects/jarvis/architecture
  - type: governed_by
    target: jarvis-control-plane
---

# Project Repository Model

Application source repositories live outside the JARVIS control-plane repo under `/home/hskim/projects/<project>`. Each project can have its own git and GitHub repository.

## Rationale

This keeps JARVIS history, registry, wiki, and harnesses separate from application code history. It also lets [[entities/codex-cli|Codex CLI]] and [[entities/omx|OMX]] run inside the target project repo with bounded scope.

## JARVIS Tracking

JARVIS tracks projects in `config/projects.yaml` and project notes under `wiki/projects/<project>/`.

## See also

- [[concepts/jarvis-control-plane|JARVIS Control Plane]]
- [[concepts/executor-routing|Executor Routing]]
- [[projects/jarvis/decisions|JARVIS Decisions]]
