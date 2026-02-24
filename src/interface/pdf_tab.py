import tempfile
from pathlib import Path
import streamlit as st

from .helpers import process_file, display_command_logs, display_entity_info
from .components import render_pdf_actions_and_preview


def render_pdf_tab():
    st.subheader("PDF Redaction")
    st.caption(
        "The pdf_redactor module detects and redacts PII from PDF documents using "
        "centralized Australian entity recognizers."
    )
    st.caption(
        "This module processes both text-based and scanned PDFs by extracting text "
        "(applying OCR when needed), identifying sensitive entities including Australian "
        "government IDs (TFN, Medicare, ABN, Passport), financial data (BSB, accounts), "
        "and contact information, then permanently removing or masking those regions."
    )
    st.caption(
        "Designed for secure document sharing, regulatory compliance (Privacy Act 1988), "
        "and safe archival of sensitive documents."
    )

    with st.expander("🇦🇺 View Supported Entity Types"):
        display_entity_info()

    with st.expander("Advanced Options"):
        col1, col2 = st.columns(2)

        with col1:
            language = st.selectbox(
                "Language (--lang)",
                options=["en", "es", "fr", "de", "it", "pt"],
                index=0,
                format_func=lambda x: {
                    "en": "English",
                    "es": "Spanish",
                    "fr": "French",
                    "de": "German",
                    "it": "Italian",
                    "pt": "Portuguese"
                }[x],
                help="Language Code For PDF Text Extraction & Analysis"
            )
            
            min_score = st.number_input(
                "Min Confidence Score",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.05,
                format="%.2f",
                help="Minimum Confidence Threshold For Entity Detection (0-1)"
            )
        
        with col2:
            draw_labels = st.checkbox(
                "Draw Entity Labels (--no-labels inverted)",
                value=True,
                help="Draw white labels on redacted regions showing entity type"
            )
            
            label_prefix = st.text_input(
                "Label Prefix (--label-prefix)",
                value="",
                help="Optional prefix for entity labels (e.g., 'REDACTED:')"
            )
            
            attach_original = st.checkbox(
                "Attach Original PDF (--attach-original)",
                value=False,
                help="Attach the original PDF as a reference within the output file"
            )
        
        entity_filter = st.multiselect(
            "Filter Entity Types (Optional)",
            options=[
                "AU_TFN", "AU_MEDICARE", "AU_ABN", "AU_ACN", "AU_PASSPORT",
                "AU_CENTRELINK_CRN", "AU_DRIVER_LICENSE", "AU_BSB", 
                "AU_BANK_ACCOUNT", "AU_PHONE_NUMBER", "AU_STATE", "AU_POSTCODE",
                "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD",
                "DATE_TIME", "LOCATION", "ORGANIZATION"
            ],
            default=[],
            help="Select specific entity types to redact. Leave empty to redact all types.",
            key="pdf_entity_filter"
        )

    pdf_file = st.file_uploader(
        "Upload .pdf File(s)",
        type=["pdf"],
        accept_multiple_files=True,
        help="You can select multiple PDFs to process in batch"
    )

    process_pdf_btn = st.button(
        "Process PDF",
        type="primary",
        key="process_pdf",
        use_container_width=True,
    )

    log_placeholder_pdf = st.empty()

    render_pdf_actions_and_preview()

    if process_pdf_btn:
        if not pdf_file:
            st.error("Please Upload PDF File(s).")
        else:
            files_to_process = pdf_file if isinstance(pdf_file, list) else [pdf_file]

            with st.spinner(f"Processing {len(files_to_process)} PDF(s)... (OCR May Take Time For Scanned PDFs)"):
                processed_files = []
                all_outputs = []

                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        tmpdir = Path(tmpdir)

                        for file_item in files_to_process:
                            def build_pdf_command(in_path, work_dir):
                                out_path = work_dir / f"{in_path.stem}_redacted.pdf"
                                cmd = [
                                    "-m", "pdf_redactor.cli",
                                    "--in", str(in_path),
                                    "--out", str(out_path),
                                    "--lang", language,
                                    "--min-score", str(min_score),
                                ]

                                if not draw_labels:
                                    cmd.append("--no-labels")

                                if label_prefix:
                                    cmd.extend(["--label-prefix", label_prefix])

                                if attach_original:
                                    cmd.append("--attach-original")

                                if entity_filter:
                                    cmd.extend(["--entities"] + entity_filter)

                                return cmd, out_path

                            rc, out, err, out_path = process_file(
                                "pdf", file_item, None, tmpdir,
                                build_pdf_command, lambda x: None
                            )

                            if out_path and out_path.exists():
                                processed_files.append({
                                    "name": out_path.name,
                                    "bytes": out_path.read_bytes(),
                                    "success": rc == 0
                                })

                            all_outputs.append((rc, out, err))

                        if processed_files:
                            st.session_state["last_pdf_files"] = processed_files

                        if len(files_to_process) == 1:
                            rc, out, err = all_outputs[0]
                            display_command_logs(log_placeholder_pdf,
                                build_pdf_command(tmpdir / "dummy.pdf", tmpdir)[0], out, err)
                        else:
                            with log_placeholder_pdf.container():
                                st.markdown("### Batch Processing Summary")
                                success_count = sum(1 for f in processed_files if f["success"])
                                st.info(f"Processed {len(processed_files)}/{len(files_to_process)} PDFs successfully")

                        if processed_files:
                            render_pdf_actions_and_preview()
                        else:
                            st.info("No Output Files Produced. See Logs Above.")

                except Exception as e:
                    st.exception(e)
