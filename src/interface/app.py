import streamlit as st
from interface import (
    setup_page,
    inject_css,
    display_header,
    render_text_tab,
    render_pdf_tab,
    render_image_tab,
    render_csv_tab,
    render_entity_mapping_tab,
)


def main():
    setup_page()
    inject_css()
    display_header()

    tab_text, tab_pdf, tab_image, tab_csv, tab_entities = st.tabs([
        "Text (.txt)",
        "PDF (.pdf)",
        "Image (.jpg/.png)",
        "CSV (.csv)",
        "🇦🇺 Entity Mapping"
    ])

    with tab_text:
        render_text_tab()

    with tab_pdf:
        render_pdf_tab()

    with tab_image:
        render_image_tab()

    with tab_csv:
        render_csv_tab()

    with tab_entities:
        render_entity_mapping_tab()


if __name__ == "__main__":
    main()
