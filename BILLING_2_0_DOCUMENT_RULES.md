# Billing 2.0 — Document Rules & Word Fidelity Contract

## 1. Primary Rule of Document Fidelity

1. **Client Reference Documents Are Law**: The existing company Word documents (stored in `Sample Bills/`) are the authoritative visual and structural source of truth.
2. **No Invented Templates**: Never replace the client's established Word document structure with a generic invoice template, modern minimalist layout, or arbitrary grid system.
3. **Company-Specific Variance**: Different companies may have distinct document designs, header banners, table columns, fonts, and footer clauses. Never force one company's layout onto another.
4. **Master Document Architecture**:
   - All bills for a company must be appended sequentially into that company's single master Word document.
   - Master document filename must be `<CompanyName>.docx`.
   - Master document storage path: `backend/storage/companies/<company_id>/master/<CompanyName>.docx`.
   - Each company has its own isolated master document. Documents from different companies must never be combined or co-located.

---

## 2. Verified Step 7 Document Specification

The following rules have been implemented and verified against the reference document (`Sample Bills/Windsor  Machines injection Chhatral (Repaired).docx`):

### A. Page Setup & Dimensions
- **Page Size**: **A4** (8.27" x 11.69" / 210mm x 297mm).
  *(Locked project requirement: even if a reference sample uses Letter, generated Billing 2.0 documents must adhere to the locked A4 standard).*
- **Page Orientation**: Portrait.
- **Margins**: Top: 0.50", Bottom: 0.50", Left: 0.65", Right: 0.65".
- **Outer Page Border**: Rectangular box border surrounding the full page using OpenXML:
  ```xml
  <w:pgBorders w:offsetFrom="page">
    <w:top w:val="single" w:sz="4" w:space="24" w:color="000000"/>
    <w:left w:val="single" w:sz="4" w:space="24" w:color="000000"/>
    <w:bottom w:val="single" w:sz="4" w:space="24" w:color="000000"/>
    <w:right w:val="single" w:sz="4" w:space="24" w:color="000000"/>
  </w:pgBorders>
  ```

### B. Header Section
1. **Phone Numbers**:
   - Text: `Mobile No: 94405 22 814, 99892 08711, 9000 240 410`
   - Font: `Imprint MT Shadow`, 11pt, Deep Navy Blue (`#002060`), Centered.
2. **Company Title**:
   - Text: `SRI TULJA BHAVANI TRAVELS`
   - Font: `Imprint MT Shadow`, 27pt, Deep Navy Blue (`#002060`), Centered.
3. **Subtitle**:
   - Text: `RENT-A-CAR`
   - Font: `Imprint MT Shadow`, 20pt, Pure Red (`#FF0000`), Centered.
4. **Address & Email**:
   - Text: `1-11-113/3,P2 Sai Shikara Apartments, Shayamlal Building Begumpet, Hyderabad - 500016, srituljabhavanitravels.rentacar@gmail.com`
   - Font: `Imprint MT Shadow`, 11pt, Deep Navy Blue (`#002060`), Centered.
5. **Horizontal Separator**:
   - Single continuous horizontal border (`#002060`, 1.5pt rule) placed on the bottom paragraph border of the address run.

### C. Recipient & Metadata Block
- **Bill Number & Date Paragraph**:
  - `Bill {number}` left-aligned.
  - `Date: {DD-MM-YYYY}` right-aligned via tab stop (`\t\t\t\t\t\t             `).
  - Font: `Bookman Old Style`, 11pt.
- **Recipient Lines**:
  - Line 1: `To, ` (Bookman Old Style, 11pt).
  - Line 2: `{party_name}` (Bookman Old Style, 11pt).
- **Anti-Hallucination Recipient Rule**:
  > **CRITICAL**: If the reference document contains multi-line company addresses, divisions, or GSTINs (e.g. Windsor Machines factory addresses), but the physical duty slip / database record contains only the passenger party name (e.g. `Uday Kumar`), **DO NOT INVENT, GUESS, OR FABRICATE** the address or GSTIN. Display only the verified available data.

