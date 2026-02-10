# src/app.py

import os
import sys
import io
import shutil
import subprocess
import tempfile
import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

try:
    from streamlit_pdf_viewer import pdf_viewer
    HAS_PDF_VIEWER = True
except Exception:
    HAS_PDF_VIEWER = False


# -------------------------------------------------------------------
# paths and environment
# -------------------------------------------------------------------
repoRoot = Path(__file__).resolve().parent.parent
srcDir = repoRoot / "src"
stylesDir = repoRoot / "styles"
themeCss = stylesDir / "theme.css"

# ensure python can import src/* packages if needed
if str(srcDir) not in sys.path:
    sys.path.insert(0, str(srcDir))


# -------------------------------------------------------------------
# page config
# -------------------------------------------------------------------
st.set_page_config(
    page_title="PII & SPI Redactor",
    page_icon="🛡️",
    layout="centered"
)


# -------------------------------------------------------------------
# load external css
# -------------------------------------------------------------------
def injectLocalCss(cssPath: Path):
    if cssPath.exists():
        css = cssPath.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


injectLocalCss(themeCss)


# -------------------------------------------------------------------
# header / logo
# -------------------------------------------------------------------
imagesDir = repoRoot / "images"
topLogoPath = imagesDir / "images.png"

if topLogoPath.exists():
    left, center, right = st.columns([1, 4, 1])
    with center:
        st.image(str(topLogoPath), use_container_width=True)


st.title("🛡️ PII & SPI Redactor")
st.caption("PII - Personally Identifiable Information; SPI - Sensitive Personal Information")
st.caption(
    "The PII and SPI include data that can directly or indirectly identify an individual, "
    "such as names, contact details, identifiers, financial data, or health information."
)
st.caption(
    "The exposure of this data can lead to privacy breaches, identity theft, fraud, "
    "or other forms of misuse."
)
st.caption(
    "The detection and redaction of this information is essential for protecting "
    "individual privacy and reducing security and compliance risks."
)
st.caption(
    "The redaction allows organizations to safely share, store, and analyze data while "
    "preventing unnecessary exposure of confidential information."
)


# -------------------------------------------------------------------
# helpers
# -------------------------------------------------------------------
def runModuleCommand(cmdArgs, cwd=None):
    """
    this runs a python module command using the current interpreter.
    also ensures pythonpath includes ./src so `-m textdetector` and
    `-m pdfredactor.cli` work.

    returns (returncode, stdout, stderr)
    """
    env = os.environ.copy()
    pyPath = str(srcDir)
    env["PYTHONPATH"] = pyPath + os.pathsep + env.get("PYTHONPATH", "")

    # use current interpreter for consistency
    fullCmd = [sys.executable] + cmdArgs
    proc = subprocess.run(
        fullCmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True
    )

    return proc.returncode, proc.stdout, proc.stderr


def makeSafeFilename(name: str) -> str:
    bad = '<>:"/\\|?*'
    for ch in bad:
        name = name.replace(ch, "_")
    return name


def displayCommandLogs(logPlaceholder, cmd, out, err=None):
    """
    displays command execution logs in a consistent format.
    """
    with logPlaceholder.container():
        st.markdown("### Command Executed:")
        st.code(" ".join([sys.executable] + cmd), language="bash")

        if out:
            st.markdown("### Output:")
            st.code(out)

        if err:
            st.markdown("### Error:")
            st.code(err)


