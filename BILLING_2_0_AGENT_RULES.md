# BILLING 2.0 — AI CODING AGENT OPERATING RULES

## Master Agent Instruction

> **MANDATORY DIRECTIVE FOR ALL AI AGENTS**:
>
> These documents are persistent project constraints.
>
> Every future AI coding task must begin by reading the relevant control documents and current project state.
>
> The agent must operate as an implementer of the user's requirements, not as an independent product designer.
>
> When the user has not specified something, the agent must not invent it.
>
> When existing code already satisfies a requirement, the agent must reuse it rather than create a parallel implementation.
>
> When a requirement is ambiguous or conflicting, the agent must stop and request clarification.
>
> The agent must never treat its own assumptions, suggestions, inferred improvements, or generated plans as user-approved requirements.

---

## 1. Hierarchy of Authority

When executing any task, the agent must adhere to this strict hierarchy:

```text
LEVEL 1  — Explicit User Instructions
LEVEL 2  — BILLING_2_0_REQUIREMENTS.md (Locked functional & non-functional requirements)
LEVEL 3  — BILLING_2_0_ARCHITECTURE.md (Verified architecture & technology decisions)
LEVEL 4  — BILLING_2_0_DATA_CONTRACT.md (Verified data relationships & source of truth)
LEVEL 5  — BILLING_2_0_DOCUMENT_RULES.md (Verified document generation & visual fidelity rules)
LEVEL 6  — BILLING_2_0_PROJECT_STATE.md (Actual implementation & verification status)
LEVEL 7  — BILLING_2_0_ROADMAP.md (Planned project progression)
LEVEL 8  — BILLING_2_0_AGENT_RULES.md (Operational rules for agent behavior)
LEVEL 9  — BILLING_2_0_CHANGE_CONTROL.md (Process for proposing and approving changes)
LEVEL 10 — BILLING_2_0_VERIFICATION.md (Testing & verification protocol)
```

> **Ponytail Principle**: Ponytail enforces simplicity and prevents over-engineering, but Ponytail **MUST NOT** override user requirements, locked architecture, document rules, data contracts, security requirements, or explicit user decisions. Simplicity is applied only *after* requirements are satisfied.

---

## 2. The 14 Mandatory Agent Rules

### RULE 1 — READ CONTROL FILES FIRST
Before EVERY implementation, modification, refactor, cleanup, test change, schema change, or architectural change:
Read the relevant control files:
1. `BILLING_2_0_AGENT_RULES.md`
2. `BILLING_2_0_REQUIREMENTS.md`
3. `BILLING_2_0_ARCHITECTURE.md`
4. `BILLING_2_0_DATA_CONTRACT.md`
5. `BILLING_2_0_DOCUMENT_RULES.md`
6. `BILLING_2_0_CHANGE_CONTROL.md`
7. `BILLING_2_0_PROJECT_STATE.md`
8. `BILLING_2_0_ROADMAP.md`
Then inspect the relevant existing code. Do not rely only on the user's latest prompt.

### RULE 2 — DO NOT HALLUCINATE
Never invent:
- Requirements
- Billing rules
- Company rules
- Fields or schema attributes
- Database relationships
- API endpoints or parameters
- UI layouts or workflows
- Document sections or taxes
- Addresses or GSTINs
- Customer information
- Authentication behavior
- Business logic

If information is missing, mark it `STATUS: UNKNOWN — USER CONFIRMATION REQUIRED`. Then stop and ask the user.

### RULE 3 — DO NOT OVERRIDE USER REQUIREMENTS
If a new user prompt appears to conflict with locked requirements or existing project architecture:
**STOP**. Report the conflict explicitly. Do not silently choose your own interpretation or bypass locked rules.

### RULE 4 — DO NOT START FUTURE STEPS
Never implement a future roadmap step unless the user explicitly authorizes it.
Do not infer "the next logical step" and implement it automatically. When Step 7 is active, Step 8 must remain `NOT STARTED`.

### RULE 5 — MINIMAL CHANGE
Before creating code:
1. Search for existing functionality.
2. Reuse existing implementations and abstractions whenever possible.
3. Do not create duplicate utilities, services, or components.
4. Channel Ponytail's minimal-code principle.
5. **Never** sacrifice a locked requirement or document fidelity rule merely to reduce line count.

### RULE 6 — NO UNAUTHORIZED REFACTORING
If the requested task is X: **Do X only**.
Do not refactor Y and Z because they "could be improved" or "look messy." Separate refactoring or cleanup requires explicit user authorization.

### RULE 7 — PRESERVE WORKING FUNCTIONALITY
Before modifying existing code:
1. Identify what currently works and what tests cover it.
2. After modification, execute test suites and verify that existing behavior remains intact.

### RULE 8 — DOCUMENTS ARE DATA
Never overwrite, edit, rename, move, delete, or restructure reference documents in `Sample Bills/` to make tests pass or simplify generation. `Sample Bills/` is an immutable reference dataset.

### RULE 9 — RESPECT THE FOUR SOURCE-OF-TRUTH PILLARS
- **Database (MongoDB)** is the authoritative structured source of truth for application state.
- **Original Scans** are immutable primary source evidence.
- **Master Word Document (`.docx`)** is the authoritative human-readable document archive.
- **PDF Document** is an on-the-fly viewing and rendering representation.
Never treat generated Word/PDF files as the primary structured database, and never treat PDFs as the editable master.

### RULE 10 — NO SILENT DATA CORRECTION
If OCR produces value X and validation expects value Y:
**DO NOT** silently replace X with Y. Flag the discrepancy (`needs_review = true`, `review_reason = "..."`) for human manual review.

### RULE 11 — VERIFICATION DISCIPLINE
"Implemented" does **NOT** mean "verified."
Only mark functionality `VERIFIED` after actual test execution and explicit human verification. Automated tests alone are insufficient to mark a roadmap step complete.

### RULE 12 — REPORT CHANGES TRANSPARENTLY
Every task report must include:
- Files inspected
- Files changed
- Rationale for each change
- Tests executed and outcomes
- Manual verification performed
- Remaining open issues
- Assumptions made
- UNKNOWN items requiring user confirmation

### RULE 13 — MANDATORY STOP CONDITIONS
The agent must immediately stop and prompt the user when:
- Requirements conflict with locked rules
- Architectural direction is ambiguous
- Necessary source data is missing
- A reference document contradicts an existing locked rule
- Implementation would require inventing business logic or tariffs
- A requested change risks breaking verified functionality
- Scope cannot be determined safely

### RULE 14 — USER APPROVAL IS REQUIRED
- An observation is not an implementation authorization.
- A possible improvement is not a user requirement.
- A `TODO` in code is not authorization to build a feature.
All scope changes require explicit user consent.
