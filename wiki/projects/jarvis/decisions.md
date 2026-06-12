# JARVIS Decisions

## 2026-06-12 — Adversarial design review applied: redefine P1/P2, correct P4, grade enforcement

Decision:
- Apply the 7 MAJOR revision proposals from the 2026-06-12 adversarial design review (verdict: revise / conditionally keep direction; BLOCK 0 · MAJOR 7 · MINOR 6 · NOTE 4) to the vNext concept docs.
- Redefine the differentiation claim (P2): not the intent-to-contract compiler alone — intent→spec compilation is already commoditized (AWS Kiro, GitHub Spec Kit, backend plan modes) — but the closed loop: compile → delegate → contract-derived, interest-separated final judgment.
- Redefine verification residency (P1): what stays with JARVIS is not "verification" in general but the final judgment that is contract-derived and interest-separated. Backend self cross-review (including Claude Code dynamic workflows adversarial review, official GA) is evidence, not judgment.
- Correct the 2026-06-10 statement that competing control planes provide no contract+verification layer: competitors already ship verification gates that delegate to external CI/review (Optio: CI polling + review agent + auto-merge, multi-vendor A/B). The actually-empty layer is contract-derived judgment, and the contract-compilation layer itself.
- Introduce per-field guardrail enforcement levels (native | wrapper | post_hoc); any field below native auto-escalates to completion_gates post-hoc checks. Confirmed: completion gates are not natively enforceable on any backend, and Codex cannot deny per-file writes inside the workspace.
- Split final judgment into two stages: deterministic mechanical gate (necessary condition) → model-based Director judgment.
- Grade contract fields must/should/optional with backend-strength thickness profiles, and add a contract quality feedback loop (run ledger links contracts to outcomes with defect classification) to the MVP priorities.

Rationale:
- Adversarial review against 24 external sources (all verified 2026-06-12; 3 top claims checked directly against original sources) found the target layer genuinely empty across 6 competitor control planes, but the existing wording indefensible as written against current backend-native capabilities.

Reference:
- wiki/projects/jarvis/reviews/vnext-adversarial-review-2026-06-12.md
- wiki/concepts/jarvis-vnext-intent-to-contract-director.md

## 2026-05-06 — Hermes-first hybrid architecture

Decision:
- Use Hermes Agent as the JARVIS control plane.
- Use Codex CLI + OMX as implementation executors.
- Keep Hermes available for direct small coding, docs, validation, wiki updates, and orchestration.

Rationale:
- User wants to use Codex subscription/OAuth path for coding workflows.
- Hermes provides memory, skills, session search, cron, tool orchestration, and gateway features.
- OMX provides stronger coding execution loops for medium/large implementation.

## 2026-05-06 — Workspace layout

Decision:
- JARVIS root: `/home/hskim/jarvis`
- Active WSL project root: `/home/hskim/projects`
- Application project source stays outside the JARVIS control-plane repo.
- Each project is managed as an independent git repository and can map to its own GitHub repository.
- If `/home/hskim/jarvis/projects/` is created locally as a root-level folder or symlink, it is ignored by `.gitignore`.

Rationale:
- Keeps the control plane separate from application repositories.
- Allows Hermes to manage many projects from one place.
- Allows Codex/OMX to run inside specific target repos with `-C <repo>`.
- Keeps project history, remotes, CI, and executor work isolated per project.

## 2026-05-06 — Permission policy

Decision:
- `approvals.mode: smart`
- `approvals.cron_mode: deny`
- `security.tirith_enabled: true`
- `security.redact_secrets: true`

Rationale:
- Allows low-risk automation while keeping high-risk actions gated.

## 2026-05-28 — JARVIS judgment-first office runtime direction

Decision:
- Future JARVIS hardening should keep JARVIS as the intelligent Director for user-intent interpretation, work design, executor selection, quality judgment, and escalation decisions.
- CLI/runtime helpers should automate run ledgers, approval queues, status views, prompt/log storage, verification capture, and Producer/Reviewer loop mechanics.
- Routing rules should be treated as guardrails and decision support, not as a rigid replacement for JARVIS judgment.

Rationale:
- A rules-only dispatcher could lower work-design quality by missing user intent, business/taste tradeoffs, context, scope nuance, and quality expectations.
- JARVIS should reduce repetitive administrative work without reducing Director-level reasoning.
- Durable ledgers and approval queues are prerequisites for safer Telegram/CLI continuity, long-running work, and future multi-agent office-style orchestration.

