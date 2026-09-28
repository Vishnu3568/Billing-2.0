# Billing 2.0 — Requirements & Control Contract

## 1. Project Purpose

Billing 2.0 is an automated billing and document management platform designed to streamline:

- Duty slip ingestion (front and back physical scans as one unified record)
- Automated data extraction using OCR and Vision AI
- Human review, verification, and editing with complete audit trail
- Faithful reproduction of company-specific Word billing documents (`.docx`)
- Company-isolated master document management where all bills for a company reside in that company's single master document
- Company Workspace for centralized visibility and auditability of bills, duty slips, and files.

---

## 2. Core Workflow

```text
Duty Slip Front + Back
        ↓
Image Preprocessing & Storage
        ↓
OCR / Vision AI Extraction
        ↓
Structured Extracted Data
        ↓
Validation & Confidence Scoring
        ↓
Human Review / Manual Editing
        ↓
Verified Structured Data
        ↓
Company-Specific Word Document Generation
        ↓
Bill Approval & Master Document Append
        ↓
Immutable Storage & Audit History
```

---

## 3. Locked Requirements

The following requirements are locked and must **never** be altered or bypassed without explicit user authorization:

1. **Unified Duty Slip Scans**: Front and back scans of a physical duty slip represent **ONE** unified duty-slip record. They must never be treated as separate slips.
2. **Original Scan Retention**: Original scan files must always be preserved immutably in storage. They are permanent source evidence.
3. **No Hallucinated Data**: OCR and Vision AI must extract only what is physically present on scans. **Never guess, invent, or extrapolate** missing, illegible, or unreadable values.
4. **Preserved Uncertainty**: Low-confidence or unreadable values must be flagged (`needs_review = true`, `confidence < 0.80`, or `value: null`) and routed to human review.
5. **Distinct Numbering Concepts**:
   - Physical Duty Slip Number (printed on physical slip, e.g. "47")
   - System-assigned sequential Duty Slip Number / internal MongoDB identifier
   - Bill Number (e.g. "Bill 01", sequential within company master document).
   These are separate concepts and must not be conflated.
6. **Mandatory Human Review**: Human review and editing is required before final verification. Manually verified values become the structured source of truth.
7. **Auditability**: Original raw OCR extractions, human-corrected values, editing actor, and timestamp must remain permanently auditable.
8. **No Universal Billing Rules**: Different companies have different billing and document rules. Never assume universal tariffs, rates, minimum packages, extra-km rates, extra-hour rates, or tax calculations.
9. **Document Fidelity**: Existing company Word bill formats (such as reference files in `Sample Bills/`) are the primary formatting reference. Generated documents must faithfully reproduce the client's actual Word format rather than introducing generic invoice designs.
10. **Same Company → Same Master Document**: All bills generated for the same company must be sequentially appended into that company's single master Word document (`<CompanyName>.docx`).
11. **Different Companies → Isolated Documents**: Master documents, storage directories, and workspaces are strictly isolated per company. Company B bills must never appear in Company A's document, storage, or workspace.
12. **Master Document Filename**: The authoritative master Word document filename is `<CompanyName>.docx`.
13. **Year-Wise Billing Organization**: Bills within a master document must be organized year-wise according to established company rules.
14. **Browser PDF Visibility**: Master Word documents must be viewable directly in the browser via high-fidelity PDF rendering.
15. **Source-of-Truth Hierarchy**:
    - **Database (MongoDB)**: Structured source of truth for application state.
    - **Original Scans**: Immutable source material.
    - **Word Document (`.docx`)**: Authoritative human-readable document archive.
    - **PDF Document**: Viewing and rendering representation.
16. **No Invented Content**: Never invent missing recipient addresses, GSTIN numbers, customer details, tax rows, or billing table sections. If reference documents contain fields that the source duty slip lacks, leave them unpopulated rather than fabricating data.

---

## 4. Explicitly Forbidden Assumptions

The agent must **never** make any of the following assumptions:

- DO NOT assume all companies use the same tariff rates (e.g. 8/80 = 2500, 15/km, 150/hr).
- DO NOT assume tax rules (GST, CGST, SGST, IGST) unless explicitly specified and approved for that company.
- DO NOT assume calendar year vs financial year for bill numbering reset unless explicitly confirmed by the user.
- DO NOT assume missing physical slip data can be filled in from other customer records automatically.
- DO NOT assume a generic PDF/Word template is acceptable when a reference format exists.
- DO NOT assume automated test passes equate to human verification.

---

## 5. Security & Data Integrity Requirements

1. **Company Directory Isolation**: All file storage must be strictly scoped under `backend/storage/companies/<company-id>/`.
2. **Immutable Scans**: Scans once uploaded must never be overwritten, modified, or deleted during document generation or review.
3. **Audit Trail Integrity**: Any human edit to extracted data must generate an immutable audit log entry containing:
   - `field_name`
   - `old_value`
   - `new_value`
   - `editor` (user ID or reviewer username)
   - `timestamp`
4. **Duplicate Slip Prevention**: Duty slips with duplicate numbers within the same company must be flagged and prevented from silent overwrites.

---

## 6. Current Known Limitations & UNKNOWN Items

The following items are not yet established or locked:

- **Bill Numbering Reset Schedule**:
  `STATUS: UNKNOWN — USER CONFIRMATION REQUIRED`
  (Whether annual reset follows the Calendar Year [Jan 1] or Financial Year [Apr 1] is pending user confirmation).
- **Authentication & Multi-User Authorization**:
  `STATUS: UNKNOWN — USER CONFIRMATION REQUIRED`
  (JWT auth is scaffolded in code but currently inactive; user roles and permissions are not yet defined).
- **Company-Specific Tariff Engines**:
  `STATUS: UNKNOWN — USER CONFIRMATION REQUIRED`
  (Automated calculation of extra KMs, hours, bata, and tolls across different company contracts is deferred to future steps).
- **Other Company Document Templates**:
  `STATUS: UNKNOWN — USER CONFIRMATION REQUIRED`
  (Templates for companies other than Sri Tulja Bhavani Travels / Windsor Machines reference format require explicit inspection of `Sample Bills/` before implementation).
