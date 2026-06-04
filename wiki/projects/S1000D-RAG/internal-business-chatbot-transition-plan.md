# S1000D-RAG → Internal Business Document Chatbot Transition Plan

## Context

- Date: 2026-06-04
- Current repository: `/home/hskim/projects/S1000D-RAG`
- Previous direction: S1000D/manual/MRO expert chatbot with ontology-guided RAG.
- New direction: closed-network internal general-employee chatbot for searching past business documents and company information.

The target user changed from expert maintainers who need strict procedure/manual correctness to general employees who need practical document discovery, summarization, comparison, and source-grounded company knowledge lookup.

## New product goal

Build an on-prem/closed-network business document assistant that can answer questions such as:

- “작년에 군 MRO 관련 제안서 찾아줘.”
- “OO기관 대상으로 했던 AI 사업자료 있어?”
- “2024년 국방 관련 RFP 중 음성인식 들어간 것 정리해줘.”
- “A사업 수행계획서 핵심 일정 알려줘.”
- “비슷한 제안서 참고해서 이번 제안 개요 초안 써줘.”
- “OO사업 담당자가 누구였지?”

The system should prioritize:

1. Finding the right historical documents.
2. Showing reliable sources/citations.
3. Summarizing and comparing multiple documents.
4. Understanding internal project/customer/technology terminology.
5. Enforcing document access permissions.
6. Clearly distinguishing document-grounded facts from generated analysis or draft text.

## Major architecture shift

### Previous S1000D/manual model

- Data model: DMC, SNS, data module type, procedure steps, applicability, components, warnings/cautions.
- Ontology role: validate target/action/procedure evidence and prevent unsupported maintenance steps.
- Answer policy: fail-closed for unsupported procedures, tools, values, and safety claims.

### New internal business-document model

- Data model: business documents, proposals, RFPs, reports, meetings, projects, customers, departments, people, technologies, dates, access groups.
- Ontology/graph role: connect projects, customers, documents, departments, technologies, and permissions.
- Answer policy: source-grounded enterprise search, summary, comparison, and drafting support.

The existing v4 AnswerPlan/citation/metadata concepts are still useful, but the schema must pivot from maintenance procedure support to enterprise document search policies.

## Data to replace or add tomorrow

Prepare a first PoC corpus of 15–20 internal-style business documents. Real internal documents are preferred if approved for the closed-network test environment; otherwise use sanitized representative samples.

Minimum recommended mix:

- Proposals: 5
- RFPs / 제안요청서: 3
- Reports / 착수·중간·완료보고서: 3
- Meeting minutes / 회의록: 3
- PPT solution/company/사업 소개자료: 2
- Excel budget/schedule/deliverable sheet: 1

Important Korean enterprise formats:

- HWP / HWPX
- PDF
- DOCX
- PPTX
- XLSX
- TXT / MD / CSV
- scanned PDF or image documents if OCR is in scope

## Required metadata schema for each document

At ingestion time, collect or infer metadata like this:

```json
{
  "doc_id": "proposal-2024-defense-mro-ai-001",
  "title": "군 MRO 음성 AI 정비지원 서비스 제안서",
  "doc_type": "proposal",
  "year": 2024,
  "created_at": "2024-00-00",
  "modified_at": "2024-00-00",
  "customer": "국방 관련 기관",
  "project_name": "군 MRO 음성 AI 정비지원",
  "department": "AI사업팀",
  "author": "unknown",
  "security_level": "internal",
  "access_group": "default-internal",
  "tags": ["군 MRO", "음성 AI", "폐쇄망", "RAG", "sLM"],
  "file_path": "data/raw/proposals/..."
}
```

Metadata quality is critical. Enterprise search will perform poorly if project names, customers, dates, document types, and access groups are missing.

## Proposed processed data layout

```text
data/
  raw/
    proposals/
    rfps/
    reports/
    meetings/
    contracts/
    technical/
  processed/
    documents.jsonl
    chunks.jsonl
    tables.jsonl
    entities.jsonl
    relationships.jsonl
  indexes/
    vector/
    bm25/
    metadata.sqlite
    graph/
  ontology/
    business-docs.ttl
    schema.ttl
```

