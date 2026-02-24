# PII & SPI: Detection + Redaction System

A comprehensive python-based solution for detecting and redacting personally identifiable information and sensitive personal information from text documents, PDF's, and images using natural language processing and optical character recognition.

## Features

### Core Capabilities
- **Multi-Format Support**: process text files, PDFs (text-based and scanned), images, and CSV spreadsheets
- **Dual Interface**: user-friendly web application + scriptable command-line tools
- **Local Processing**: all operations run locally - no data sent to external servers
- **Privacy-First**: permanent redaction with automatic cleanup of temporary files

### Detection & Analysis
- **Named Entity Recognition (NER)**: advanced NLP using spaCy models for context-aware detection
- **Pattern Matching**: regex-based detection for structured data (emails, phone numbers, credit cards)
- **Custom Recognizers**: australian-specific entities (ABN, TFN, Medicare numbers)
- **Configurable Thresholds**: adjustable confidence scores to balance precision and recall
- **Multi-Language Support**: extensible language support via spaCy models
- **Long Text Processing**: intelligent chunking with overlap for documents of any size
- **OCR Integration**: tesseract OCR for scanned PDFs and images

### Redaction Options
- **Multiple Redaction Styles**:
  - **Fill**: solid color rectangles (black, custom colors)
  - **Blur**: gaussian blur effect for images
  - **Pixelate**: pixelation effect for images
- **Label-Based Replacement**:replace PII with entity type labels (e.g., `<PERSON>`, `<EMAIL>`)
- **Relationship-Aware Masking**: context-based labels (e.g., "John's email" → `<John's EMAIL_ADDRESS>`)
- **Anonymization Mode**: type-based anonymization with customizable operators
- **Character Customization**: configurable redaction characters (default: `*`)
- **Permanent Removal**: true redaction, not just visual masking

### Output & Reporting
- **Redacted Files**: generate clean, redacted versions of all file types
- **JSON Export**: structured detection results with entity types, positions, and confidence scores
- **Summary Reports**: statistical overview of detections by entity type
- **Command Logs**: detailed execution logs in web interface
- **Preview Capability**: in-app preview of redacted content before download
- **CSV Structure Preservation**: maintain headers, delimiters, and formatting

### Advanced Features
- **Batch Processing**: CLI tools for automated, large-scale operations
- **Header Row Handling**: smart CSV processing with optional header preservation
- **Custom Delimiters**: support for various CSV formats (comma, tab, semicolon, etc.)
- **Confidence Filtering**: minimum score thresholds to reduce false positives
- **Adjustable Parameters**: chunk size, overlap, language, and more
- **Error Handling**: robust exception handling with informative error messages

## Project Structure

```
pii-detection-redaction/
├── src/
│   ├── app.py                      # streamlit web application
│   ├── common/                     # shared utilities
│   │   ├── common.py               # presidio analyzer builders
│   │   └── __init__.py
│   ├── text_detector/              # text PII detection module
│   │   ├── analyzer.py             # analyzer engine setup
│   │   ├── chunker.py              # long text processing
│   │   ├── anonymize.py            # text anonymization
│   │   ├── formatter.py            # results formatting
│   │   ├── relationships.py        # context-aware masking
│   │   ├── cli.py                  # command-line interface
│   │   └── __main__.py
│   ├── pdf_redactor/               # PDF PII redaction module
│   │   ├── analyzer.py             # PDF text extraction & analysis
│   │   ├── redactor.py             # PDF redaction engine
│   │   ├── cli.py                  # command-line interface
│   │   └── __init__.py
│   ├── image_redactor/             # image PII redaction module
│   │   ├── analyzer.py             # image analysis
│   │   ├── redactor.py             # image redaction engine
│   │   ├── types.py                # data classes
│   │   └── __init__.py
│   ├── csv_redactor/               # CSV PII redaction module
│   │   ├── analyzer.py             # analyzer engine setup
│   │   ├── redactor.py             # CSV redaction engine
│   │   ├── formatter.py            # results formatting
│   │   ├── cli.py                  # command-line interface
│   │   └── __main__.py
│   └── entity_mapping/             # australia-specific entities
│       ├── au_recognizers.py       # custom recognizers
│       ├── entity_config.py        # severity & color mappings
│       └── __init__.py
├── styles/
│   └── theme.css                   # web app styling
├── requirements.txt                # python dependencies
└── README.md                       # this file
```

## Architecture & Flow Diagrams

### System Architecture Overview

