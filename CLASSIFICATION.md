# AI-Powered Device Classification

## Overview

Automatic classification system using LLM to extract structured metadata from FDA device names and descriptions.

## Classification Schema

Each device is automatically tagged with:

### 1. Imaging Modality
**Purpose**: What imaging technology is used?

- `CT` - Computed Tomography
- `MRI` - Magnetic Resonance Imaging
- `X-ray` - Radiography
- `Ultrasound` - Sonography
- `Endoscopy` - Endoscopic imaging
- `ECG` - Electrocardiogram
- `EEG` - Electroencephalogram
- `PET` - Positron Emission Tomography
- `Mammography` - Breast imaging
- `Fluoroscopy` - Real-time X-ray
- `OCT` - Optical Coherence Tomography
- `Non-imaging` - No imaging involved
- `Unknown` - Cannot determine

### 2. Body Region
**Purpose**: Which anatomical area is targeted?

- `Brain` - Neurological/cerebral
- `Heart` - Cardiac
- `Chest/Lung` - Thoracic/pulmonary
- `Breast` - Mammary
- `Abdomen` - Abdominal cavity
- `Liver` - Hepatic
- `Kidney` - Renal
- `Bone/Musculoskeletal` - Skeletal system
- `Eye/Retina` - Ophthalmic
- `Vascular` - Blood vessels
- `Multi-organ` - Multiple systems
- `Not applicable` - No specific region
- `Unknown` - Cannot determine

### 3. Clinical Application
**Purpose**: What is the primary clinical use?

- `Screening` - Early detection in asymptomatic patients
- `Diagnosis` - Identifying specific conditions
- `Treatment Planning` - Guiding therapeutic decisions
- `Monitoring` - Tracking disease progression
- `Risk Assessment` - Predicting future events
- `Image Enhancement` - Improving image quality
- `Workflow Optimization` - Efficiency improvements
- `Detection/Segmentation` - Identifying anatomical structures
- `Unknown` - Cannot determine

## Usage

### One-time Classification

Run classification on all devices:

```bash
run_classify.bat
```

Or manually:

```bash
venv\Scripts\python.exe src\classify.py
```

**Options:**
- `--limit N` - Classify only first N devices (for testing)
- `--batch-size N` - Commit every N devices (default: 10)
- `--stats` - Show statistics only, no classification

**Example:**
```bash
# Test on 10 devices first
python src\classify.py --limit 10

# Full classification with larger batches
python src\classify.py --batch-size 20

# View statistics
python src\classify.py --stats
```

### Performance

- **Speed**: ~2 seconds per device (depends on LLM model)
- **Total time**: 40-60 minutes for 1200+ devices
- **Model**: Uses Ollama model specified in `.env` (default: gpt-oss:latest)
- **Temperature**: 0.1 (low for consistent classification)

### After Classification

Restart the Streamlit app to see new filters:

```bash
run_app.bat
```

Navigate to **Competition** page to see:
- **Imaging Modality** filter (CT, MRI, X-ray, etc.)
- **Body Region** filter (Brain, Heart, Chest, etc.)
- **Clinical Application** filter (Screening, Diagnosis, etc.)

## Examples

### Use Case 1: "Who are my competitors in brain MRI screening?"

**Filters:**
- Imaging Modality: `MRI`
- Body Region: `Brain`
- Clinical Application: `Screening`

**Result:** List of all companies with brain MRI screening devices

### Use Case 2: "What CT-based devices target the chest?"

**Filters:**
- Imaging Modality: `CT`
- Body Region: `Chest/Lung`
- Clinical Application: `All`

**Result:** All CT chest imaging devices across all applications

### Use Case 3: "Show me all treatment planning AI devices"

**Filters:**
- Imaging Modality: `All`
- Body Region: `All`
- Clinical Application: `Treatment Planning`

**Result:** All devices used for treatment planning regardless of modality or body region

## Technical Details

### Database Schema

New columns added to `devices` table:

```sql
ALTER TABLE devices ADD COLUMN imaging_modality TEXT;
ALTER TABLE devices ADD COLUMN body_region TEXT;
ALTER TABLE devices ADD COLUMN clinical_application TEXT;
ALTER TABLE devices ADD COLUMN ai_tags_version TEXT;
```

Indexes created for fast filtering:

```sql
CREATE INDEX idx_imaging_modality ON devices(imaging_modality);
CREATE INDEX idx_body_region ON devices(body_region);
CREATE INDEX idx_clinical_application ON devices(clinical_application);
```

### Classification Logic

1. **Input**: Device name, panel, product code
2. **LLM Prompt**: Structured classification template
3. **Output**: JSON with three classification fields
4. **Validation**: Parse JSON and verify required fields
5. **Storage**: Update database with classifications

### Re-classification

To re-classify devices (e.g., after improving prompt):

1. Update `CLASSIFICATION_VERSION` in `src/classify.py`
2. Run `python src/classify.py` again
3. Only devices with old/missing version tags will be re-processed

### Error Handling

- **Failed classifications**: Device retains NULL values
- **Partial failure**: Committed in batches (data safe)
- **API errors**: Logged but don't stop entire process

## Monitoring

Check progress during long-running classification:

```bash
# View statistics of already classified devices
python src\classify.py --stats
```

Query database directly:

```python
import sqlite3
conn = sqlite3.connect('data/devices.db')

# Count classified devices
c.execute("SELECT COUNT(*) FROM devices WHERE imaging_modality IS NOT NULL")

# Distribution by modality
c.execute("SELECT imaging_modality, COUNT(*) FROM devices GROUP BY imaging_modality")
```

## Maintenance

### When to Re-classify

- New devices added (via `update.py`)
- Improved classification prompts
- Updated LLM model with better accuracy
- Changed classification schema

### Best Practices

1. **Test first**: Use `--limit 10` before full run
2. **Monitor initially**: Check first 20-30 results for accuracy
3. **Batch commits**: Use `--batch-size 20` for safety
4. **Backup data**: Classification is additive, but backup recommended

## Troubleshooting

### Classification too slow

- Use faster Ollama model (e.g., `llama3.2:latest` instead of `gpt-oss`)
- Reduce batch size to prevent memory issues
- Check Ollama server response time

### Inaccurate classifications

- Review `CLASSIFICATION_PROMPT` in `src/classify.py`
- Lower temperature for more consistency
- Use larger/better LLM model
- Add few-shot examples to prompt

### Memory issues

- Reduce `--batch-size` parameter
- Process in chunks using `--limit` and manual offset

### Database locked

- Stop all Streamlit instances
- Close any SQLite browser connections
- Retry classification
