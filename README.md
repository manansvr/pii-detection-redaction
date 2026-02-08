# PII & SPI: Detection + Redaction System

A comprehensive python-based solution for detecting and redacting PII and SPI from text documents, PDF's, and images.

## Project Scope

This system helps organizations protect sensitive information by automatically detecting and redacting PII/SPI such as names, email addresses, phone numbers, financial information, and more. The system designed for secure document sharing, compliance requirements, and data privacy protection.

## Features

### Multi-Format Support
- **Text Files**: process plain text documents (.txt)
- **PDF Documents**: handle both text-based and scanned PDF's using OCR
- **Images**: detect and redact PII from image files

### Dual Interface
- **Web Application**: user-friendly stream-lit interface for interactive processing
- **Command-Line Tools**: scriptable CLI for batch processing and automation

### Entity Types Detected
- Personal Names (PERSON)
- Email Addresses
- Phone Numbers
- URL's
- Credit Card Numbers
- Social Security Numbers
- Bank Account Numbers
- Australian Business Numbers (ABN)
- Custom Pattern Recognition

## Installation

### Prerequisites
- Python 3.8
- Tesseract OCR (Scanned PDF's): `brew install tesseract` on macOS

### Setup

1. **clone the repository**
```bash
git clone <repository-url>
cd pii-detection-redaction
```

2. **install dependencies**
```bash
pip install -r requirements.txt
```

3. **download spaCy language model**
```bash
python -m spacy download en_core_web_sm

# or

python -m spacy download en_core_web_lg
```

## Usage

### Web Application

```bash
streamlit run src/app.py
```

then open your browser to `http://localhost:8501`

**Features:**
- upload or paste text for analysis
- upload PDF files for redaction
- adjust detection parameters (chunk size, overlap, confidence threshold)
- preview and download redacted files
- view command execution logs

### Command-Line Interface

#### Text Detection

**basic usage:**
```bash
python -m textDetector --text "contact manan rathi at manan.rathi@example.com"
```

**from file:**
```bash
python -m textDetector --in input.txt --mask-to-file output.txt
```

**advanced options:**
```bash
python -m textDetector \
  --in input.txt \
  --size 4000 \
  --overlap 300 \
  --min-score 0.3 \
  --mask-to-file redacted.txt \
  --print-text
```

#### PDF Redaction

```bash
python -m pdfRedactor.cli --in document.pdf --out redacted.pdf
```

#### Image Redaction

```bash
python -m imageRedactor.analyzer --input image.jpg --output redacted.jpg
```

## 📁 Project Structure

```
pii-detection-redaction/
├── src/
│   ├── app.py                      # streamlit web application
│   ├── common/                     # shared utilities
│   │   ├── common.py               # presidio analyzer builders
│   │   └── __init__.py
│   ├── textDetector/               # text PII detection module
│   │   ├── analyzer.py             # analyzer engine setup
│   │   ├── chunker.py              # long text processing
│   │   ├── anonymize.py            # text anonymization
│   │   ├── formatter.py            # results formatting
│   │   ├── relationships.py        # context-aware masking
│   │   ├── cli.py                  # command-line interface
│   │   └── __main__.py
│   ├── pdfRedactor/                # PDF PII redaction module
│   │   ├── analyzer.py             # PDF text extraction & analysis
│   │   ├── redactor.py             # PDF redaction engine
│   │   ├── cli.py                  # command-line interface
│   │   └── __init__.py
│   └── imageRedactor/              # image PII redaction module
│       ├── analyzer.py             # image analysis
│       ├── redactor.py             # image redaction engine
│       ├── types.py                # data classes
│       └── __init__.py
├── styles/
│   └── theme.css                   # web app styling
├── requirements.txt                # python dependencies
└── README.md                       # this file
```

## Architecture & Flow Diagrams

### Web Application Flow

```mermaid
sequenceDiagram
    participant User
    participant Streamlit as app.py
    participant Common as common/common.py
    participant TextDetector as textDetector/*
    participant PDFRedactor as pdfRedactor/*
    participant Session as Session State

    User->>Streamlit: Upload File / Paste Text
    Streamlit->>Streamlit: processFile()
    Streamlit->>Streamlit: buildCommand()
    Streamlit->>Streamlit: runModuleCommand()

    alt Text Processing
        Streamlit->>TextDetector: python -m textDetector
        TextDetector->>Common: buildPresidioAnalyzer()
        Common-->>TextDetector: AnalyzerEngine
        TextDetector->>TextDetector: analyzeLongText()
        TextDetector->>TextDetector: maskWithRelationships()
        TextDetector-->>Streamlit: Redacted File
    else PDF Processing
        Streamlit->>PDFRedactor: python -m pdfRedactor.cli
        PDFRedactor->>Common: buildPresidioAnalyzer()
        Common-->>PDFRedactor: AnalyzerEngine
        PDFRedactor->>PDFRedactor: analyzePdfToBboxes()
        PDFRedactor->>PDFRedactor: writeRedactedPdf()
        PDFRedactor-->>Streamlit: Redacted PDF
    end

    Streamlit->>Session: Store file Bytes & Name
    Streamlit->>Streamlit: displayCommandLogs()
    Streamlit->>Streamlit: renderDownloadAndPreview()
    Streamlit-->>User: Display Results & Preview
```

### Text Detection Module Flow

```mermaid
sequenceDiagram
    participant CLI as cli.py
    participant Analyzer as analyzer.py
    participant Common as common.py
    participant Chunker as chunker.py
    participant Relationships as relationships.py
    participant Anonymize as anonymize.py
    participant Presidio as Presidio Engine
    participant Spacy as spaCy NLP

    CLI->>CLI: parseArgs()
    CLI->>CLI: readInputText()

    CLI->>Analyzer: buildAnalyzer(language)
    Analyzer->>Common: buildPresidioAnalyzer()
    Common->>Common: pickSpacyModel()
    Common->>Spacy: Load Model
    Spacy-->>Common: NLP Model
    Common->>Presidio: Create AnalyzerEngine
    Presidio-->>Analyzer: AnalyzerEngine

    CLI->>Chunker: analyzeLongText(text, size, overlap)
    loop For Each Chunk
        Chunker->>Presidio: analyze(chunk)
        Presidio->>Spacy: NLP Processing
        Spacy-->>Presidio: Entities
        Presidio-->>Chunker: RecognizerResults
    end
    Chunker->>Chunker: Merge Overlapping Results
    Chunker-->>CLI: All Results

    alt Anonymize Mode
        CLI->>Anonymize: anonymizeText(text, results)
        Anonymize-->>CLI: Type-Based Anonymization
    else Relationship Masking
        CLI->>Relationships: maskWithRelationships(text, results)
        Relationships->>Relationships: assignRelationships()
        Relationships-->>CLI: Context-Aware Masked Text
    end

    CLI-->>CLI: Write Output File
```

### PDF Redaction Module Flow

```mermaid
sequenceDiagram
    participant CLI as cli.py
    participant Analyzer as analyzer.py
    participant Common as common.py
    participant Redactor as redactor.py
    participant PDFMiner as pdfminer.six
    participant Presidio as Presidio Engine
    participant Pikepdf as pikepdf

    CLI->>CLI: parseArgs()

    CLI->>Analyzer: buildAnalyzer()
    Analyzer->>Common: buildPresidioAnalyzer()
    Common-->>Analyzer: AnalyzerEngine

    CLI->>Analyzer: analyzePdfToBboxes(pdfPath)

    loop For Each Page
        Analyzer->>PDFMiner: extract_pages()
        PDFMiner-->>Analyzer: Page Layout

        loop For Each Text Container
            Analyzer->>Analyzer: Extract Characters & Positions
            Analyzer->>Presidio: analyze(text)
            Presidio-->>Analyzer: Entity Results
            Analyzer->>Analyzer: Map Entities To Bounding Boxes
        end

        Analyzer-->>Analyzer: Page Bounding Boxes
    end

    Analyzer-->>CLI: All Pages With bboxes

    CLI->>Redactor: writeRedactedPdf(srcPdf, dstPdf, bboxes)
    Redactor->>Pikepdf: Open Source PDF

    loop For Each Page With Entities
        Redactor->>Redactor: Build Redaction Rectangles
        Redactor->>Redactor: Generate Overlay Stream
        Redactor->>Pikepdf: Add Redaction Layer
    end

    Redactor->>Pikepdf: Save Redacted PDF
    Pikepdf-->>Redactor: Success
    Redactor-->>CLI: Output File Path
```

### Image Redaction Module Flow

```mermaid
sequenceDiagram
    participant CLI as analyzer.py
    participant Redactor as redactor.py
    participant Common as common.py
    participant Presidio as Presidio Engine
    participant ImageRedactor as presidio_image_redactor
    participant Tesseract as pytesseract OCR
    participant PIL as Pillow

    CLI->>CLI: Parse Arguments
    CLI->>CLI: hexToRgb() For Colors

    CLI->>Common: buildPresidioAnalyzer()
    Common-->>CLI: AnalyzerEngine

    CLI->>Redactor: ImageRedactor(analyzer, ocrLanguages)

    CLI->>Redactor: redactFile(inputPath, outputPath)
    Redactor->>PIL: Open Image
    PIL-->>Redactor: Image Object

    Redactor->>Tesseract: Extract Text & Positions
    Tesseract-->>Redactor: OCR Results (bboxes)

    Redactor->>Presidio: Analyze(Extracted Text)
    Presidio-->>Redactor: Entity Eesults

    Redactor->>Redactor: Map Entities To Image Coordinates
    Redactor->>ImageRedactor: Apply Redaction Style

    alt Fill Style
        ImageRedactor->>PIL: Draw Filled Rectangles
    else Blur Style
        ImageRedactor->>PIL: Apply Blur Filter
    else Pixelate Style
        ImageRedactor->>PIL: Pixelate Regions
    end

    Redactor->>PIL: Save Redacted Image
    PIL-->>Redactor: Success
    Redactor-->>CLI: Output File Path
```

### Common Module Interaction

```mermaid
graph TB
    subgraph "Common Module"
        Common[common.py]
        PickModel[pickSpacyModel]
        BuildAnalyzer[buildPresidioAnalyzer]
    end

    subgraph "Text Detection"
        TextAnalyzer[textDetector/analyzer.py]
        TextCLI[textDetector/cli.py]
    end

    subgraph "PDF Redaction"
        PDFAnalyzer[pdfRedactor/analyzer.py]
        PDFCLI[pdfRedactor/cli.py]
    end

    subgraph "Image Redaction"
        ImageAnalyzer[imageRedactor/analyzer.py]
        ImageRedactor[imageRedactor/redactor.py]
    end

    subgraph "Web Application"
        App[app.py]
    end

    subgraph "External Libraries"
        Spacy[spaCy NLP]
        Presidio[Presidio Analyzer]
    end

    TextAnalyzer --> Common
    PDFAnalyzer --> Common
    ImageAnalyzer --> Common

    Common --> PickModel
    Common --> BuildAnalyzer

    BuildAnalyzer --> Spacy
    BuildAnalyzer --> Presidio

    App --> TextCLI
    App --> PDFCLI
    App --> ImageAnalyzer

    TextCLI --> TextAnalyzer
    PDFCLI --> PDFAnalyzer
    ImageAnalyzer --> ImageRedactor

    style Common fill:#e1f5ff
    style BuildAnalyzer fill:#b3e5fc
    style PickModel fill:#b3e5fc
```

## Configuration

### Text Detection Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--size` | chunk size in characters | 5000 |
| `--overlap` | over lap between chunks | 300 |
| `--min-score` | minimum confidence threshold | 0.0 |
| `--lang` | language code | en |
| `--print-text` | echo input preview | False |
| `--anonymize` | enable anonymization mode | False |

### Detection Confidence Levels

- **1.0**: exact pattern matches (emails, URLs)
- **0.85+**: high confidence (names with context)
- **0.5-0.85**: medium confidence
- **<0.5**: low confidence (may include false positives)

## Examples

### Example 1: Basic Text Redaction

**Input:**
```
contact jane smith at jane.smith@company.com or call (555) 123-4567
```

**Output:**
```
contact <PERSON_1> at <EMAIL_ADDRESS_1> or call <PHONE_NUMBER_1>
```

### Example 2: Relationship-Aware Masking

**Input:**
```
john's email is john@example.com
sarah's phone is 555-1234
```

**Output:**
```
john's email is <John's EMAIL_ADDRESS>
sarah's phone is <Sarah's PHONE_NUMBER>
```

### Example 3: PDF with Multiple Pages

```bash
python -m pdfRedactor.cli --in contract.pdf --out contract_redacted.pdf
```

creates a new PDF with all detected PII regions permanently redacted with black boxes.

## Technology Stack

- **Microsoft Presidio**: PII detection and anonymization framework
- **spaCy**: advanced NLP and named entity recognition
- **Stream Lit**: modern web application framework
- **pdfminer.six**: PDF text extraction
- **pikepdf**: PDF manipulation and editing
- **pytesseract**: OCR for scanned documents
- **Pillow**: image processing

## Requirements

see [requirements.txt](requirements.txt) for complete list:

```txt
streamlit>=1.20.0
streamlit-pdf-viewer>=0.0.15
presidio-analyzer>=2.2.0
presidio-anonymizer>=2.2.0
presidio-image-redactor>=0.0.50
spacy>=3.5.0
pdfminer.six>=20221105
pikepdf>=8.0.0
Pillow>=10.0.0
pytesseract>=0.3.10
```

## Privacy & Security

- all processing happens locally: no data is sent to external servers
- redacted files are generated with permanent removal (not just visual masking)
- original files remain unchanged
- temporary files are automatically cleaned up

## Limitations

- spaCy model accuracy varies by entity type and context
- scanned PDF processing requires Tesseract OCR installation
- very large files may require increased memory
- some context-dependent PII may be missed (requires human review)

**Note**: this tool aids in PII detection but should not be solely relied upon for compliance. always review redacted documents manually for sensitive use cases.