```mermaid
graph TB
    subgraph "User Interfaces"
        WebUI[Web Interface<br/>Streamlit App]
        CLI[Command Line<br/>Interface]
    end

    subgraph "Processing Modules"
        TextMod[Text Detector<br/>Plain Text Processing]
        PDFMod[PDF Redactor<br/>Document Processing]
        ImgMod[Image Redactor<br/>OCR + Redaction]
        CSVMod[CSV Redactor<br/>Structured Data]
    end

    subgraph "Core Engine"
        Common[Common Utilities<br/>Analyzer Builder]
        Presidio[Microsoft Presidio<br/>PII Detection Engine]
        SpaCy[spaCy NLP<br/>Named Entity Recognition]
        CustomRec[Custom Recognizers<br/>AU Entities]
    end

    subgraph "External Tools"
        PDFLib[pdfminer.six<br/>pikepdf]
        OCR[Tesseract OCR<br/>pytesseract]
        ImgLib[Pillow<br/>Image Processing]
    end

    subgraph "Output"
        RedactedFiles[Redacted Files<br/>TXT, PDF, Images, CSV]
        JSONOutput[Detection Reports<br/>JSON Format]
        Summary[Summary Statistics<br/>Entity Counts]
    end

    WebUI --> TextMod
    WebUI --> PDFMod
    WebUI --> ImgMod
    WebUI --> CSVMod

    CLI --> TextMod
    CLI --> PDFMod
    CLI --> ImgMod
    CLI --> CSVMod

    TextMod --> Common
    PDFMod --> Common
    ImgMod --> Common
    CSVMod --> Common

    Common --> Presidio
    Common --> SpaCy
    Common --> CustomRec

    PDFMod --> PDFLib
    ImgMod --> OCR
    ImgMod --> ImgLib

    TextMod --> RedactedFiles
    PDFMod --> RedactedFiles
    ImgMod --> RedactedFiles
    CSVMod --> RedactedFiles

    TextMod --> JSONOutput
    CSVMod --> JSONOutput

    TextMod --> Summary
    CSVMod --> Summary

    style Common fill:#e1f5ff
    style Presidio fill:#c8e6c9
    style SpaCy fill:#c8e6c9
    style RedactedFiles fill:#fff9c4
```

### Web Application Flow

