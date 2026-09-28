# Billing 2.0 — Data Contract & Schema Architecture

## 1. Entity Lifecycle & Relationships

The data model follows a strict unidirectional lifecycle from raw physical scans to an authoritative company master document:

```text
Company (1)
  │
  └── Duty Slips (N) [Each has 1 front scan + optional 1 back scan]
        │
        └── Extraction (1:1) [Raw OCR/AI fields + confidence scores]
              │
              └── Human Review / Audit Trail [Per-field corrections + editor stamps]
                    │
                    └── Verified Structured Data [Source of truth for billing]
                          │
                          └── Bill (1:1 with Duty Slip, e.g. "Bill 01")
                                │
                                └── Company Master Document (1:N bills appended)
```

---

## 2. Key Numbering & Identification Rules

1. **Company ID**: MongoDB `ObjectId` (24-char hex string) uniquely identifying the company across database and storage paths (`storage/companies/<company_id>/`).
2. **Physical Duty Slip Number**: The human-readable or pre-printed number on the physical duty slip (e.g. `"47"`). Extracted via OCR or entered by the user.
3. **Internal Duty Slip ID**: MongoDB `ObjectId` representing the unique duty slip database record.
4. **Bill Number**: The sequential invoice or bill number within that company's master document (e.g. `"Bill 01"`, `"Bill 02"`). It is company-scoped and resets according to the year-wise schedule.

---

## 3. Verified Active Database Collections & Schemas

### A. `companies` Collection

Represents a client company.

| Field | Type | Verified Status | Description |
|---|---|---|---|
| `_id` | `ObjectId` | VERIFIED EXISTING | Unique company identifier |
| `name` | `string` | VERIFIED EXISTING | Full company name (used for master doc filename) |
| `code` | `string` | VERIFIED EXISTING | Unique uppercase short code (e.g. `FVL`) |
| `address` | `string \| null` | VERIFIED EXISTING | Registered company address |
| `gstin` | `string \| null` | VERIFIED EXISTING | Goods and Services Tax Identification Number |
| `contact_email` | `string \| null` | VERIFIED EXISTING | Billing/contact email address |
| `contact_phone` | `string \| null` | VERIFIED EXISTING | Contact telephone number |
| `is_active` | `boolean` | VERIFIED EXISTING | Active/deactivated company status flag |
| `created_at` | `datetime` | VERIFIED EXISTING | Record creation timestamp |
| `updated_at` | `datetime` | VERIFIED EXISTING | Last modification timestamp |

### B. `duty_slips` Collection

Represents a single unified physical duty slip containing its scans and processing status.

| Field | Type | Verified Status | Description |
|---|---|---|---|
| `_id` | `ObjectId` | VERIFIED EXISTING | Unique duty slip record identifier |
| `company_id` | `ObjectId` | VERIFIED EXISTING | Foreign key referencing parent company |
| `duty_slip_no` | `string` | VERIFIED EXISTING | Physical slip number (e.g. `"47"`) |
| `front_scan` | `ScanFile` | VERIFIED EXISTING | Front scan file metadata (path, size, content_type, filename) |
| `back_scan` | `ScanFile \| null` | VERIFIED EXISTING | Optional back scan file metadata |
| `has_back_scan` | `boolean` | VERIFIED EXISTING | Flag indicating presence of back scan |
| `status` | `string` | VERIFIED EXISTING | Enum: `uploaded`, `processing`, `extracted`, `verified`, `billed` |
| `notes` | `string \| null` | VERIFIED EXISTING | Optional operator or audit notes |
| `has_word_bill` | `boolean` | VERIFIED EXISTING | True if appended to master Word document |
| `word_bill` | `WordBillInfo \| null` | VERIFIED EXISTING | Embedded object: `bill_no`, `stored_filename`, `storage_path`, `generated_at` |
| `created_at` | `datetime` | VERIFIED EXISTING | Ingestion timestamp |
| `updated_at` | `datetime` | VERIFIED EXISTING | Status update timestamp |

### C. `extractions` Collection

Represents the raw OCR extraction, confidence metadata, validation flags, human review corrections, audit trail, and verified data snapshot.