Reference:
- `wiki/concepts/jarvis-office-runtime-direction.md`

## 2026-06-08 — Ouroboros as JARVIS vNext reference, not replacement

Decision:
- Use `Q00/ouroboros` as a useful reference and partial-absorption source for JARVIS vNext design.
- Do not replace JARVIS with Ouroboros, and do not install/register Ouroboros into the default Hermes profile without explicit approval and sandbox evidence.
- Absorb patterns selectively into JARVIS-native design: Seed-like task contracts, run-ledger event logs, ambiguity/interview gates, evaluation ladders, executor adapter contracts, and harness manifests.
- Existing JARVIS harnesses remain assets to register, wrap, refactor, compare, or archive; they are not discarded because of ontology/runtime redesign.

Rationale:
- Ouroboros overlaps strongly with JARVIS vNext goals, but it is itself an Agent OS and could blur the user's desired JARVIS Director boundary if adopted wholesale.
- JARVIS needs a broader project-operations control plane across wiki, registry, Telegram/CLI continuity, approvals, multiple executors, and project-specific harnesses.
- A sandbox/shadow-mode path preserves safety while still extracting valuable architecture patterns.

Reference:
- `wiki/concepts/ouroboros-adoption-review.md`
- `wiki/concepts/jarvis-vnext-executor-ontology.md`
- `wiki/concepts/jarvis-office-runtime-direction.md`

## 2026-06-08 — Open-source target should be Hermes-agnostic core plus adapters

Decision:
- The JARVIS system has open-source potential as an Agent Operations Control Plane, but the private `/home/hskim/jarvis` instance should not be published as-is.
- Public extraction should separate a runtime-agnostic core from host/runtime adapters.
- The private JARVIS instance may remain Hermes-first because Hermes is operationally useful for memory, skills, session search, tools, cron, gateway, and wiki orchestration.
- The public core must not require Hermes; Hermes should be a first-class adapter and recommended host, not a hard dependency.
- Avoid using `JARVIS` as the public project name until naming/trademark risk is resolved.

Rationale:
- Open-source users may use Claude Code, Codex, OpenCode, shell runners, local LLMs, or other hosts; a Hermes-only core would unnecessarily narrow adoption.
- The valuable generalizable piece is the operating contract: task contracts, routing ontology, run ledgers, approval queues, executor/harness adapters, verification gates, and status/resume.
- Keeping the private JARVIS repo separate prevents leaking personal paths, project registry entries, internal wiki/status notes, session-derived context, and approval/security assumptions.

Reference:
- `wiki/concepts/jarvis-open-source-strategy.md`
- `wiki/concepts/jarvis-office-runtime-direction.md`
- `wiki/concepts/jarvis-vnext-executor-ontology.md`

## 2026-05-12 — Claude Code and OMC as secondary external executors

Decision:
- Keep Hermes' main model/provider on the current Codex/OpenAI-Codex path.
- Keep Codex CLI + OMX as the primary implementation executor line.
- Add Claude Code + OMC as a secondary external CLI executor line.
- Use Claude Code's Claude Max OAuth login for the external `claude` CLI rather than treating it as a Hermes main-provider switch.

Rationale:
- Codex/OMX is already validated for the user's default coding workflow.
- Claude Code/OMC provides a useful second executor for review, planning, refactoring, Claude-specific reasoning strengths, and quota/load balancing.
- Separating Hermes provider auth from external CLI executor auth avoids conflating Claude Code subscription OAuth with direct Anthropic API-key usage.

Verification:
- `claude auth status --text` showed Claude Max account login.
- `claude -p 'Reply with exactly CLAUDE-CODE-OK' --max-turns 1 --output-format json` returned `CLAUDE-CODE-OK`.
- `omc --version` returned `4.13.7` after installing `oh-my-claude-sisyphus`.
- `omc setup` completed agent/skill/hook sync under `~/.claude`.

## 2026-06-11 — JARVIS vNext should optimize intent-to-contract over orchestration