```mermaid
sequenceDiagram
    participant User
    participant Streamlit as app.py
    participant Common as common/common.py
    participant TextDetector as text_detector/*
    participant PDFRedactor as pdf_redactor/*
    participant ImageRedactor as image_redactor/*
    participant CSVRedactor as csv_redactor/*
    participant Session as Session State

    User->>Streamlit: Upload File / Paste Text
    Streamlit->>Streamlit: detectFileType()
    Streamlit->>Streamlit: buildCommand()
    Streamlit->>Streamlit: runModuleCommand()

    alt Text Processing
        Streamlit->>TextDetector: python -m text_detector
        TextDetector->>Common: buildPresidioAnalyzer()
        Common-->>TextDetector: AnalyzerEngine
        TextDetector->>TextDetector: analyzeLongText()
        TextDetector->>TextDetector: maskWithRelationships()
        TextDetector-->>Streamlit: Redacted Text
    else PDF Processing
        Streamlit->>PDFRedactor: python -m pdf_redactor.cli
        PDFRedactor->>Common: buildPresidioAnalyzer()
        Common-->>PDFRedactor: AnalyzerEngine
        PDFRedactor->>PDFRedactor: analyzePdfToBboxes()
        PDFRedactor->>PDFRedactor: writeRedactedPdf()
        PDFRedactor-->>Streamlit: Redacted PDF
    else Image Processing
        Streamlit->>ImageRedactor: python -m image_redactor
        ImageRedactor->>Common: buildPresidioAnalyzer()
        Common-->>ImageRedactor: AnalyzerEngine
        ImageRedactor->>ImageRedactor: OCR + Analysis
        ImageRedactor->>ImageRedactor: applyRedactionStyle()
        ImageRedactor-->>Streamlit: Redacted Image
    else CSV Processing
        Streamlit->>CSVRedactor: python -m csv_redactor
        CSVRedactor->>Common: buildPresidioAnalyzer()
        Common-->>CSVRedactor: AnalyzerEngine
        CSVRedactor->>CSVRedactor: analyzeCsvFile()
        CSVRedactor->>CSVRedactor: redactCsvFile()
        CSVRedactor-->>Streamlit: Redacted CSV
    end

    Streamlit->>Session: Store File Bytes & Name
    Streamlit->>Streamlit: displayCommandLogs()
    Streamlit->>Streamlit: renderDownloadAndPreview()
    Streamlit-->>User: Display Results & Download
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
    Presidio-->>Redactor: Entity Results

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

### CSV Redaction Module Flow

```mermaid
sequenceDiagram
    participant CLI as cli.py
    participant Analyzer as analyzer.py
    participant Common as common.py
    participant Redactor as redactor.py
    participant Formatter as formatter.py
    participant Presidio as Presidio Engine
    participant CSV as csv module

    CLI->>CLI: parseArgs()
    CLI->>CLI: Validate Input Parameters

    CLI->>Analyzer: buildAnalyzer(language)
    Analyzer->>Common: buildPresidioAnalyzer()
    Common-->>Analyzer: AnalyzerEngine

    alt Analysis Only Mode
        CLI->>Redactor: analyzeCsvFile(path, analyzer)
    else Redaction Mode
        CLI->>Redactor: redactCsvFile(path, analyzer, outPath)
    end

    Redactor->>CSV: Read CSV File
    CSV-->>Redactor: Rows Iterator

    Redactor->>Redactor: Detect Header Row

    loop For Each Row
        loop For Each Cell
            Redactor->>Presidio: analyze(cell_text)
            Presidio-->>Redactor: RecognizerResults

            alt Score >= Threshold
                Redactor->>Redactor: Store Detection

                alt Redaction Mode
                    Redactor->>Redactor: Apply Redaction
                    Note over Redactor: Character Masking or<br/>Label Replacement
                end
            end
        end
    end

    alt JSON Output Requested
        CLI->>Formatter: resultsToJson(detections)
        Formatter-->>CLI: JSON String
        CLI->>CLI: Write JSON File
    end

    alt Summary Requested
        CLI->>Formatter: summarizeDetections(results)
        Formatter-->>CLI: Summary Statistics
        CLI->>CLI: Print Summary
    end

    alt Redaction Mode
        Redactor->>CSV: Write Redacted CSV
        CSV-->>Redactor: Success
        Redactor-->>CLI: Output File Path
    end
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
        TextAnalyzer[text_detector/analyzer.py]
        TextCLI[text_detector/cli.py]
    end

    subgraph "PDF Redaction"
        PDFAnalyzer[pdf_redactor/analyzer.py]
        PDFCLI[pdf_redactor/cli.py]
    end

    subgraph "Image Redaction"
        ImageAnalyzer[image_redactor/analyzer.py]
        ImageRedactor[image_redactor/redactor.py]
    end

    subgraph "CSV Redaction"
        CSVAnalyzer[csv_redactor/analyzer.py]
        CSVCLI[csv_redactor/cli.py]
        CSVRedactor[csv_redactor/redactor.py]
    end

    subgraph "Web Application"
        App[app.py]
    end

    subgraph "External Libraries"
        Spacy[spaCy NLP]
        Presidio[Presidio Analyzer]
    end

    subgraph "Custom Extensions"
        AURecog[entity_mapping/au_recognizers.py]
        EntityConfig[entity_mapping/entity_config.py]
    end

    TextAnalyzer --> Common
    PDFAnalyzer --> Common
    ImageAnalyzer --> Common
    CSVAnalyzer --> Common

    Common --> PickModel
    Common --> BuildAnalyzer

    BuildAnalyzer --> Spacy
    BuildAnalyzer --> Presidio
    BuildAnalyzer --> AURecog

    App --> TextCLI
    App --> PDFCLI
    App --> ImageAnalyzer
    App --> CSVCLI

    TextCLI --> TextAnalyzer
    PDFCLI --> PDFAnalyzer
    ImageAnalyzer --> ImageRedactor
    CSVCLI --> CSVAnalyzer
    CSVCLI --> CSVRedactor

    EntityConfig -.-> App

    style Common fill:#e1f5ff
    style BuildAnalyzer fill:#b3e5fc
    style PickModel fill:#b3e5fc
    style AURecog fill:#ffccbc
