import tempfile
from pathlib import Path
import streamlit as st

from .helpers import process_file, display_command_logs, display_entity_info
from .components import render_image_actions_and_preview


def render_image_tab():
    st.subheader("Image Redaction")
    st.caption(
        "The image_redactor module detects and redacts PII from image files using "
        "OCR and centralized Australian entity recognizers."
    )
    st.caption(
        "This module uses Optical Character Recognition (Tesseract OCR) to extract text "
        "from images, identifies sensitive entities including Australian government IDs, "
        "financial data, and contact information, then applies customizable redaction styles "
        "(fill, blur, pixelate, rectangle) to permanently obscure the information."
    )
    st.caption(
        "Ideal for processing scanned documents, identity cards, screenshots, receipts, "
        "photos with visible PII, and other image-based content containing sensitive text."
    )

    with st.expander("🇦🇺 View Supported Entity Types"):
        display_entity_info()

    with st.expander("Advanced Options"):
        col1, col2 = st.columns(2)

        with col1:
            redaction_mode = st.selectbox(
                "Redaction Mode (--mode)",
                options=["fill", "blur", "pixelate", "rectangle"],
                index=0,
                help="fill: Solid Color Fill; blur: Blur Effect; pixelate: Pixelated Blocks; rectangle: Outline Only"
            )

        with col2:
            min_score = st.number_input(
                "Min Confidence Score (--min-score)",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.05,
                format="%.2f",
                help="Minimum Confidence Threshold For Entity Detection (0-1)"
            )

        entity_filter = st.multiselect(
            "Filter Entity Types (--entities)",
            options=[
                "AU_TFN", "AU_MEDICARE", "AU_ABN", "AU_ACN", "AU_PASSPORT",
                "AU_CENTRELINK_CRN", "AU_DRIVER_LICENSE", "AU_BSB", 
                "AU_BANK_ACCOUNT", "AU_PHONE_NUMBER", "AU_STATE", "AU_POSTCODE",
                "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD",
                "DATE_TIME", "LOCATION", "ORGANIZATION"
            ],
            default=[],
            help="Select Specific Entity Types to Redact. Leave Empty To Redact All Types.",
            key="image_entity_filter"
        )

        fill_color = st.color_picker(
            "Fill/Rectangle Color",
            value="#000000",
            help="Color For Fill & Rectangle Modes"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            blur_radius = st.number_input(
                "Blur Radius",
                min_value=1,
                max_value=50,
                value=8,
                help="Blur Strength (Blur Mode Only)"
            )

        with col2:
            pixel_size = st.number_input(
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

        draw_labels = st.checkbox(
            "Draw Entity Labels",
            value=False,
            help="Show Entity Type Labels On Redacted Regions"
        )

        ocr_lang = st.text_input(
            "OCR Language(s)",
            value="eng",
            help="Language Codes For OCR"
        )

    image_file = st.file_uploader(
        "Upload Image File(s)",
        type=["jpg", "jpeg", "png", "bmp", "tiff"],
        accept_multiple_files=True,
        help="You Can Select Multiple Images To Process In Batch"
    )

    process_image_btn = st.button(
        "Process Image",
        type="primary",
        key="process_image",
        use_container_width=True,
    )

    log_placeholder_image = st.empty()

    render_image_actions_and_preview()

    if process_image_btn:
        if not image_file:
            st.error("Please Upload Image File(s).")
        else:
            files_to_process = image_file if isinstance(image_file, list) else [image_file]

            with st.spinner(f"Processing {len(files_to_process)} Image(s)... (OCR In Progress)"):
                processed_files = []
                all_outputs = []

                try:
                    with tempfile.TemporaryDirectory() as tmpdir:
                        tmpdir = Path(tmpdir)

                        for file_item in files_to_process:
                            def build_image_command(in_path, work_dir):
                                out_ext = in_path.suffix if in_path.suffix else ".png"
                                out_path = work_dir / f"{in_path.stem}_redacted{out_ext}"

                                cmd = [
                                    "-m", "image_redactor.cli",
                                    "--in", str(in_path),
                                    "--out", str(out_path),
                                    "--mode", redaction_mode,
                                    "--fill", fill_color,
                                    "--blur-radius", str(blur_radius),
                                    "--pixel-size", str(pixel_size),
                                    "--padding", str(padding),
                                    "--lang", ocr_lang,
                                    "--min-score", str(min_score),
                                ]

                                if draw_labels:
                                    cmd.append("--labels")

                                if entity_filter:
                                    cmd.extend(["--entities"] + entity_filter)

                                return cmd, out_path

                            rc, out, err, out_path = process_file(
                                "image", file_item, None, tmpdir,
                                build_image_command, lambda x: None
                            )

                            if out_path and out_path.exists():
                                processed_files.append({
                                    "name": out_path.name,
                                    "bytes": out_path.read_bytes(),
                                    "success": rc == 0
                                })

                            all_outputs.append((rc, out, err))

                        if processed_files:
                            st.session_state["last_image_files"] = processed_files

                        if len(files_to_process) == 1:
                            rc, out, err = all_outputs[0]
                            display_command_logs(log_placeholder_image,
                                build_image_command(tmpdir / "dummy.jpg", tmpdir)[0], out, err)
                        else:
                            with log_placeholder_image.container():
                                st.markdown("### Batch Processing Summary")
                                success_count = sum(1 for f in processed_files if f["success"])
                                st.info(f"Processed {len(processed_files)}/{len(files_to_process)} images successfully")

                        if processed_files:
                            render_image_actions_and_preview()
                        else:
                            st.info("No Output Files Produced. See Logs Above.")

                except Exception as e:
                    st.exception(e)