Decision:
- Treat the default vNext workflow as `Understand -> Contract -> Delegate -> Verify -> Report`.
- Narrow JARVIS's core role to requirement normalization, backend-native task-contract generation, policy/approval gating, evidence-backed verification, and result arbitration.
- Assume modern backends such as Claude Code/Fable, Codex, Cursor Cloud Agents, Devin, OpenHands, OMX, and Gajae-Code may act as both Runtime and Producer in a single selected backend.
- Do not make separate orchestration layers the default path. Use them only when multi-backend arbitration, long-running programs, queues, cron/kanban, cross-repo coordination, high risk, or audit needs justify the overhead.
- Expose backend-native systems through adapters that standardize capability, contract preparation, launch, status, result collection, and cancellation while preserving backend-specific strengths.

Rationale:
- Backend-native systems increasingly include planning, subagents, background/cloud execution, worktree isolation, test/fix loops, PR workflows, hooks, skills, and MCP-style extension surfaces.
- As backend execution improves, the bottleneck shifts from running agents to giving them high-quality requirements and judging whether the result is trustworthy.
- JARVIS's defensible value is converting vague user intent and accumulated project knowledge into executable contracts, then verifying explicit QA plus implicit user/project constraints.

Consequences:
- MVP schemas should prioritize `task-contract.yaml`, backend capability metadata, backend result records, workflow-level routing, and verification reports.
- JARVIS thin runtime should remain a ledger/adapter/evidence layer rather than a full custom orchestrator.
- Multi-agent or multi-backend flows should be escalation levels, not the default.

Reference:
- `wiki/concepts/jarvis-vnext-intent-to-contract-director.md`

## 2026-06-10 — JARVIS vNext should be a Director over runtimes and producers

Decision:
- Narrow JARVIS vNext away from being another generic coding agent runner or multi-agent orchestrator.
- Position JARVIS vNext as a project-operations Director/meta-control-plane above existing coding agents and orchestration/runtime systems.
- Replace the ambiguous shorthand `orchestrator/executor` with role-based terms: `Director`, `Runtime`, `Producer`, and `Verifier`.
- Treat tools such as Codex, OMX/Gajae-Code, Claude Code, AgentWrapper, CodeMachine, Golutra, Agor, Optio, cron, and kanban as possible role-bearing backends rather than fixed categories. A tool can be a Runtime in one Run and a Producer in another.
- JARVIS should own task interpretation, backend selection rationale, approval/risk gates, task contracts, evidence-backed completion judgment, long-term project memory, and next-action decisions.
- Runtimes should own low-level execution mechanics such as process spawning, worktree isolation, parallel agents, CI/PR automation, workflow execution, dashboard/log streaming, and session management.

Rationale:
- Modern coding agents with goal modes can already complete many single-repo tasks when given a strong design document.
- GitHub already has many overlapping projects in the agent-orchestrator/control-plane space, including AgentWrapper, Golutra, CodeMachine, Agor, Optio, Overstory, Codex Mate, aiagentflow, and c9r orchestrator.
- Therefore “multi-agent orchestration” by itself is not a durable differentiator.
- JARVIS's stronger differentiator is the long-term conversational Director layer: route, gate, contract, verify, remember, and escalate across projects and tools.

Consequences:
- MVP priority should shift toward run ledger, route-decision records, approval/verification gate models, task-contract generation, and project operations memory queries.
- Custom multi-agent spawning, workflow engines, dashboards, PR/CI auto-fix, and own coding-agent development should be lower priority unless needed as adapters.
- Initial external-orchestrator integration can be manual/prompt or CLI-based before deeper API/daemon integration.

Reference:
- `wiki/concepts/jarvis-vnext-meta-control-plane.md`


## 2026-06-11 — vNext must separate Markdown instructions from executable guardrails

Decision:
- Treat Markdown instruction files (`AGENTS.md`, `CLAUDE.md`, skills, wiki, runbooks) as guidance, not as deterministic enforcement.
- Add an explicit Contract Enforcement Layer to the vNext design: task contracts should include allowed paths, denied paths, denied commands, approval gates, required evidence, budget limits, and completion gates.
- Model backend-native deep workflow modes, including Claude Code `ultracode` / Dynamic workflows, as control-flow orchestration capabilities rather than as policy enforcement by themselves.
- Require adapters to map JARVIS guardrails to the strongest available backend mechanisms: permissions, hooks, sandboxing, managed settings, command/path policy, wrapper checks, isolated worktrees, post-run diff checks, and JARVIS completion refusal when evidence is missing.