```

### Text Chunking Strategy

```mermaid
graph TB
    Start[Long Text Document<br/>100,000 characters] --> ChunkEval{Text Length > Chunk Size?}

    ChunkEval -->|No| Direct[Direct Analysis<br/>Single Pass]
    ChunkEval -->|Yes| ChunkSplit[Split into Chunks<br/>Size: 5000 chars<br/>Overlap: 300 chars]

    Direct --> Analyze1[Presidio Analysis]

    ChunkSplit --> Chunk1[Chunk 1: 0-5000]
    ChunkSplit --> Chunk2[Chunk 2: 4700-9700<br/>Overlap: 300]
    ChunkSplit --> Chunk3[Chunk 3: 9400-14400<br/>Overlap: 300]
    ChunkSplit --> ChunkN[Chunk N: ...<br/>Continue until end]

    Chunk1 --> A1[Analyze Chunk 1]
    Chunk2 --> A2[Analyze Chunk 2]
    Chunk3 --> A3[Analyze Chunk 3]
    ChunkN --> AN[Analyze Chunk N]

    A1 --> Merge[Merge Results<br/>Handle Overlaps]
    A2 --> Merge
    A3 --> Merge
    AN --> Merge

    Analyze1 --> Output[RecognizerResults]

    Merge --> Dedup[Deduplication<br/>Remove Overlapping Entities]
    Dedup --> Adjust[Adjust Offsets<br/>Map To Original Text]
    Adjust --> Output

    style ChunkSplit fill:#fff9c4
    style Merge fill:#c8e6c9
    style Output fill:#e1f5ff
```

### Deployment & Usage Workflow

```mermaid
graph LR
    subgraph "Setup Phase"
        Install[Install Dependencies<br/>pip install -r requirements.txt] --> Model[Download spaCy Model<br/>python -m spacy download]
        Model --> OCRSetup[Install Tesseract<br/>brew install tesseract]
    end

    subgraph "Usage Options"
        OCRSetup --> Choice{Choose Interface}

        Choice -->|Interactive| Web[Launch Web App<br/>streamlit run src/app.py]
        Choice -->|Automation| CLI[Use CLI Tools<br/>python -m module]
    end

    subgraph "Web Application Workflow"
        Web --> Upload[Upload/Paste Content]
        Upload --> Configure[Set Parameters<br/>Chunk Size, Threshold, etc.]
        Configure --> Process[Process & Redact]
        Process --> Preview[Preview Results]
        Preview --> Download[Download Redacted File]
    end

    subgraph "CLI Workflow"
        CLI --> SelectMod{Select Module}

        SelectMod -->|Text| TextCLI[text_detector]
        SelectMod -->|PDF| PDFCLI[pdf_redactor]
        SelectMod -->|Image| ImgCLI[image_redactor]
        SelectMod -->|CSV| CSVCLI[csv_redactor]

        TextCLI --> Batch[Batch Processing<br/>Scripts & Automation]
        PDFCLI --> Batch
        ImgCLI --> Batch
        CSVCLI --> Batch
    end

    Download --> Done[Secure Document<br/>Ready for Sharing]
    Batch --> Done

    style Web fill:#c8e6c9
    style Done fill:#fff9c4
    style Batch fill:#e1f5ff
```

### Data Privacy & Security Flow

```mermaid
graph TB
    Input[Input Document<br/>Contains PII] --> LocalCheck{Processing Location}

    LocalCheck -->|✓ Local Machine| LocalProc[Local Processing<br/>No External Servers]
    LocalCheck -->|✗ External API| Reject[❌ Not Supported<br/>Privacy First Design]

    LocalProc --> TempFiles[Temporary Files<br/>Created During Processing]

    TempFiles --> Process[PII Detection<br/>& Redaction]

    Process --> Original[Original File<br/>Remains Unchanged]
    Process --> Redacted[Redacted Copy<br/>Created]

    Redacted --> Permanent{Redaction Type}

    Permanent -->|Text/CSV| CharReplace[Character Replacement<br/>Original Text Lost]
    Permanent -->|PDF| BlackBox[Black Overlay<br/>Text Removed from Layer]
    Permanent -->|Image| PixelMod[Pixel Modification<br/>Original Pixels Lost]

    CharReplace --> Cleanup[Temporary File Cleanup<br/>Auto-Deletion]
    BlackBox --> Cleanup
    PixelMod --> Cleanup

    Cleanup --> SecureOutput[✓ Secure Redacted File<br/>Safe For Distribution]
    Original --> Archive[Original Archived<br/>Securely]

    style LocalProc fill:#c8e6c9
    style Reject fill:#ffccbc
    style SecureOutput fill:#fff9c4
    style Archive fill:#e1f5ff
```

## Technology Stack

- **Microsoft Presidio**: PII detection and anonymization framework
- **spaCy**: advanced NLP and named entity recognition
- **Stream-Lit**: modern web application framework
- **pdfminer.six**: PDF text extraction
- **pikepdf**: PDF manipulation and editing
- **pytesseract**: OCR for scanned documents
- **pillow**: image processing

## Requirements

see [requirements.txt](requirements.txt) for complete list.