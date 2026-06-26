# just-chill Ontology Contract Harness

Use this harness for the contract-level RDF/OWL TBox/ABox, deterministic Turtle export, SHACL shape export, SHACL-style validation, RDF/SHACL live-boundary planning, and host-owned RDF persistence receipt slice of just-chill memory. The slice creates ontology candidate records, serialization manifests, shapes, validation reports, live-boundary reports, host-owned persistence plans, and receipt evidence; just-chill still does not persist RDF, write Hermes memory, run a live SHACL engine, or promote canonical assertions itself.

## Purpose

```text
raw artifact contract
  -> optional summary memory contract
  -> scripts/just_chill_ontology_contracts.py
  -> TBox + ABox promotion candidate + RDF/OWL Turtle export + SHACL shapes/report
  -> future Hermes/RDF persistence only after live binding and approval gates
```

## Implemented files

| File | Role |
|---|---|
| `scripts/just_chill_ontology_contracts.py` | Builds deterministic TBox classes/properties, ABox promotion candidates, provenance links, promotion policy, RDF/OWL Turtle export contracts, SHACL shape exports, validation reports, RDF/SHACL live-boundary reports, and host-owned persistence plans from raw artifact / summary memory contracts. |
| `scripts/check_just_chill_ontology_contracts.py` | Checks explicit-confirmation blockers, PreferenceAssertion auto-promotion criteria, provenance validation, sensitive/deleted/redacted source blocking, deterministic RDF export, SHACL export, live-binding guards, RDF/SHACL persistence planning, and valid candidate JSON output. |
| `scripts/just_chill_rdf_persistence_receipts.py` | Runs the host-owned RDF persistence receipt bridge: builds deterministic exports, runs live `pyshacl` as host evidence, calls Hermes RDF graph MCP create/read/delete through stdio JSON-RPC, and records read-back/delete receipts while preserving just-chill execution boundaries. |
| `scripts/check_just_chill_rdf_persistence_receipts.py` | Checks live SHACL evidence, ready persistence plans, RDF graph read-back hash matching, delete receipts, and fail-closed just-chill boundary validation. |

## Ontology contract rules

- Hermes remains the storage authority; just-chill remains the contract/promotion-policy authority.
- `liveBinding.status` remains `contract-only` in just-chill ontology records; host-owned receipt runners may provide external persistence evidence without changing just-chill's storage authority.
- TBox output names the canonical classes/properties used by this slice; it is a deterministic contract, not a persisted ontology store.
- RDF/OWL export is serialization-only: `storageAuthority` stays `Hermes`, `contractAuthority` stays `just-chill`, `liveBinding.status` stays `contract-only`, and `storageWriteAllowedHere` stays `false`.
- SHACL shape export is a deterministic contract report; live `pyshacl` evidence is recorded separately by the host-owned persistence receipt runner.
- RDF/SHACL live-boundary planning is read-only: it may detect host RDF parsers, host SHACL engines, and Hermes RDF graph APIs, but it must not run the live engine or write Hermes itself.
- RDF/SHACL persistence plans are host-owned and require all of: RDF parser availability, live SHACL engine availability, Hermes graph create/read/delete API mapping, conforming SHACL report, sensitive approval when applicable, and Hermes read-back hash evidence.
- A `shaclResult.conforms: true` value passed to the Hermes RDF graph MCP tool is host-asserted evidence from the operator-owned SHACL step; the MCP server enforces presence/shape/approval gates but does not independently run SHACL.
- ABox output is a `PromotionCandidate`, not canonical personal memory.
- `DecisionAssertion` and `PolicyAssertion` require explicit confirmation before canonical promotion.
- `PreferenceAssertion` auto-promotion requires repeated independent sources, non-sensitive content, non-destructive semantics, access allowed, retention valid, conflict-free state, high confidence, and a ready Hermes boundary.
- Missing provenance, sensitive unapproved sources, deleted/redacted sources, and unmapped Hermes write boundaries block promotion.
- Operational/audit facts remain traceability evidence and must not become canonical personal memory without promotion.

## Verification

Run:

```sh
python3 scripts/check_just_chill_router.py
python3 scripts/check_just_chill_bridge_contracts.py
python3 scripts/check_just_chill_live_bindings.py
python3 scripts/check_just_chill_visible_helpers.py
python3 scripts/check_just_chill_hermes_boundary.py
python3 scripts/check_just_chill_ontology_contracts.py
python3 scripts/check_just_chill_rdf_persistence_receipts.py
python3 scripts/check_executor_routing_policy.py
python3 scripts/just_chill_ontology_contracts.py --export-rdf --export-shacl --live-boundary --plan-persistence --pretty --summary "User prefers visible routed GJC sessions for development routing." --assertion-kind PreferenceAssertion "remember that GJC should use visible routed sessions by default"
python3 scripts/just_chill_rdf_persistence_receipts.py --pretty "remember that GJC should use visible routed sessions by default"
```

Expected high-level results:

- Focused checks pass, including `PASS: 25 just-chill ontology contract cases passed` and `PASS: 4 just-chill RDF persistence receipt cases passed`.
- Real-host ontology contracts remain promotion-blocked until source raw artifacts have live Hermes receipts and assertion promotion gates pass; eligible host-owned receipt fixtures can now produce live SHACL evidence and RDF graph read-back/delete receipts.
- Fake write-ready fixtures allow PreferenceAssertion eligibility only when every auto-promotion criterion is satisfied.
- DecisionAssertion and PolicyAssertion remain blocked without explicit confirmation.
- RDF/OWL export emits stable Turtle text, a source contract hash, source artifact triples, promotion-policy triples, and no live persistence receipt.
- SHACL export emits deterministic shape Turtle and a validation report whose conformance follows the candidate blockers.
- RDF/SHACL live-boundary reports show local RDF parsing support, mapped Hermes RDF graph lifecycle tools, and mapped live `pyshacl` support when installed.
- RDF/SHACL persistence plans keep `allowedHere: false`, `justChillCallsHermes: false`, and `justChillRunsShaclEngine: false`; host-owned receipt runs supply live SHACL and Hermes evidence without making just-chill the executor.

## Remaining work

- Decide which staged raw artifacts or approved ontology candidates should be replayed through the host-owned Hermes/RDF receipt runners.
- Replace the deterministic SHACL-style contract validator as the primary conformance source only after production policy accepts live SHACL receipts as canonical evidence.
- Add vector sidecar and recall-gate contracts that resolve through Hermes references and obey access/deletion/redaction policy.
