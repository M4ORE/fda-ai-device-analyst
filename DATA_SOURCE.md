# Data Source Documentation

## Official FDA Source

### Main Page
**URL:** https://www.fda.gov/medical-devices/software-medical-device-samd/artificial-intelligence-enabled-medical-devices

**Description:** FDA's official list of AI/ML-enabled medical devices that have received marketing authorization.

### Excel File Download
**Direct Link:** https://www.fda.gov/media/178540/download?attachment

**File Name:** `ai-ml-enabled-devices-excel.xlsx`

**Content:** List of AI/ML-enabled medical devices with:
- Date of Final Decision
- Submission Number (510(k), De Novo, PMA)
- Device Name
- Company
- Panel (lead)
- Primary Product Code

### PDF Summaries

**Location:** `summaries/` folder

**Format:** PDF files named by submission number (e.g., `K251406.pdf`)

**Content:** FDA 510(k) and De Novo decision letters containing:
- Device description
- Intended use
- Technological characteristics
- Performance data
- Regulatory decision

**Note:** PMA (Premarket Approval) summaries are not included in this dataset.

## Update Procedure

### Automated Update (Recommended)

```bash
run_update.bat
```

Or manually:

```bash
venv\Scripts\python.exe src\update.py
```

This automated script will:

1. **Download Latest Excel** from FDA website
   - URL: https://www.fda.gov/media/178540/download?attachment
   - Saves as `ai-ml-enabled-devices-excel_new.xlsx`

2. **Compare Changes**
   - Identifies new devices
   - Lists removed devices (if any)
   - Shows statistics

3. **Check Missing/Corrupted PDFs**
   - Scans all devices in database
   - Identifies missing PDF files
   - Detects corrupted or failed extractions (text < 100 chars)

4. **Download PDFs Automatically**
   - **510(k)**: `https://www.accessdata.fda.gov/cdrh_docs/pdf{YY}/{submission}.pdf`
   - **De Novo**: `https://www.accessdata.fda.gov/cdrh_docs/reviews/{submission}.pdf`
   - **PMA**: Cannot auto-download (manual process required)

5. **Update Database**
   - Extracts text from new/re-downloaded PDFs
   - Updates SQLite with new data
   - Creates backup of old Excel file

6. **Finalize**
   - Replaces old Excel with new version
   - Shows update summary

### Manual Update Process

If automated update fails or for PMA devices:

#### 1. Download PDFs Manually

**510(k) Database:**
https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm

**De Novo Database:**
https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/denovo.cfm

**PMA Database:**
https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpma/pma.cfm

Search by submission number, download PDF, save to `summaries/` folder.

#### 2. Re-run Full Extraction

```bash
# Backup existing database
copy data\devices.db data\devices.db.backup

# Run full extraction
venv\Scripts\python.exe src\extract.py
```

#### 3. Rebuild Vector Database

```bash
venv\Scripts\python.exe src\embed.py
```

## Data Statistics (as of 2025-10-06)

- **Total Devices in Excel:** 1,247
- **Successfully Extracted:** 1,228 (98.5%)
- **510(k) Devices:** ~1,200
- **De Novo Devices:** ~30
- **PMA Devices:** 16 (PDFs not available)

### Date Range
- **Earliest Approval:** 2003
- **Latest Approval:** 2025-05-30

### Top Panels
- Radiology
- Cardiovascular
- Clinical Chemistry
- Hematology
- Microbiology

## FDA Device Classification

### 510(k) Premarket Notification
- **Prefix:** K (e.g., K251406)
- **Approval Type:** Substantial equivalence
- **PDF Location:** summaries/K*.pdf
- **Count in Dataset:** ~1,200

### De Novo Classification
- **Prefix:** DEN (e.g., DEN240047)
- **Approval Type:** Novel device, low-moderate risk
- **PDF Location:** summaries/DEN*.pdf
- **Count in Dataset:** ~30

### Premarket Approval (PMA)
- **Prefix:** P (e.g., P210011)
- **Approval Type:** High-risk devices
- **PDF Location:** Not included in summaries folder
- **Count in Dataset:** 16 (metadata only)

## Legal Notice

This data is publicly available from the U.S. Food and Drug Administration (FDA).

- **Source:** FDA.gov
- **License:** Public domain (U.S. Government work)
- **Disclaimer:** This dataset is for informational purposes only. Always refer to official FDA databases for regulatory decisions.

## Related FDA Resources

- **510(k) Database:** https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm
- **De Novo Database:** https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/denovo.cfm
- **Device Classification:** https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpcd/classification.cfm
- **Product Code Database:** https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpcd/pcdsimplesearch.cfm
