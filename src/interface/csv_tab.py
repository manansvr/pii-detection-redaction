import tempfile
from pathlib import Path
import streamlit as st

from .helpers import process_file, display_command_logs, display_entity_info
from .components import render_download_and_preview, render_multiple_files_download


def render_csv_actions_and_preview():
    files_list = st.session_state.get("last_csv_files")
    if files_list:
        render_multiple_files_download(files_list, "csv")
        return

    csv_bytes = st.session_state.get("last_csv_bytes")
    csv_name = st.session_state.get("last_csv_name")

    if not csv_bytes or not csv_name:
        return

    st.download_button(
        label="⬇️ Download Redacted CSV",
        data=csv_bytes,
        file_name=csv_name,
        mime="text/csv",
        key=f"dl_csv_{csv_name}",
        use_container_width=True,
    )

    pv_key = f"show_csv_preview::{csv_name}"
    if pv_key not in st.session_state:
        st.session_state[pv_key] = False

    st.session_state[pv_key] = st.checkbox(
        "👁️ Show Redacted CSV Preview",
        value=st.session_state[pv_key],
        key=f"pv_csv_toggle_{csv_name}",
        help="Toggle To Show/Hide The Preview. This Will Persist Until You Process A New File.",
    )

    if st.session_state[pv_key]:
        st.markdown("### Preview")
        try:
            preview_text = csv_bytes.decode("utf-8", errors="replace")
        except Exception:
            preview_text = ""

        st.text_area(
            label="Redacted CSV Preview",
            value=preview_text,
            height=300,
            label_visibility="collapsed",
            key=f"csv_area_preview_{csv_name}",
        )


def render_csv_tab():
    st.subheader("CSV Detection & Redaction")
    st.caption(
        "The csv_redactor module analyzes and redacts PII/SPI from structured CSV files using "
        "centralized Australian entity recognizers."
    )
    st.caption(
        "This module processes CSV files cell-by-cell, identifies sensitive entities including "
        "Australian government IDs, financial information, and personal data, then replaces them "
        "with either redaction characters (***) or descriptive entity labels (<AU_TFN>, <EMAIL>)."
    )
    st.caption(
        "Supports customizable delimiters, header row preservation, and maintains the original "
        "structure and formatting of your CSV files for seamless data pipeline integration."
    )

    with st.expander("🇦🇺 View Supported Entity Types"):
        display_entity_info()

    with st.expander("Advanced Options"):
        col1, col2 = st.columns(2)

        with col1:
            delimiter = st.selectbox(
                "CSV Delimiter",
                options=[",", ";", "\t", "|"],
                index=0,
                format_func=lambda x: {
                    ",": "Comma (,)",
                    ";": "Semicolon (;)",
                    "\t": "Tab (\\t)",
                    "|": "Pipe (|)"
                }[x],
                help="The Character That Separates Columns In Your CSV File",
            )

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
                help="Language Code For Text Analysis In CSV Cells"
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
            help="Select Specific Entity Types To Detect. Leave Empty To Detect All Types.",
            key="csv_entity_filter"
        )

        skip_header = st.checkbox(
            "Skip Header Row",
            value=True,
            help="Treat The First Row As A Header And Don't Redact It",
        )

        min_score = st.number_input(
            "Min Score (--min-score)",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.05,
            format="%.2f",
            help=(
                "Confidence Threshold (0–1). Entities Below This Score Are Ignored. "
                "Increase To Reduce False Positives; Decrease To Detect Weaker Matches."
            ),
        )

        use_labels = st.checkbox(
            "Use Entity Labels (<AU_TFN>, <EMAIL>, etc.)",
            value=False,
            help=(
                "Replace PII With Descriptive Entity Type Labels Like <AU_TFN>, <AU_MEDICARE>, <EMAIL> "
                "instead of Generic Redaction Characters. Useful For Data Analysis & Validation."
            ),
        )

        if not use_labels:
            redaction_char = st.text_input(
                "Redaction Character",
                value="*",
                max_chars=1,
                help="Character To Use For Redacting PII (default: *)",
            )
        else:
            redaction_char = "*"

        enable_summary = st.checkbox(
            "Show Summary",
            value=True,
            help="Display Summary Statistics of Detections In The Logs",
        )

        save_json = st.checkbox(
            "Save Detection Results as JSON",
            value=False,
            help="Save Detailed Detection Results To A JSON File Alongside The Redacted CSV",
        )

    csv_file = st.file_uploader(
        "Upload CSV File(s)",
        type=["csv"],
        accept_multiple_files=True,
        help="You Can Select Multiple CSV Files To Process In Batch"
    )

    process_csv_btn = st.button(
        "Process CSV",
        type="primary",
        key="process_csv",
        use_container_width=True,
    )

    log_placeholder_csv = st.empty()

    render_csv_actions_and_preview()

    if process_csv_btn:
        if not csv_file:
            st.error("Please Upload CSV File(s).")
        else:
            files_to_process = csv_file if isinstance(csv_file, list) else [csv_file]

            with st.spinner(f"Processing {len(files_to_process)} CSV file(s)..."):
                processed_files = []
                all_outputs = []

                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        tmpdir = Path(tmpdir)

                        for file_item in files_to_process:
                            def build_csv_command(in_path, work_dir):
                                out_path = work_dir / f"{in_path.stem}_redacted.csv"

                                cmd = [
                                    "-m", "csv_redactor.cli",
                                    "--in", str(in_path),
                                    "--out", str(out_path),
                                    "--delimiter", delimiter,
                                    "--min-score", str(min_score),
                                    "--redaction-char", redaction_char,
                                    "--lang", language,
                                ]

                                if not skip_header:
                                    cmd.append("--no-skip-header")

                                if use_labels:
                                    cmd.append("--use-labels")

                                if enable_summary:
                                    cmd.append("--summary")

                                if save_json:
                                    json_path = work_dir / f"{in_path.stem}_detections.json"
                                    cmd.extend(["--json-output", str(json_path)])

                                if entity_filter:
                                    cmd.extend(["--entities"] + entity_filter)

                                return cmd, out_path

                            rc, out, err, out_path = process_file(
                                "csv", file_item, None, tmpdir,
                                build_csv_command, lambda x: None
                            )

                            if out_path and out_path.exists():
                                processed_files.append({
                                    "name": out_path.name,
                                    "bytes": out_path.read_bytes(),
                                    "success": rc == 0
                                })

                            all_outputs.append((rc, out, err))

                        if processed_files:
                            st.session_state["last_csv_files"] = processed_files

                        if len(files_to_process) == 1:
                            rc, out, err = all_outputs[0]
                            display_command_logs(log_placeholder_csv,
                                build_csv_command(tmpdir / "dummy.csv", tmpdir)[0], out, err)
                        else:
                            with log_placeholder_csv.container():
                                st.markdown("### Batch Processing Summary")
                                success_count = sum(1 for f in processed_files if f["success"])
                                st.info(f"Processed {len(processed_files)}/{len(files_to_process)} CSV files successfully")

                        if processed_files:
                            render_csv_actions_and_preview()
                        else:
                            st.info("No Output Files Produced. See Logs Above.")

                except Exception as e:
                    st.exception(e)