def processFile(fileType, inputFile, inputText, workDir, cmdBuilder, outputProcessor):
    """
    generic file processing workflow for text, pdf, and image files.

    args:
        filetype: "text", "pdf", or "image"
        inputfile: uploaded file object or none
        inputtext: pasted text string or none (text mode only)
        workdir: path to temporary working directory
        cmdbuilder: function(inpath, workdir) -> (cmd_list, outpath)
        outputprocessor: function(outpath) -> none (stores result in session_state)

    returns:
        (returncode, stdout, stderr, outpath)
    """
    # prepare input path
    if inputFile:
        rawName = makeSafeFilename(Path(inputFile.name).stem)

        if fileType == "text":
            ext = ".txt"
        elif fileType == "pdf":
            ext = ".pdf"
        elif fileType == "image":
            # preserve original image extension
            ext = Path(inputFile.name).suffix or ".png"
        else:
            raise ValueError(f"FileType: {fileType}")

        inPath = workDir / f"{rawName}{ext}"
        inPath.write_bytes(inputFile.read())
    elif inputText and fileType == "text":
        inPath = workDir / "pasted_input.txt"
        inPath.write_text(inputText, encoding="utf-8")
    else:
        raise ValueError("No Input Provided")

    # build command and get output path
    cmd, outPath = cmdBuilder(inPath, workDir)

    # run command
    rc, out, err = runModuleCommand(cmd, cwd=workDir)

    # process output if successful
    if rc == 0 and outPath and outPath.exists():
        outputProcessor(outPath)

    return rc, out, err, outPath


# -------------------------------------------------------------------
# text preview + download
# -------------------------------------------------------------------
def renderDownloadAndPreview(fileType, bytesKey, nameKey, previewRenderer=None):
    """
    generic download + preview ui for text or pdf files.

    args:
        filetype: "text" or "pdf"
        byteskey: session_state key for file bytes
        namekey: session_state key for file name
        previewrenderer: optional function(filebytes, filename) to render custom preview
    """
    fileBytes = st.session_state.get(bytesKey)
    fileName = st.session_state.get(nameKey)

    if not fileBytes or not fileName:
        return

    # determine mime type and label
    if fileType == "text":
        mimeType = "text/plain"
        label = "⬇️ Download Redacted Text"
        previewLabel = "👁️ Show Redacted Text Preview"
    else:
        mimeType = "application/pdf"
        label = "⬇️ Download Redacted PDF"
        previewLabel = "👁️ Preview Redacted PDF"

    # download button
    st.download_button(
        label=label,
        data=fileBytes,
        file_name=fileName,
        mime=mimeType,
        key=f"dl_{fileType}_{fileName}",
        use_container_width=True,
    )

    # preview control
    if fileType == "text":
        # text uses persistent checkbox
        pvKey = f"show_{fileType}_preview::{fileName}"
        if pvKey not in st.session_state:
            st.session_state[pvKey] = False

        st.session_state[pvKey] = st.checkbox(
            previewLabel,
            value=st.session_state[pvKey],
            key=f"pv_{fileType}_toggle_{fileName}",
            help="Toggle To Show/Hide The Preview. This Will Persist Until You Process A New File.",
        )

        if st.session_state[pvKey]:
            st.markdown("### Preview")
            if previewRenderer:
                previewRenderer(fileBytes, fileName)
            else:
                # default text preview
                try:
                    previewText = fileBytes.decode("utf-8", errors="replace")
                except Exception:
                    previewText = ""

                st.text_area(
                    label="Redacted Text Preview",
                    value=previewText,
                    height=300,
                    label_visibility="collapsed",
                    key=f"txt_area_preview_{fileName}",
                )
    else:
        # pdf uses button
        if st.button(
            previewLabel,
            key=f"pv_{fileType}_{fileName}",
            use_container_width=True,
        ):
            st.session_state[f"show_{fileType}_preview"] = True

        if st.session_state.get(f"show_{fileType}_preview"):
            st.markdown("### Preview")
            if previewRenderer:
                previewRenderer(fileBytes, fileName)
            else:
                # default pdf preview
                if HAS_PDF_VIEWER:
                    pdf_viewer(fileBytes, width=900, height=800, key=f"pdfv_{fileName}")
                else:
                    b64Pdf = base64.b64encode(fileBytes).decode("utf-8")
                    iframehtml = f"""
                    <iframe
                        src="data:application/pdf;base64,{b64pdf}#toolbar=1&navpanes=0&statusbar=1"
                        width="100%"
                        height="800"
                        style="border:none;"
                    ></iframe>
                    """
                    components.html(iframeHtml, height=800, scrolling=True)


def renderTextActionsAndPreview():
    """renders download + preview controls for text output."""
    renderDownloadAndPreview("text", "last_text_bytes", "last_text_name")


