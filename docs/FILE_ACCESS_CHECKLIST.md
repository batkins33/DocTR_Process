# 🗂 FILE ACCESS CHECKLIST

**Project:** 24-105 PHMS NPC — Truck Ticket & Load Tracking System
**Purpose:** Verify and confirm accessibility of all folders, files, and data sources required for LoadMatcher / DocTR_Process extraction, validation, and reconciliation.

---

## 1. Load Tracking Data

**🔍 GDrive Shared Folder**
`G:\My Drive\Lindamood\24-105\Load Tracking\`

* [ ] `24-105_Load Tracking Log.gsheet` — confirm it opens and can be exported to `.xlsx` or `.csv`
* [ ] Verify permissions (ensure “Anyone with link” is set for AI assistants / automation scripts)
* [ ] Check for auxiliary sheets or tabs such as:

  * *“Daily Totals”*
  * *“WM Hauls”*
  * *“Material Breakdown”*
  * *“Export Logs”*

---

## 2. Project Documentation (OneDrive)

**🔍 Primary Project Directory**
`C:\Users\brian.atkins\OneDrive - Lindamood Demolition\24-105 PHMS NPC - Documents`

* [ ] Confirm standard subdirectories are visible:

  * `PM\Invoices` — invoice samples for vendor classifier
  * `truck tickets` — daily field and AP uploads
  * `Reports` — exported summaries (potential validation source)
  * `Plans` / `Schedules` — optional context for load-site mapping
* [ ] Check file permissions and sync status (ensure “Always keep on this device”)

---

## 3. Truck Ticket System (General)

**🔍 AP & Field Ticket Repository**
`C:\Users\brian.atkins\OneDrive - Lindamood Demolition\Documents - Truck Tickets\General\24-105-PHMS New Pediatric Campus`

* [ ] Date-based subfolders (`YYYY-MM-DD`)
* [ ] Subfolders:

  * `MANIFEST\COPIES FROM WM` — manifests for WM classifier
  * `Scanned Tickets` — field or AP uploads
  * `QA` or `Review` — tickets marked for audit
* [ ] Verify filenames follow convention (`JobDate_Vendor_TicketNo.pdf` or similar)

---

## 4. Historical / Reference Data

**🔍 Waste Management Archive**
`C:\Users\brian.atkins\OneDrive - Lindamood Demolition\Documents - Truck Tickets\General\Waste Management`

* [ ] Confirm invoice and manifest PDFs (2019–2025)
* [ ] Check for naming pattern (e.g. “WM Invoice ######”)

**🔍 Trucking Spreadsheets (Monthly)**
`C:\Users\brian.atkins\OneDrive - Lindamood Demolition\Documents - Truck Tickets\General\Trucking Spreadsheet`

* [ ] Files per month: `Trucking_YYYY-MM.xlsx`
* [ ] Cross-check with `24-105_Load Tracking Log` totals

---

## 5. Supplementary Folders (Optional but Recommended)

**🧠 Analysis + Pipeline**

* [ ] `U:\Dev\projects\LoadMatcher\samples\` — reference PDFs, manifests, invoices
* [ ] `U:\Dev\projects\LoadMatcher\data\` — extracted CSVs, OCR outputs, test data
* [ ] `U:\Dev\projects\DocTR_Process\extractors\` — base extractors for comparison

**📦 Archives / Legacy Data**

* [ ] `C:\LDI_TEMP\` — temporary OCR outputs or recovery data
* [ ] `U:\Automation Projects\Recovered` — archived results from previous runs

**📝 Reference Documents**

* [ ] `24-105\Schedules` — may be relevant for timeline-based load validation
* [ ] `24-105\Plans` — for potential GPS / site mapping overlays

---

## 6. Validation Data (optional but useful)

* [ ] Power Apps exports from **Truck Ticket App**

  * `truck_ticket_submissions.xlsx` (SharePoint / OneDrive sync)
* [ ] SQL Server: `TruckTicketsDB`

  * Verify master tables (`jobs`, `materials`, `sources`, `destinations`, `ticket_types`)
  * Confirm fact table `truck_tickets` receives PowerApps + OCR entries

---

## ✅ Recommended Action

Once verified, copy or export a **minimal sample set** into the repo:

```
U:\Dev\projects\LoadMatcher\samples\
│
├── invoices\           # 2–3 vendor samples (WM, Arcosa, Austin Asphalt)
├── manifests\          # representative manifest examples
├── tickets\            # 3–5 scanned ticket PDFs
├── spreadsheets\       # monthly trucking logs or load tracking exports
└── reference\          # optional: DOCX or CSV metadata examples
```

Then commit with:

```bash
git add samples/
git commit -m "Add sample input set for validation and extractor testing"
```
