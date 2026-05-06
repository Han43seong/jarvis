# JARVIS Architecture

## High-level structure

```text
User
  |
  v
Hermes Agent in /home/hskim/jarvis
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
  +--> Codex/OMX executors in /home/hskim/projects/<repo>
         - codex exec
         - Codex /goal
         - omx exec
         - OMX $ralph
         - OMX $team
```

## Key decision

Keep Hermes as the central control plane and use Codex/OMX as execution runtimes for implementation-heavy work.

## Directory model

- `/home/hskim/jarvis`: control plane.
- `/home/hskim/projects`: active WSL-native repos.
- `/mnt/c/Users/hskim/...`: Windows-side files, registered only when needed.