### D. 9-Column Billing Table
The billing table consists of 3 rows: Header Row, Multi-line Data Row, and Total Row.

#### Column Specifications & Order
| Col # | Header Title | Width | Cell Alignment | Content Rules |
|---|---|---|---|---|
| 1 | `Duty Slip No.` | 0.75" | Center | Physical slip number |
| 2 | `Date` | 0.85" | Center | Slip date (`DD-MM-YYYY`) |
| 3 | `Vehicle No.` | 1.30" | Left | Registration & vehicle class |
| 4 | `Total Kms` | 0.70" | Center | Total KM traveled |
| 5 | `Total Hrs.` | 0.70" | Center | Total elapsed duty hours |
| 6 | `Extra Kms.` | 0.75" | Center | Extra KMs beyond package |
| 7 | `Extra Hrs.` | 0.90" | Center | Extra hours beyond package |
| 8 | `Amt` | 0.75" | Left | **Calculation expressions ONLY** |
| 9 | `Total Amount` | 0.95" | Right | **Line-item currency amounts ONLY** |

#### Header Formatting
- Font: `Bookman Old Style`, 9.0pt, Bold.
- Borders: Single 0.5pt black box borders on all cells.
- Padding: 80 dxa top/bottom, 60 dxa left/right.
- Height: Minimum 770 dxa (`hRule="atLeast"`).

#### Data Row Formatting
- Minimum Row Height: Open layout with `trHeight` atLeast 2663 dxa (~1.85 inches) to match the open vertical look of reference sample bills.
- Font: `Bookman Old Style`, 10.0pt, Regular.
- Vertical Alignment: Top.
- Padding: 100 dxa top/bottom, 60 dxa left/right.

#### Column 8 vs Column 9 Separation Rule
- **Column 8 (`Amt`) MUST contain ONLY calculation expressions**:
  ```text
  8/80
  67 x 15
  1.5 x 150
  Bata
  Toll
  ```
  *(Never place numeric currency amounts in Column 8).*
- **Column 9 (`Total Amount`) MUST contain ONLY numeric currency amounts**:
  ```text
  2500.00
  1005.00
  225.00
  250.00
  40.00
  ```
  *(Never place calculation expression strings in Column 9).*

#### Verified Test Example (Duty Slip #47)
```text
Amt Expression         → Total Amount
---------------------------------------
8/80                   → 2500.00
67 x 15                → 1005.00
1.5 x 150              → 225.00
Bata                   → 250.00
Toll                   → 40.00
---------------------------------------
Total                  → 4020.00
```
> **IMPORTANT GUARDRAIL**: This calculation mapping is a verified example for current test data. It **MUST NOT** be treated as a universal formula for all companies.

#### Total Row Formatting
- Row 2 of table:
  - Columns 1–7: Blank cells.
  - Column 8: `"Total"` (Bold, Right-aligned).
  - Column 9: `"{total_amount:.2f}"` (e.g. `4020.00`, Bold, Right-aligned).

### E. Footer Section
1. **Rupees in Words**:
   - `Rupees (in words): {Amount in Words} Only`
   - Font: `Imprint MT Shadow`, 14pt, Left-aligned.
2. **Provider Sign-Off**:
   - `For Sri Tulja Bhavani Travels`
   - Font: `Imprint MT Shadow`, 14pt, Right-aligned.
3. **Client Sign-Off**:
   - `For :{party_name}`
   - Font: `Imprint MT Shadow`, 11pt, Left-aligned.
4. **Booking / Management Line**:
   - `Booked by : {driver_or_booker} \t\t\t\t\t\t\t\t Manager`
   - Font: `Imprint MT Shadow`, 11pt.

### F. Sequential Multi-Bill Append Behavior
- When appending a subsequent bill (e.g. Bill 02) into an existing master document:
  1. Insert a section break / page break (`doc.add_page_break()`).
  2. Repeat the complete A4 layout (outer border, header, recipient block, 9-column table, footer).
  3. Master document remains exactly one unified `.docx` file per company containing all bills.