## New ontology / knowledge graph concepts

Replace the S1000D-centric concepts with business-document concepts:

- Project
- Customer
- Document
- Department
- Person
- Technology
- Proposal
- RFP
- Contract
- Deliverable
- Meeting
- Requirement
- Budget
- Schedule
- SecurityLevel
- AccessGroup

Example relationships:

```text
Project hasCustomer Customer
Project hasDocument Document
Document hasType Proposal
Document authoredBy Person
Document belongsTo Department
Document mentionsTechnology Technology
Document respondsTo RFP
Project hasPeriod DateRange
Project hasBudget Budget
Document hasSecurityLevel SecurityLevel
User belongsTo Department
User canAccess AccessGroup
```

## Retrieval strategy

Do not rely on vector search alone. Internal document search needs exact keywords, acronyms, project numbers, customer names, dates, and metadata filters.

Use hybrid retrieval:

1. Vector search for semantic similarity.
2. BM25/full-text search for exact terms, names, acronyms, project IDs, and document titles.
3. Metadata filtering for document type, date, customer, department, security level, and author.
4. Graph/entity search for project-customer-document-technology relationships.
5. Permission filtering before answer generation.
6. Reranking after candidate retrieval.

## New answer policies

Use answer-type policies instead of per-question guards.

### fact_lookup

For questions about dates, amounts, people, customers, project names, or document-specific facts:

- Require citation.
- If no source supports the fact, say that the document evidence was not found.
- Do not invent numbers, dates, or names.

### document_search

For “찾아줘” questions:

- Return ranked document list.
- Include title, date/year, document type, customer/project, matching reason, and source path/link.

### summarization

For “요약해줘” questions:

- Summarize by source document first, then optionally provide an integrated summary.
- Include citations/source documents.

### comparison

For “비교해줘” questions:

- Separate document-grounded facts from interpretation.
- Show which documents support each comparison point.

### drafting

For “초안 써줘” questions:

- Separate retrieved facts from newly generated draft text.
- List source documents used as references.

### unknown / no-access

When no evidence is found or access is restricted:

- Distinguish “not found” from “not accessible”.
- Avoid revealing inaccessible document contents or even sensitive titles if policy requires hiding them.

## Tomorrow’s recommended work order

1. Decide whether to keep this repository name or create a new repo/project.
   - Recommendation: keep S1000D-RAG as a reference if possible and create/branch a new internal-business-doc RAG project.
   - If continuing in the same repo, expect significant renaming/refactoring.
2. Prepare the first internal document sample set.
3. Create a `documents.jsonl` metadata manifest for every file.
4. Implement or adapt general document loaders:
   - PDF
   - HWP/HWPX
   - DOCX
   - PPTX
   - XLSX
   - TXT/MD/CSV
5. Build processed `documents.jsonl` and `chunks.jsonl`.
6. Add BM25/full-text index in addition to the existing vector index.
7. Add metadata SQLite or equivalent filter store.
8. Define business-document ontology/graph schema.
9. Redesign AnswerPlan around enterprise intents:
   - document_search
   - fact_lookup
   - summarization
   - comparison
   - drafting
10. Update UI to show:
   - source document cards
   - document type/date/customer/project
   - citation snippets
   - access/visibility indicators

## Acceptance criteria for the next PoC

A useful first PoC should pass these checks:

- Ingests at least 15 representative business documents.
- Finds documents by exact project/customer/keyword search.
- Finds semantically related documents by natural Korean question.
- Filters by year and document type.
- Provides source-grounded summaries with document titles and snippets.
- Refuses or qualifies unsupported factual claims.
- Does not expose documents outside the current user/access group policy.

## Open decisions

- Keep current `S1000D-RAG` repo and refactor, or create a new repo for internal business-document RAG?
- Which document formats are mandatory for the first closed-network demo: HWP/HWPX, PDF, DOCX, PPTX, XLSX?
- What access-control model should be simulated first: simple `access_group`, department-based, or per-file ACL?
- Should sample data be real internal data, sanitized internal data, or synthetic representative data?
- Should the first UI prioritize chat answers, document search result cards, or both?