def renderPdfActionsAndPreview():
    """renders download + preview controls for pdf output."""
    renderDownloadAndPreview("pdf", "last_pdf_bytes", "last_pdf_name")


def renderImageActionsAndPreview():
    """renders download + preview controls for image output."""
    imageBytes = st.session_state.get("last_image_bytes")
    imageName = st.session_state.get("last_image_name")

    if not imageBytes or not imageName:
        return

    # download button
    st.download_button(
        label="⬇️ Download Redacted Image",
        data=imageBytes,
        file_name=imageName,
        mime="image/png",
        key=f"dl_image_{imageName}",
        use_container_width=True,
    )

    # preview button
    if st.button(
        "👁️ Preview Redacted Image",
        key=f"pv_image_{imageName}",
        use_container_width=True,
    ):
        st.session_state["show_image_preview"] = True

    # render preview
    if st.session_state.get("show_image_preview"):
        st.markdown("### Preview")
        st.image(imageBytes, use_column_width=True, caption="Redacted Image")


tabText, tabPdf, tabImage = st.tabs(["Text (.txt)", "PDF (.pdf)", "Image (.jpg/.png)"])

# ============================
# == text tab ================
# ============================

with tabText:
    st.subheader("Text Detection & Redaction")
    st.caption(
        "The textRedactor module analyzes and redacts PII from plain text inputs."
    )
    st.caption(
        "The module supports strings, files, or structured text content, "
        "identifies sensitive entities using predefined and configurable recognizers, "
        "and replaces or masks them according to the configured redaction strategy."
    )
    st.caption(
        "This module is lightweight, fast, and ideal for logs, emails, transcripts, "
        "and other text-only data sources."
    )

    mode = st.radio(
        "Input Type",
        options=["Upload .txt File", "Paste Raw Text"],
        horizontal=True,
    )

    # most common options (must stay inside tabtext so it doesn't leak into pdf tab)
    with st.expander("Advanced Options"):
        size = st.number_input(
            "Chunk Size (--size)",
            min_value=100,
            max_value=10000,
            value=4000,
            step=100,
            help=(
                "Max Characters Per Chunk For Processing. Larger Chunks Mean Fewer Calls "
                "But Higher Memory; Smaller Chunks Improve Recall At Boundaries."
            ),
        )

        overlap = st.number_input(
            "Overlap (--overlap)",
            min_value=0,
            max_value=2000,
            value=300,
            step=50,
            help=(
                "How Many Characters To Overlap Between Adjacent Chunks. "
                "Helps Catch Entities Split Across Chunk Boundaries."
            ),
        )

        minScore = st.number_input(
            "Min Score (--min-score)",
            min_value=0.0,
            max_value=1.0,
            value=0.2,
            step=0.05,
            format="%.2f",
            help=(
                "Confidence Threshold (0–1). Entities Below This Score Are Ignored. "
                "Increase To Reduce False Positives; Decrease To Detect Weaker Matches."
            ),
        )

        printText = st.checkbox(
            "Print Matched Text To Logs (--print-text)",
            value=False,
            help=(
                "When Enabled, Matched Spans Are Printed To Stdout For Debugging/Audit. "
                "Useful For Verifying Detections During Testing."
            ),
        )

        redactToFile = st.checkbox(
            "Redact To A New File (mask-to-file)",
            value=True,
            help=(
                "Writes The Redacted Output To A New .txt File Instead Of Only "
                "Printing Results To Logs."
            ),
        )

        anonymizeText = st.checkbox(
            "Anonymize (Only When Using Raw Text Input)",
            value=False,
            help=(
                "When Pasting Raw Text (Not A File), Anonymize In-Memory And Preview "
                "Without Creating An Output File."
            ),
        )

    # inputs belong to the text tab as well
    inputText = None
    inputUpload = None

    if mode == "Upload .txt File":
        inputUpload = st.file_uploader(
            "Upload A .txt File",
            type=["txt"],
        )
    else:
        inputText = st.text_area(
            "Paste Your Text Here",
            height=200,
            placeholder="e.g., manans's email is manan.rathi@gmail.com",
        )

    processBtn = st.button(
        "Process Text",
        type="primary",
        use_container_width=True,
    )

    logPlaceholder = st.empty()

    # if we already have a previous output, show actions immediately
    renderTextActionsAndPreview()

    if processBtn:
        if not inputUpload and not inputText:
            st.error("Please Upload A .txt File Or Paste Some Text.")
        else:
            with st.spinner("Processing Text..."):
                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        tmpdir = Path(tmpdir)

                        def buildTextCommand(inPath, workDir):
                            cmd = [
                                "-m", "textDetector",
                                "--in", str(inPath),
                                "--size", str(size),
                                "--overlap", str(overlap),
                                "--min-score", str(minScore),
                            ]

                            if printText:
                                cmd.append("--print-text")

                            outPath = None
                            if redactToFile:
                                outName = f"{inPath.stem}_redacted.txt"
                                outPath = workDir / outName
                                cmd.extend(["--mask-to-file", outName])
                            elif inputText and anonymizeText:
                                cmd.append("--anonymize")

                            return cmd, outPath

                        def storeTextOutput(outPath):
                            st.session_state["last_text_bytes"] = outPath.read_bytes()
                            st.session_state["last_text_name"] = outPath.name

                        rc, out, err, outPath = processFile(
                            "text", inputUpload, inputText, tmpdir,
                            buildTextCommand, storeTextOutput
                        )

                        displayCommandLogs(logPlaceholder, 
                            buildTextCommand(tmpdir / "dummy.txt", tmpdir)[0], out)

                        if rc != 0:
                            st.error("TextDetector Reported An Error. See Logs Above.")
                        elif outPath and outPath.exists():
                            renderTextActionsAndPreview()
                        else:
                            st.info(
                                "No Output File Generated "
                                "(Likely Detect-Only/Anonymize Mode). "
                                "Check Log For Results."
                            )

                except Exception as e:
                    st.exception(e)

