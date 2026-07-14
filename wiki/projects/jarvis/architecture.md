# JARVIS Architecture

## High-level structure

```text
User
  |
  v
Hermes Agent in $HOME/jarvis
  |-- memory: compact durable user/environment facts
  |-- skills: reusable agent procedures
  |-- session_search: past work recall
  |-- wiki: human-readable project knowledge
  |-- harnesses: execution rules and safety gates
  |
  +--> Hermes direct tools
  |      - file edits
  |      - terminal validation
  |      - search/analysis
  |      - docs/wiki updates
  |
  +--> Codex/OMX executors in $HOME/projects/<repo>
         - codex exec
         - Codex /goal
         - omx exec
         - OMX $ralph
         - OMX $team
```

## Key decision

Keep Hermes as the central control plane and use Codex/OMX as execution runtimes for implementation-heavy work.

## Directory model

- `$HOME/jarvis`: control plane.
- `$HOME/projects`: active WSL-native repos.
- `/mnt/c/Users/<user>/...`: Windows-side files, registered only when needed.

## Project repository model

- JARVIS tracks projects by registry/wiki metadata, not by vendoring their source into `$HOME/jarvis`.
- Project source lives under `$HOME/projects/<project>`.
- Each project is managed as an independent git repository and can map to an independent GitHub repository.
- `$HOME/jarvis/projects/` is ignored if created locally as a root-level convenience folder or symlink.
