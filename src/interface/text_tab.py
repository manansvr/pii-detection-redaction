import tempfile
from pathlib import Path
import streamlit as st

from .helpers import process_file, display_command_logs, display_entity_info
from .components import render_text_actions_and_preview


def render_text_tab():
    st.subheader("Text Detection & Redaction")
    st.caption(
        "The text_detector module analyzes and redacts PII from plain text inputs using "
        "centralized Australian entity recognizers."
    )
    st.caption(
        "This module processes text files or pasted content, identifies sensitive entities "
        "using pattern matching and context analysis, and replaces or masks detected information "
        "according to your chosen redaction strategy."
    )
    st.caption(
        "Ideal for processing logs, emails, transcripts, reports, and other text-based "
        "data sources that may contain Australian government IDs, financial information, "
        "or personal contact details."
    )

    with st.expander("🇦🇺 View Supported Entity Types"):
        display_entity_info()

    mode = st.radio(
        "Input Type",
        options=["Upload .txt File", "Paste Raw Text"],
        horizontal=True,
    )

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
                help="Language Code For Text Analysis & NER Models"
            )

        with col2:
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
                help="Select Specific Entity Types To Detect. Leave Empty To Detect All Types.",
                key="text_entity_filter"
            )

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

        min_score = st.number_input(
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

        print_text = st.checkbox(
            "Print Matched Text To Logs (--print-text)",
            value=False,
            help=(
                "When Enabled, Matched Spans Are Printed To Stdout For Debugging/Audit. "
                "Useful For Verifying Detections During Testing."
            ),
        )

        redact_to_file = st.checkbox(
            "Redact To A New File (mask-to-file)",
            value=True,
            help=(
                "Writes The Redacted Output To A New .txt File Instead Of Only "
                "Printing Results To Logs."
            ),
        )

        anonymize_text = st.checkbox(
            "Anonymize (Only When Using Raw Text Input)",
            value=False,
            help=(
                "When Pasting Raw Text (Not A File), Anonymize In-Memory & Preview "
                "Without Creating An Output File."
            ),
        )

    input_text = None
    input_upload = None

    if mode == "Upload .txt File":
        input_upload = st.file_uploader(
            "Upload .txt File(s)",
            type=["txt"],
            accept_multiple_files=True,
            help="You Can Select Multiple Files To Process In Batch"
        )
    else:
        input_text = st.text_area(
            "Paste Your Text Here",
            height=200,
            placeholder="e.g., My ABN is 51 824 753 556 and TFN is 123 456 782. Contact: manan.rathi@gmail.com",
        )

    process_btn = st.button(
        "Process Text",
        type="primary",
        use_container_width=True,
    )

    log_placeholder = st.empty()

    render_text_actions_and_preview()

    if process_btn:
        if not input_upload and not input_text:
            st.error("Please Upload .txt File(s) Or Paste Some Text.")
        else:
            files_to_process = input_upload if input_upload else [None]

            with st.spinner(f"Processing {len(files_to_process)} file(s)..." if input_upload else "Processing Text..."):
                processed_files = []
                all_outputs = []

                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        tmpdir = Path(tmpdir)

                        for file_item in files_to_process:
                            def build_text_command(in_path, work_dir):
                                cmd = [
                                    "-m", "text_detector",
                                    "--in", str(in_path),
                                    "--size", str(size),
                                    "--overlap", str(overlap),
                                    "--min-score", str(min_score),
                                    "--lang", language,
                                ]

                                if entity_filter:
                                    cmd.extend(["--entities"] + entity_filter)

                                if print_text:
                                    cmd.append("--print-text")

                                out_path = None
                                if redact_to_file:
                                    out_name = f"{in_path.stem}_redacted.txt"
                                    out_path = work_dir / out_name
                                    cmd.extend(["--mask-to-file", out_name])
                                elif input_text and anonymize_text:
                                    cmd.append("--anonymize")

                                return cmd, out_path

                            rc, out, err, out_path = process_file(
                                "text", file_item, input_text, tmpdir,
                                build_text_command, lambda x: None
                            )

                            if out_path and out_path.exists():
                                processed_files.append({
                                    "name": out_path.name,
                                    "bytes": out_path.read_bytes(),
                                    "success": rc == 0
                                })

                            all_outputs.append((rc, out, err))

                        if processed_files:
                            st.session_state["last_text_files"] = processed_files

                        if len(files_to_process) == 1:
                            rc, out, err = all_outputs[0]
                            display_command_logs(log_placeholder,
                                build_text_command(tmpdir / "dummy.txt", tmpdir)[0], out)
                        else:
                            with log_placeholder.container():
                                st.markdown("### Batch Processing Summary")
                                success_count = sum(1 for f in processed_files if f["success"])
                                st.info(f"Processed {len(processed_files)}/{len(files_to_process)} files successfully")

                        if processed_files:
                            render_text_actions_and_preview()
                        else:
                            st.info(
                                "No Output Files Generated "
                                "(Likely Detect-Only/Anonymize Mode). "
                                "Check Logs For Results."
                            )

                except Exception as e:
                    st.exception(e)