# ============================
# == pdf tab =================
# ============================

with tabPdf:
    st.subheader("PDF Redaction")
    st.caption(
        "The pdfRedactor module detects and redacts PII from PDF documents."
    )
    st.caption(
        "The module processes both text-based PDFs and scanned PDFs by extracting text "
        "(and applying OCR when needed), identifying sensitive entities such as names, "
        "emails, phone numbers, and financial details, and permanently removing or "
        "masking those regions before saving a sanitized PDF."
    )
    st.caption(
        "This module is designed for secure document sharing and compliance use cases."
    )

    pdfFile = st.file_uploader(
        "Input Type (Upload .pdf File)",
        type=["pdf"],
    )

    processPdfBtn = st.button(
        "Process PDF",
        type="primary",
        key="process_pdf",
        use_container_width=True,
    )

    logPlaceholderPdf = st.empty()

    # if we already have a previous output, show actions immediately
    renderPdfActionsAndPreview()

    if processPdfBtn:
        if not pdfFile:
            st.error("Please Upload A PDF File.")
        else:
            with st.spinner("Processing PDF... (OCR May Take Time For Scanned PDFs)"):
                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        tmpdir = Path(tmpdir)

                        def buildPdfCommand(inPath, workDir):
                            outPath = workDir / f"{inPath.stem}_redacted.pdf"
                            cmd = [
                                "-m", "pdfRedactor.cli",
                                "--in", str(inPath),
                                "--out", str(outPath),
                            ]
                            return cmd, outPath

                        def storePdfOutput(outPath):
                            st.session_state["last_pdf_bytes"] = outPath.read_bytes()
                            st.session_state["last_pdf_name"] = outPath.name

                        rc, out, err, outPath = processFile(
                            "pdf", pdfFile, None, tmpdir,
                            buildPdfCommand, storePdfOutput
                        )

                        displayCommandLogs(logPlaceholderPdf,
                            buildPdfCommand(tmpdir / "dummy.pdf", tmpdir)[0], out, err)

                        if rc != 0:
                            st.error("pdfRedactor Reported An Error. See Logs Above.")
                        elif outPath and outPath.exists():
                            renderPdfActionsAndPreview()
                        else:
                            st.info("No Output File Produced. See Logs Above.")

                except Exception as e:
                    st.exception(e)

