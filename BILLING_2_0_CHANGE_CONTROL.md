# Billing 2.0 — Change Control & Protocol

## 1. Change Control Workflow

All modifications to the Billing 2.0 codebase, documentation, schemas, or templates must follow this mandatory pipeline:

```text
1. USER REQUEST
       ↓
2. READ CONTROL DOCUMENTS (Requirements, Architecture, Data Contract, Document Rules, Agent Rules)
       ↓
3. INSPECT CURRENT IMPLEMENTATION (Examine existing code, tests, and storage)
       ↓
4. IDENTIFY IMPACT & DEPENDENCIES
       ↓
5. CHECK FOR CONFLICTS (Verify against locked requirements and anti-hallucination rules)
       ↓
6. PROPOSE MINIMAL CHANGE (Outline exact files, minimal diff, and test plan)
       ↓
7. USER AUTHORIZATION (Wait for user approval when altering scope, schema, or architecture)
       ↓
8. IMPLEMENT (Apply surgical changes adhering to Ponytail's minimal-code principle)
       ↓
9. AUTOMATED TESTING (Run pytest suite and frontend validation)
       ↓
10. MANUAL / VISUAL VERIFICATION (Inspect output, rendered PDFs, or UI state)
       ↓
11. UPDATE PROJECT STATE (Record verified progress in project control files)
       ↓
12. REPORT (Deliver transparent report with changed files, tests, and UNKNOWN items)
```

---

## 2. Change Categories & Authorization Boundaries

Every requested change must be classified into one or more of these 9 categories:

| Category | Description | Authorization Requirement |
|---|---|---|
| **A. Requirement Change** | Modifying or adding functional or business rules | Explicit user authorization required; update `BILLING_2_0_REQUIREMENTS.md` |
| **B. Architecture Change** | Modifying frameworks, services, storage, or APIs | Explicit user authorization required; update `BILLING_2_0_ARCHITECTURE.md` |
| **C. Data-Model Change** | Adding or altering MongoDB collections, fields, or schemas | Explicit user authorization required; update `BILLING_2_0_DATA_CONTRACT.md` |
| **D. Document-Format Change** | Modifying Word generator layout, XML, fonts, or tables | Explicit user authorization required; update `BILLING_2_0_DOCUMENT_RULES.md` |
| **E. UI Change** | Modifying frontend pages, modals, styles, or routing | Review against existing component design; no unauthorized new workflows |
| **F. Bug Fix** | Correcting broken or malfunctioning existing behavior | Allowed within requested scope; **does NOT authorize architecture changes** |
| **G. Refactor** | Restructuring existing code without changing behavior | Requires explicit user consent; **does NOT allow bundled feature additions** |
| **H. Cleanup** | Deleting dead code, temporary files, or stale artifacts | Allowed only when explicitly requested; must be executed one phase at a time |
| **I. Dependency Change** | Adding, upgrading, or removing packages in `requirements.txt` or `package.json` | Explicit user authorization required; must run `--help` and verify compatibility |

---

## 3. Strict Boundary Rules

1. **Bug Fix != Architectural License**: A request to fix a bug (e.g. temporary file cleanup) does **NOT** authorize rewriting database schemas, altering API contracts, or replacing libraries.
2. **Feature Request != Cleanup License**: A request to implement or verify a feature does **NOT** authorize cleaning up unrelated code or refactoring other services.
3. **No Bundling**: Refactoring, cleanup, and feature additions must remain strictly separated into distinct, reviewable steps.
4. **Anti-Hallucination Gate**: If a change requires business knowledge that is not documented or present in source scans, the agent must halt execution and mark the item:
   `STATUS: UNKNOWN — USER CONFIRMATION REQUIRED`.