Rationale:
- Markdown can be skipped, summarized away, or inconsistently followed by LLM backends.
- Dynamic workflows improve execution structure by scripting phases, loops, subagent fanout, result aggregation, and verifier passes, but they do not guarantee that prose instructions are semantically obeyed.
- Deterministic safety requires executable guardrails and evidence gates: “do not edit secrets” must become path/tool denial, and “run verification before completion” must become a completion gate backed by logs or an explicit failed/blocked status.

Consequences:
- The vNext MVP should include an executable guardrail schema before investing in a full custom workflow engine.
- Backend capability records should distinguish `native_features.deep_workflow` from `enforcement_features.permissions/hooks/sandbox/managed_settings`.
- JARVIS remains the final judge: a backend workflow can complete, but JARVIS should report success only after scope, secret, diff, and verification evidence pass.

Reference:
- `wiki/concepts/jarvis-vnext-intent-to-contract-director.md`
- `wiki/concepts/jarvis-vnext-meta-control-plane.md`
- Claude Code Dynamic workflows: `https://docs.anthropic.com/en/docs/claude-code/workflows`
- Claude Code permissions/hooks/sandboxing docs: `https://docs.anthropic.com/en/docs/claude-code/settings`


## 2026-06-11 — JARVIS sits above harness and loop engineering

Decision:
- Define harness engineering as the design of task wrappers that help AI work reliably: instructions, context, tools, environment, permissions, sandbox, output schema, validation, logging, and evidence capture.
- Define loop engineering as closed-cycle AI automation: observe, judge, act, verify, repair, and repeat until success, failure, or escalation.
- Treat loops as execution patterns available to JARVIS, not as the top-level JARVIS identity.
- Position JARVIS as the Director/Governor above loops: it chooses whether a loop is needed, selects or designs the loop, binds harnesses into loop steps, applies guardrails, controls budget/risk, verifies evidence, and makes the final stop/pass/escalate judgment.

Rationale:
- Harnesses make individual AI work units more reliable; loops create autonomous progress across repeated work units.
- A loop can contain multiple harnesses, such as diagnosis, implementation, test, review, and report harnesses inside a test-fix loop.
- JARVIS's differentiator is not merely running loops, but deciding which loop and harness combination is appropriate for a user's intent, project context, backend capability, and risk profile.

Consequences:
- vNext schemas should include reusable harness manifests and loop contracts in addition to task contracts and guardrails.
- Run ledgers should record the selected loop type, harnesses used, iteration count, stop condition, evidence, and JARVIS final judgment.
- The product language should describe JARVIS as an Agent Operations Director/Governor that uses harness and loop engineering, not as a generic loop runner.

Reference:
- `wiki/concepts/jarvis-vnext-intent-to-contract-director.md`
- `wiki/concepts/jarvis-vnext-meta-control-plane.md`


## 2026-06-11 — vNext plans should be agent implementation briefs, not line-by-line manuals

Decision:
- Keep the vNext planning documents at the level of architecture constraints, implementation contracts, invariants, non-goals, and first artifacts.
- Do not expand them into a detailed human step-by-step build manual unless a future task specifically needs that.
- Make the documents usable in a fresh environment by an implementation agent: it should be able to infer repo/module layout and implementation details while preserving JARVIS Director/Governor semantics, task contracts, harnesses, loops, guardrails, evidence gates, and backend adapters.

Rationale:
- The intended implementation path will use capable coding agents, so over-specifying every build step may reduce backend-native planning, subagent, workflow, and repair-loop strengths.
- What must be preserved is the operating contract: JARVIS turns vague intent into bounded contracts, applies executable guardrails, delegates to backend-native systems, collects evidence, and makes the final judgment.
- A greenfield agent needs clear invariants and acceptance criteria more than a hand-coded installation recipe.

Consequences:
- Add an Agent implementation brief to the intent-to-contract concept page.
- Treat future implementation prompts as task contracts derived from the concept pages.
- Keep current-environment details such as Hermes, OMX, Gajae, Codex, and Claude Code as adapter examples rather than mandatory dependencies for a portable core.

Reference:
- `wiki/concepts/jarvis-vnext-intent-to-contract-director.md`
- `wiki/concepts/jarvis-vnext-meta-control-plane.md`
