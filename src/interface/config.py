import sys
from pathlib import Path
import streamlit as st

try:
    from streamlit_pdf_viewer import pdf_viewer
    HAS_PDF_VIEWER = True
except Exception:
    HAS_PDF_VIEWER = False


repo_root = Path(__file__).resolve().parent.parent.parent
src_dir = repo_root / "src"
styles_dir = repo_root / "styles"
theme_css = styles_dir / "theme.css"
images_dir = repo_root / "images"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


def setup_page():
    st.set_page_config(
        page_title="PII & SPI Redactor",
        page_icon="🛡️",
        layout="wide"
    )


def inject_css():
    if theme_css.exists():
        css = theme_css.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def display_header():
    top_logo_path = images_dir / "images.png"

    if top_logo_path.exists():
        left, center, right = st.columns([1, 4, 1])
        with center:
            st.image(str(top_logo_path), use_container_width=True)

    st.title("🛡️ PII & SPI Redactor")
    st.caption("PII - Personally Identifiable Information; SPI - Sensitive Personal Information")
    st.caption(
        "This application detects and redacts PII/SPI from multiple file formats using "
        "centralized Australian-specific entity recognition powered by Microsoft Presidio."
    )
    st.caption(
        "Supported entities include Australian government IDs (TFN, Medicare, ABN, ACN, "
        "Centrelink CRN, Driver License, Passport), financial information (BSB, bank accounts), "
        "contact details (phone numbers), and common PII (names, emails, addresses)."
    )
    st.caption(
        "The detection and redaction of this information is essential for protecting "
        "individual privacy, ensuring regulatory compliance (Privacy Act 1988), and reducing "
        "security risks from data breaches or unauthorized disclosure."
    )
    st.caption(
        "This tool allows organizations to safely share, store, and analyze data while "
        "preventing unnecessary exposure of sensitive personal and business information."
    )
