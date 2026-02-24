# Quick Start Guide

## Installation (3 Steps)

### 1. Install Dependencies

```bash
# clone or download the repository
cd pii-detection-redaction

# install Python packages
pip install -r requirements.txt
```

### 2. Install spaCy Model

```bash
# install the language model (choose one)
python -m spacy download en_core_web_lg   # better accuracy, larger size
# OR
python -m spacy download en_core_web_sm   # faster, smaller size
```

### 3. Install Tesseract (For PDFs & Images)

```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows - Download from:
# https://github.com/UB-Mannheim/tesseract/wiki
```

---

## Usage

### Option 1: Web Interface (Easiest)

**Launch The App:**
```bash
streamlit run src/app.py
```

**Then:**
1. Open Browser To `http://localhost:8501`
2. Choose A Tab (Text, PDF, Image, Or CSV)
3. Upload File or Paste Text
4. Click "Process"
5. Download Redacted File

---

### Option 2: Command Line (Scripting)

#### Text Files

**Redact A Text File:**
```bash
python -m text_detector --in input.txt --mask-to-file output.txt
```

**Analyze Text Directly:**
```bash
python -m text_detector --text "Email: john@example.com, Phone: 555-1234"
```

**With Relationship-Aware Masking:**
```bash
# input: "john's email is john@example.com"
# output: "john's email is <John's EMAIL_ADDRESS>"
python -m text_detector --in input.txt --mask-to-file output.txt
```

---

#### PDF Files

**Redact A PDF:**
```bash
python -m pdf_redactor.cli --in document.pdf --out redacted.pdf
```

**With Higher Confidence Threshold:**
```bash
python -m pdf_redactor.cli --in document.pdf --out redacted.pdf --min-score 0.7
```

---

#### Images

**Redact An Image (Fill Mode):**
```bash
python -m image_redactor.analyzer --in photo.jpg --out redacted.jpg
```

**With Blur Effect:**
```bash
python -m image_redactor.analyzer --in photo.jpg --out redacted.jpg --mode blur
```

**With Pixelation:**
```bash
python -m image_redactor.analyzer --in photo.jpg --out redacted.jpg --mode pixelate
```

---

#### CSV Files

**Analyze Only (No Redaction):**
```bash
python -m csv_redactor --in data.csv --summary
```

**Redact With Character masking:**
```bash
python -m csv_redactor --in data.csv --out redacted.csv
```

**Redact With Labels:**
```bash
# "john@example.com" becomes "<EMAIL_ADDRESS>"
python -m csv_redactor --in data.csv --out redacted.csv --use-labels
```

**Export Detection Results To JSON:**
```bash
python -m csv_redactor --in data.csv --json-output results.json --summary
```

---

## Common Options

### For All Modules

| Option | Description | Example |
|--------|-------------|---------|
| `--min-score` | minimum confidence (0.0-1.0) | `--min-score 0.5` |
| `--lang` | language code | `--lang en` |
| `--help` | show all options | `--help` |

### Text Detector Specific

| Option | Description | Default |
|--------|-------------|---------|
| `--size` | chunk size in characters | 5000 |
| `--overlap` | overlap between chunks | 300 |
| `--anonymize` | use anonymization mode | False |
| `--print-text` | show input preview | False |

### CSV Redactor Specific

| Option | Description | Default |
|--------|-------------|---------|
| `--delimiter` | CSV delimiter | `,` |
| `--use-labels` | use entity labels | False |
| `--redaction-char` | masking character | `*` |
| `--no-skip-header` | process header row | False |

### Image Redactor Specific

| Option | Description | Default |
|--------|-------------|---------|
| `--mode` | fill/blur/pixelate | fill |
| `--fill-color` | fill color (hex) | #000000 |
| `--blur-radius` | blur strength | 8 |

---

## What Gets Detected?

### Personal Information
- ✅ Names (PERSON)
- ✅ Email Addresses
- ✅ Phone Numbers
- ✅ Physical Addresses
- ✅ URLs

### Financial Data
- ✅ Credit Card Numbers
- ✅ Bank Account Numbers
- ✅ IBAN Codes
- ✅ Australian ABN, BSB

### Government IDs
- ✅ Social Security Numbers (SSN)
- ✅ Australian TFN (Tax File Number)
- ✅ Australian Medicare Numbers
- ✅ Australian Passport Numbers
- ✅ Driver License Numbers

### ++
see the [main README](README.md#entity-types-detected) for complete list.