| Field | Type | Verified Status | Description |
|---|---|---|---|
| `_id` | `ObjectId` | VERIFIED EXISTING | Unique extraction record identifier |
| `duty_slip_id` | `ObjectId` | VERIFIED EXISTING | Foreign key referencing parent duty slip |
| `provider` | `string` | VERIFIED EXISTING | Name of OCR provider used (`mock`, `gemini_vision`) |
| `fields` | `dict[str, ExtractedField]` | VERIFIED EXISTING | Extracted fields dictionary (see field structure below) |
| `overall_confidence`| `float` | VERIFIED EXISTING | Aggregated average confidence (0.00 to 1.00) |
| `flags` | `list[str]` | VERIFIED EXISTING | Consistency and review flag codes (e.g. `low_confidence`) |
| `status` | `string` | VERIFIED EXISTING | Status: `extracted`, `reviewed`, `verified` |
| `audit_trail` | `list[AuditTrailEntry]` | VERIFIED EXISTING | Immutable list of human edits (`field_name`, `old_value`, `new_value`, `editor`, `timestamp`) |
| `verified_data` | `dict \| null` | VERIFIED EXISTING | Flattened verified field values used for document generation |
| `created_at` | `datetime` | VERIFIED EXISTING | OCR extraction timestamp |
| `updated_at` | `datetime` | VERIFIED EXISTING | Review/verification timestamp |

---

## 4. Extracted & Verified Field Data Model

The `fields` mapping in `extractions` contains structured field records conforming to:

```python
class ExtractedField:
    value: Any                  # Extracted value (string, float, date, or null)
    confidence: float           # 0.0 to 1.0 score
    needs_review: bool          # Flagged if low confidence or rule mismatch
    review_reason: str | None   # Explanation for review flag
    raw_text: str               # Exact verbatim OCR text before normalization
    source_side: str            # 'front' or 'back' scan
    original_value: Any         # Unchanged raw extraction value for auditability
    edited: bool                # True if human modified this field
    edited_at: datetime | None  # Edit timestamp
    edited_by: str | None       # Reviewer username / identity
```

### Standard Duty Slip Extracted Fields

| Field Name | Type | Description |
|---|---|---|
| `duty_slip_number` | `string` | Printed duty slip number |
| `date` | `string` | Duty slip execution date (`DD-MM-YYYY`) |
| `customer_name` | `string` | Customer / passenger party name |
| `vehicle_number` | `string` | Vehicle registration and type (e.g. `TS09GC6246 A/c Sedan`) |
| `driver_name` | `string` | Name of the driver |
| `starting_km` | `float` | Opening odometer reading |
| `closing_km` | `float` | Closing odometer reading |
| `total_km` | `float` | Total kilometers run (`closing_km - starting_km`) |
| `starting_time` | `string` | Starting time of duty |
| `closing_time` | `string` | Ending time of duty |
| `total_hours` | `float` | Total duty hours elapsed |
| `package_name` | `string \| null` | Base tariff package identifier (e.g. `8/80 = 2500`) |
| `extra_km` | `float \| null` | Additional KMs driven beyond base package |
| `extra_hours` | `float \| null` | Additional hours elapsed beyond base package |
| `extra_km_amount` | `float \| null` | Charge for extra KMs (e.g. `67 x 15 = 1005`) |
| `extra_hours_amount`| `float \| null` | Charge for extra hours (e.g. `1.5 x 150 = 225`) |
| `bata` | `float \| null` | Driver allowance / Bata amount (e.g. `Bata = 250`) |
| `toll_parking` | `float \| null` | Toll and parking fees (e.g. `Toll = 40`) |
| `total_amount` | `float` | Final calculated or printed invoice total (e.g. `4020.00`) |

---

## 5. Status Summary of Relationships

- **Unified Front/Back Scan**: `VERIFIED EXISTING`
- **Duty Slip to Company Scoping**: `VERIFIED EXISTING`
- **Extraction Audit Trail**: `VERIFIED EXISTING`
- **Verified Data Snapshot**: `VERIFIED EXISTING`
- **Master DOCX Path Scoping**: `VERIFIED EXISTING`
- **Multi-Year Archive Schema**: `PLANNED` (Deferred to Step 8)
- **Batch Processing Queue Records**: `PLANNED` (Deferred to Step 9)
- **User Authentication / RBAC Schemas**: `PLANNED` (Deferred to Step 10)
