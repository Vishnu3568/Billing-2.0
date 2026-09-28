# Billing 2.0 — Project Roadmap & Control Contract

## 1. Project Purpose

Billing 2.0 is an automated billing and document management platform designed to streamline:

- Duty slip ingestion (front and back physical scans as one unified record)
- Automated data extraction using OCR and Vision AI
- Human review, verification, and editing with complete audit trail
- Faithful reproduction of company-specific Word billing documents (`.docx`)
- Company-isolated master document management where all bills for a company reside in that company's single master document
- Company Workspace for centralized visibility and auditability of bills, duty slips, and files.

---

## Control Documentation Hierarchy

This document represents **LEVEL 7 (Planned Milestone Progression)** in the Billing 2.0 Agent Control System:

1. **LEVEL 1**: Explicit User Instructions
2. **LEVEL 2**: `BILLING_2_0_REQUIREMENTS.md` (Locked functional & non-functional requirements)
3. **LEVEL 3**: `BILLING_2_0_ARCHITECTURE.md` (Verified architecture & technology decisions)
4. **LEVEL 4**: `BILLING_2_0_DATA_CONTRACT.md` (Verified data relationships & schema contracts)
5. **LEVEL 5**: `BILLING_2_0_DOCUMENT_RULES.md` (Word fidelity & reference document rules)
6. **LEVEL 6**: `BILLING_2_0_PROJECT_STATE.md` (Current live implementation state)
7. **LEVEL 7**: `BILLING_2_0_ROADMAP.md` (Planned milestone progression)
8. **LEVEL 8**: `BILLING_2_0_AGENT_RULES.md` (AI agent operational rules & constraints)
9. **LEVEL 9**: `BILLING_2_0_CHANGE_CONTROL.md` (Protocol for proposing and authorizing changes)
10. **LEVEL 10**: `BILLING_2_0_VERIFICATION.md` (Testing & verification protocol ledger)

---

## 2. Locked Requirements

The following core requirements are strictly locked and must **never** be altered without explicit user approval:

1. **Unified Duty Slip Scans**: Front and back scans of a duty slip represent **ONE** unified duty-slip record.
2. **Original Scan Retention**: Original scan files must always be preserved immutably in storage.
3. **No Hallucinated Data**: OCR/Vision AI must read only what is actually present on physical scans. **Never guess** missing, illegible, or unreadable values.
4. **Preserved Uncertainty**: Low-confidence or unreadable values must be flagged (`needs_review = true`) and routed to human review.
5. **Human Review Authority**: Human review and editing is required before final verification. Manually verified values become the structured source of truth.
6. **Auditability**: Original raw OCR extractions and human-corrected values must both remain permanently auditable.
7. **No Universal Billing Rules**: Different companies have different billing/document rules. Never assume universal tariffs, rates, minimums, or tax calculations.
8. **Document Fidelity**: The existing company Word bill format is the primary formatting reference. Generated documents must faithfully reproduce the client's actual Word format rather than introducing generic invoice designs.
9. **Same Company → Same Master Document**: All bills generated for the same company must be sequentially appended into that company's single master Word document (`<CompanyName>.docx`).
10. **Different Companies → Isolated Documents**: Master documents and workspaces are strictly isolated per company. Company B bills must never appear in Company A's document or workspace.
11. **Browser PDF Visibility**: Master Word documents must be viewable directly in the browser via high-fidelity PDF rendering.
12. **Structured DB vs Human Archive**: MongoDB is the structured source of truth; DOCX is the authoritative human-readable document archive.
13. **Duplicate Prevention**: Duplicate duty slips must be detected and prevented according to established rules.
14. **Human Verification for Step Completion**: Automated tests alone never mark a step `VERIFIED`. Explicit human verification is required.

---

## 3. Technology / Current Architecture

Only the implemented, verified technology stack is documented here:

- **Frontend**: React 18, Vite, React Router v6, Tailwind CSS
- **Backend**: Python 3.11, FastAPI, Uvicorn
- **Database**: MongoDB (`billing_db`) via PyMongo
- **Document Generation**: `python-docx`
- **Storage Layer**: Modular `LocalStorageService` with strict company directory isolation (`storage/companies/<company_id>/...`)
- **OCR / Vision AI**: Provider abstraction (`MockOCRProvider` default test pipeline, `GeminiVisionOCRProvider` for live API)

---

## 4. Development Rules

All agent and developer actions must adhere to these rules:

