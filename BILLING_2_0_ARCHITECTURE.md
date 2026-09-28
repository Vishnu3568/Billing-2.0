# Billing 2.0 — Architecture & Technology Contract

## 1. Architectural Philosophy

Billing 2.0 operates on four foundational data pillars:

```text
DATABASE = STRUCTURED SOURCE OF TRUTH (MongoDB)
ORIGINAL SCANS = IMMUTABLE SOURCE MATERIAL (Disk Storage)
DOCX = HUMAN-READABLE MASTER DOCUMENT & PERMANENT ARCHIVE (Disk Storage)
PDF = VIEWING & RENDERING REPRESENTATION (On-the-fly / Cached COM Export)
```

---

## 2. Actual Verified System Architecture

```text
Frontend (React 18 + Vite + Tailwind CSS + React Router v6)
              │
              │ REST API (/api/v1) [JSON & Multipart]
              ▼
Backend (FastAPI + Uvicorn + Python 3.11)
  ├── API Layer (Endpoints: health, auth, companies, duty_slips, extractions)
  ├── Service Layer (CompanyService, DutySlipService, ExtractionService, StorageService, WordBillService)
  ├── OCR Pipeline (BaseOCRProvider abstraction: MockOCRProvider, GeminiVisionOCRProvider, Validator)
  └── Word Generator (python-docx + win32com COM Word-to-PDF converter)
              │
    ┌─────────┴─────────┐
    ▼                   ▼
MongoDB (billing_db)  File Storage (LocalStorageService)
  - companies           backend/storage/companies/<company_id>/
  - duty_slips            ├── master/<CompanyName>.docx
  - extractions           └── duty_slips/<duty_slip_id>/[front, back]
```

---

## 3. Detailed Component Breakdown

### A. Frontend
- **Framework**: React 18 with Vite build tooling.
- **Routing**: React Router v6.
- **Styling**: Tailwind CSS with custom component utilities.
- **Key Modules**:
  - `Dashboard.jsx`: Overall operational metrics and activity feed.
  - `Companies.jsx`: Company list, company creation modal, company deactivation, search.
  - `CompanyWorkspace.jsx`: Centralized workspace for a selected company.
    * Overview tab with Master Word Document card, bill count, download DOCX, and preview PDF modal.
    * Duty Slips tab with company-filtered duty slip list.
    * Scans & Files tab for file traceability.
  - `DutySlips.jsx`: Duty slip list, upload modal (front + back), OCR trigger, and Human Review modal with side-by-side scan view and field audit trail.
  - `client.js`: Centralized Axios-based API client communicating with `/api/v1`.

### B. Backend
- **Framework**: FastAPI on Python 3.11 with asynchronous endpoint support and Uvicorn ASGI server.
- **API Routing**: Modular routers registered under `/api/v1`:
  - `/health`: Database connectivity and service health check.
  - `/auth`: Authentication placeholder / scaffold.
  - `/companies`: Company CRUD, workspace endpoints, master document metadata, DOCX download, and PDF stream.
  - `/duty-slips`: Duty slip upload, metadata retrieval, scan file serving, status tracking.
  - `/duty-slips/{id}/extract`: OCR extraction trigger, extraction retrieval, human review field correction, verification.
  - `/duty-slips/{id}/word-bill`: Single bill generation and company master document append.

### C. Database
- **Database Engine**: MongoDB 6.0+ running on `mongodb://localhost:27017`.
- **Database Name**: `billing_db`.
- **Driver**: PyMongo (`pymongo.MongoClient`) wrapped in dependency-injected session management (`app.core.database.get_db`).
- **Core Collections**:
  - `companies`: Company metadata, codes, status.
  - `duty_slips`: Unified duty slip records, front/back scan references, workflow status.
  - `extractions`: OCR raw extractions, field-level confidence scores, review flags, human edit history (`audit_trail`), and verified data snapshots.

### D. File Storage Layer
- **Abstraction**: `BaseStorageService` with `LocalStorageService` implementation (`backend/app/services/storage/`).
- **Isolation Rule**: Storage is partitioned strictly by company ID:
  ```text
  backend/storage/companies/<company_id>/
  ├── master/
  │   └── <CompanyName>.docx
  └── duty_slips/
      └── <duty_slip_id>/
          ├── front_<hash>.jpeg
          └── back_<hash>.jpeg
  ```

### E. Document Processing & Generation
- **DOCX Engine**: `python-docx` for creating and appending Word documents conforming to reference fidelity.
- **Document Model**: One master Word document per company (`<CompanyName>.docx`).
- **Sequential Append**: New bills are added as new sections with an A4 page break, duplicating header, table, and footer structures.
- **PDF Conversion Engine**: Microsoft Word COM Automation (`win32com.client` with `Word.Application` Dispatch) converting DOCX to high-fidelity PDF with clean COM release and temporary file cleanup in a guaranteed `try...finally` block.

### F. OCR / Vision AI Engine
- **Provider Abstraction**: `BaseOCRProvider` interface.
- **Mock Provider**: `MockOCRProvider` providing deterministic test extractions with intentional review flags for validation.
- **Live Provider**: `GeminiVisionOCRProvider` using Google Gemini Vision API for multi-modal scan inspection.
- **Validation Layer**: `ExtractionValidator` calculating per-field confidence, consistency checks (e.g. `closing_km >= opening_km`), and flagging low-confidence fields.

---

## 4. Implementation Status Classification

| Component | Status | Notes |
|---|---|---|
| Company Management CRUD | **IMPLEMENTED** | Verified in Step 3 |
| Front/Back Unified Duty Slip Upload | **IMPLEMENTED** | Verified in Step 4 |
| Company Storage Isolation | **IMPLEMENTED** | Verified in Step 4 & 7 |
| Mock OCR Extraction Pipeline | **IMPLEMENTED** | Verified in Step 5 |
| Extraction Validation & Review Flagging | **IMPLEMENTED** | Verified in Step 5 |
| Human Review & Audit Trail | **IMPLEMENTED** | Verified in Step 6 |
| Master Word Document Generation (`.docx`) | **IMPLEMENTED** | Verified in Step 7 |
| Sequential Bill Append into Master DOCX | **IMPLEMENTED** | Verified in Step 7 |
| In-Browser PDF Rendering & Viewer | **IMPLEMENTED** | Verified in Step 7 |
| Company Workspace Overview & Tabs | **IMPLEMENTED** | Verified in Step 7 |
| Live Gemini Vision OCR Integration | **IMPLEMENTED** | Tested; mock provider remains default for offline tests |
| Bill Approval & Advanced Master Workflow | **NOT STARTED** | Reserved for Step 8 |
| Automated Batch Slip Ingestion | **NOT STARTED** | Reserved for Step 9 |
| Production Hardening & Cloud Storage | **NOT STARTED** | Reserved for Step 10 |
| JWT Authentication & Multi-User Roles | **NOT IMPLEMENTED** | Scaffolded only; inactive |
| Annual Reset Workflow (Calendar vs Financial) | **UNKNOWN** | Requires explicit user decision |
| Multiple Document Template Engines | **UNKNOWN** | Only Sri Tulja Bhavani / Windsor template verified |
