import os
import sys
import subprocess
from pathlib import Path
from io import BytesIO
import zipfile
import streamlit as st

from .config import src_dir

try:
    from entity_mapping import (
        ALL_AU_ENTITY_TYPES,
        AU_ENTITY_SEVERITY_MAP,
        get_entity_severity,
        get_entities_by_group,
    )
    HAS_ENTITY_MAPPING = True
except ImportError:
    HAS_ENTITY_MAPPING = False
    ALL_AU_ENTITY_TYPES = []
    AU_ENTITY_SEVERITY_MAP = {}


def run_module_command(cmd_args, cwd=None):
    env = os.environ.copy()
    py_path = str(src_dir)
    env["PYTHONPATH"] = py_path + os.pathsep + env.get("PYTHONPATH", "")

    full_cmd = [sys.executable] + cmd_args
    proc = subprocess.run(
        full_cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True
    )

    return proc.returncode, proc.stdout, proc.stderr


def make_safe_filename(name: str) -> str:
    bad = '<>:"/\\|?*'
    for ch in bad:
        name = name.replace(ch, "_")
    return name


def display_command_logs(log_placeholder, cmd, out, err=None):
    with log_placeholder.container():
        st.markdown("### Command Executed:")
        st.code(" ".join([sys.executable] + cmd), language="bash")

        if out:
            st.markdown("### Output:")
            st.code(out)

        if err:
            st.markdown("### Error:")
            st.code(err)


def process_file(file_type, input_file, input_text, work_dir, cmd_builder, output_processor):
    if input_file:
        raw_name = make_safe_filename(Path(input_file.name).stem)

        if file_type == "text":
            ext = ".txt"
        elif file_type == "pdf":
            ext = ".pdf"
        elif file_type == "image":
            ext = Path(input_file.name).suffix or ".png"
        elif file_type == "csv":
            ext = ".csv"
        else:
            raise ValueError(f"FileType: {file_type}")

        in_path = work_dir / f"{raw_name}{ext}"
        in_path.write_bytes(input_file.read())
    elif input_text and file_type == "text":
        in_path = work_dir / "pasted_input.txt"
        in_path.write_text(input_text, encoding="utf-8")
    else:
        raise ValueError("No Input Provided")

    cmd, out_path = cmd_builder(in_path, work_dir)

    rc, out, err = run_module_command(cmd, cwd=work_dir)

    if rc == 0 and out_path and out_path.exists():
        output_processor(out_path)

    return rc, out, err, out_path


def display_entity_info():
    if not HAS_ENTITY_MAPPING:
        st.info("Entity mapping module not available.")
        return

    entity_descriptions = {
        "AU_TFN": "Tax File Number - 9-Digit Identifier Issued By ATO (E.G., 123 456 782)",
        "AU_MEDICARE": "Medicare Number - 10+1 Digit Health Card Number (E.G., 2123 45670 1)",
        "AU_PASSPORT": "Australian Passport - 1-2 Letters + 7 Digits (E.G., N1234567)",
        "AU_CENTRELINK_CRN": "Centrelink Customer Reference Number - 9-10 Digit Identifier",
        "AU_DRIVER_LICENSE": "Driver License - State-Specific Formats (NSW: 8 Digits, VIC: 10 Digits)",
        "AU_ABN": "Australian Business Number - 11 Digits With Check-Sum Validation",
        "AU_ACN": "Australian Company Number - 9-Digit ASIC Identifier",
        "AU_BANK_ACCOUNT": "Bank Account Number - 6-12 Digit Account Identifier",
        "AU_BSB": "Bank State Branch - 6-Digit Branch Code (E.G., 062-000)",
        "CREDIT_CARD": "Credit Card Number - 13-19 Digit Payment Card With Luhn Validation",
        "AU_PHONE_NUMBER": "Australian Phone - Mobile (04XX), Landline, Toll-Free (1300/1800)",
        "PERSON": "Person Name - Full Names, First/Last Names Using NER",
        "EMAIL_ADDRESS": "Email Address - Standard Email Format (User@Domain.Com)",
        "PHONE_NUMBER": "Phone Number - International Phone Numbers (Various Formats)",
        "DATE_TIME": "Date & Time - Various Date/Time Formats And Representations",
        "ORGANIZATION": "Organization Name - Company And Organization Names",
        "AU_STATE": "Australian State/Territory - NSW, VIC, QLD, Etc. (Abbreviations Or Full)",
        "AU_POSTCODE": "Australian Postcode - 4-Digit Postal Codes",
        "LOCATION": "Location - Geographic Locations, Addresses, Places",
    }

    st.markdown("### 🇦🇺 Supported Australian Entity Types")

    critical_entities = [e for e in ALL_AU_ENTITY_TYPES if get_entity_severity(e) == "critical"]
    high_entities = [e for e in ALL_AU_ENTITY_TYPES if get_entity_severity(e) == "high"]
    medium_entities = [e for e in ALL_AU_ENTITY_TYPES if get_entity_severity(e) == "medium"]
    low_entities = [e for e in ALL_AU_ENTITY_TYPES if get_entity_severity(e) == "low"]

    col1, col2 = st.columns(2)

    with col1:
        if critical_entities:
            st.markdown("**🔴 Critical (Government IDs)**")
            for entity in critical_entities:
                description = entity_descriptions.get(entity, "No Description Available")
                with st.expander(f"ℹ️ `{entity}`", expanded=False):
                    st.caption(description)

        if high_entities:
            st.markdown("**🟠 High (Financial)**")
            for entity in high_entities:
                description = entity_descriptions.get(entity, "No Description Available")
                with st.expander(f"ℹ️ `{entity}`", expanded=False):
                    st.caption(description)

    with col2:
        if medium_entities:
            st.markdown("**🟡 Medium (Personal)**")
            for entity in medium_entities:
                description = entity_descriptions.get(entity, "No Description Available")
                with st.expander(f"ℹ️ `{entity}`", expanded=False):
                    st.caption(description)

        if low_entities:
            st.markdown("**🔵 Low (Geographic)**")
            for entity in low_entities:
                description = entity_descriptions.get(entity, "No Description Available")
                with st.expander(f"ℹ️ `{entity}`", expanded=False):
                    st.caption(description)


def get_all_entity_types():
    if HAS_ENTITY_MAPPING:
        return ALL_AU_ENTITY_TYPES
    return []


def create_zip_from_files(files_list):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_data in files_list:
            zip_file.writestr(file_data['name'], file_data['bytes'])
    zip_buffer.seek(0)
    return zip_buffer