1. **Read `BILLING_2_0_ROADMAP.md` first.**
2. **Read `BILLING_2_0_PROJECT_STATE.md` second.**
3. Inspect existing code before proposing changes.
4. Reuse existing implementations and abstractions before creating new ones.
5. Do not create duplicate abstractions or bloat dependencies.
6. Do not invent fields, billing rules, document sections, taxes, invoice structures, workflows, or UI features.
7. If information is missing, report it as `UNKNOWN / NEEDS USER CONFIRMATION` rather than guessing.
8. If a requested change conflicts with this roadmap or project state, STOP and report the conflict.
9. Never silently expand scope.
10. A step is `VERIFIED` only after implementation, automated testing, visual inspection where applicable, and explicit human verification.
11. Do not move to the next step until the current step is explicitly verified by the user.

---

## 5. Step History

- **Step 1: Repository Inspection** — `[VERIFIED]`
- **Step 2: Project Foundation & Control** — `[VERIFIED]`
- **Step 3: Company Management** — `[VERIFIED]`
- **Step 4: Duty Slip Management** — `[VERIFIED]`
- **Step 5: OCR / AI Extraction** — `[VERIFIED]`
- **Step 6: Human Review / Editing** — `[VERIFIED]`
- **Step 7: Word Document Generation & Company Master Architecture** — `[IMPLEMENTED / AWAITING HUMAN VERIFICATION]`
- **Step 8: Bill Approval & Advanced Master Workflow** — `[NOT STARTED]`
- **Step 9: Complete Automation Workflow** — `[NOT STARTED]`
- **Step 10: Production Hardening** — `[NOT STARTED]`

---

## 6. Step 7 — Current Status

Step 7 implements:

- Company master Word document generation (`<CompanyName>.docx`)
- Same-company sequential bill append behavior (A4 page break per bill)
- Multi-company document isolation
- Company Workspace Overview with master document card & generated bills
- In-browser PDF preview modal
- Faithful 9-column billing table mapping

**Verified Functionality**:

- Vehicle number `TS09GC6246 A/c Sedan` correctly consumed from verified data.
- 9-Column Table (`Duty Slip No.`, `Date`, `Vehicle No.`, `Total Kms`, `Total Hrs.`, `Extra Kms.`, `Extra Hrs.`, `Amt`, `Total Amount`) verified.
- Calculation expressions under `Amt` (`8/80`, `67 x 15`, `1.5 x 150`, `Bata`, `Toll`) and currency amounts under `Total Amount` (`2500.00`, `1005.00`, `225.00`, `250.00`, `40.00`) verified.
- Total `₹4020.00` verified.
- Same company bills inside one master document verified.
- Different company document isolation verified.
- Browser PDF viewer modal verified.
- Full Company Workspace flow verified.

---

## 7. Known Step 7 Discrepancies & Corrections

### A. Header Typography & Colors

- **Target**: Imprint MT Shadow title ("SRI TULJA BHAVANI TRAVELS" 27pt in Navy Blue `#002060`), Subtitle ("RENT-A-CAR" 20pt in Red `#FF0000`), Phone number (`#0070C0` centered), Address/Email, and horizontal dividing separator beneath the header.

### B. Outer Page Border

- **Target**: Solid outer page border matching the reference document structure (`<w:pgBorders>`).

### C. Footer Typography

- **Target**: Typography styling for `Rupees (in words): ...`, `For Sri Tulja Bhavani Travels`, and sign-offs matching the reference document.

### D. Table Data Row Height

- **Target**: Open/tall minimum data row height (`trHeight` >= 2663 dxa / ~133pt) matching the reference layout while preserving the 9-column structure and data mapping.

### E. Recipient Block

- **Target**: `To,` followed by available recipient/customer name.
- **Status on Full Multi-Line Address/GSTIN**: The current application schema only stores `name` / `customer_name`. Full multi-line street address, phone, fax, and GSTIN are not part of the current schema and are marked `UNKNOWN / NEEDS USER CONFIRMATION` (never fabricated).

---

## 8. Next Roadmap

The immediate task is:

**STEP 7 — DOCUMENT FIDELITY CORRECTION**

After this correction is implemented, tested, and visually compared:

1. Present the rendered output to the user.
2. Await explicit human verification.
3. Once Step 7 is marked `[VERIFIED]`, STOP and wait for explicit user direction for Step 8.

Future Steps:

- **Step 8**: `NOT DEFINED — WAITING FOR USER REQUIREMENTS`
- **Step 9**: `NOT DEFINED — WAITING FOR USER REQUIREMENTS`
- **Step 10**: `NOT DEFINED — WAITING FOR USER REQUIREMENTS`

---

## 9. Change Control

Every implementation task must explicitly specify:

- Current step
- Requested change
- Rationale
- Files expected to change
- Files that must not change
- Automated tests required
- Visual / manual verification required
- Project state update requirement

---

## 10. Anti-Hallucination Rule

If code, project state, roadmap, sample documents, tests, or user requirements do not provide sufficient information to implement a feature:

**DO NOT GUESS OR FABRICATE DATA.**

Report:

`UNKNOWN / NEEDS USER CONFIRMATION`

and stop.