# ============================
# == image tab ===============
# ============================

with tabImage:
    st.subheader("Image Redaction")
    st.caption(
        "The imageRedactor module detects and redacts PII from image files."
    )
    st.caption(
        "The module uses OCR (Optical Character Recognition) to extract text from images, "
        "identifies sensitive entities, and applies various redaction styles "
        "(fill, blur, pixelate) to hide the information."
    )
    st.caption(
        "This module is ideal for processing scanned documents, screenshots, "
        "photos with visible text, and other image-based content."
    )

    # redaction options
    with st.expander("Redaction Options"):
        redactionMode = st.selectbox(
            "Redaction Mode",
            options=["fill", "blur", "pixelate", "rectangle"],
            index=0,
            help="fill: solid color fill; blur: blur effect; pixelate: pixelated blocks; rectangle: outline only"
        )

        fillColor = st.color_picker(
            "Fill/Rectangle Color",
            value="#000000",
            help="Color For Fill & Rectangle Modes"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            blurRadius = st.number_input(
                "Blur Radius",
                min_value=1,
                max_value=50,
                value=8,
                help="Blur Strength (Blur Mode Only)"
            )

        with col2:
            pixelSize = st.number_input(
                "Pixel Size",
                min_value=1,
                max_value=50,
                value=12,
                help="Block Size (Pixelate Mode Only)"
            )

        with col3:
            padding = st.number_input(
                "Padding",
                min_value=0,
                max_value=20,
                value=2,
                help="Extra Padding Around Detected Regions"
            )

        drawLabels = st.checkbox(
            "Draw Entity Labels",
            value=False,
            help="Show Entity Type Labels On Redacted Regions"
        )

        ocrLang = st.text_input(
            "OCR Language(s)",
            value="eng",
            help="Language Codes For OCR"
        )

    imageFile = st.file_uploader(
        "Input Type (Upload Image File)",
        type=["jpg", "jpeg", "png", "bmp", "tiff"],
    )

    processImageBtn = st.button(
        "Process Image",
        type="primary",
        key="process_image",
        use_container_width=True,
    )

    logPlaceholderImage = st.empty()

    # if we already have a previous output, show actions immediately
    renderImageActionsAndPreview()

    if processImageBtn:
        if not imageFile:
            st.error("Please Upload An Image File.")
        else:
            with st.spinner("Processing Image... (OCR In Progress)"):
                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        tmpdir = Path(tmpdir)

                        def buildImageCommand(inPath, workDir):
                            # determine output format based on input
                            outExt = inPath.suffix if inPath.suffix else ".png"
                            outPath = workDir / f"{inPath.stem}_redacted{outExt}"

                            cmd = [
                                "-m", "imageRedactor.cli",
                                "--in", str(inPath),
                                "--out", str(outPath),
                                "--mode", redactionMode,
                                "--fill", fillColor,
                                "--blur-radius", str(blurRadius),
                                "--pixel-size", str(pixelSize),
                                "--padding", str(padding),
                                "--lang", ocrLang,
                            ]

                            if drawLabels:
                                cmd.append("--labels")

                            return cmd, outPath

                        def storeImageOutput(outPath):
                            st.session_state["last_image_bytes"] = outPath.read_bytes()
                            st.session_state["last_image_name"] = outPath.name

                        # process image file
                        rc, out, err, outPath = processFile(
                            "image", imageFile, None, tmpdir,
                            buildImageCommand, storeImageOutput
                        )

                        displayCommandLogs(logPlaceholderImage,
                            buildImageCommand(tmpdir / "dummy.jpg", tmpdir)[0], out, err)

                        if rc != 0:
                            st.error("imageRedactor Reported An Error. See Logs Above.")
                        elif outPath and outPath.exists():
                            renderImageActionsAndPreview()
                        else:
                            st.info("No Output File Produced. See Logs Above.")

                except Exception as e:
                    st.exception(e)