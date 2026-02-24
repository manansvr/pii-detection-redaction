import base64
from io import BytesIO
import zipfile
import streamlit as st
import streamlit.components.v1 as components

try:
    from streamlit_pdf_viewer import pdf_viewer
    HAS_PDF_VIEWER = True
except Exception:
    HAS_PDF_VIEWER = False


def render_download_and_preview(file_type, bytes_key, name_key, preview_renderer=None):
    file_bytes = st.session_state.get(bytes_key)
    file_name = st.session_state.get(name_key)

    if not file_bytes or not file_name:
        return

    if file_type == "text":
        mime_type = "text/plain"
        label = "⬇️ Download Redacted Text"
        preview_label = "👁️ Show Redacted Text Preview"
    else:
        mime_type = "application/pdf"
        label = "⬇️ Download Redacted PDF"
        preview_label = "👁️ Preview Redacted PDF"

    st.download_button(
        label=label,
        data=file_bytes,
        file_name=file_name,
        mime=mime_type,
        key=f"dl_{file_type}_{file_name}",
        use_container_width=True,
    )

    if file_type == "text":
        pv_key = f"show_{file_type}_preview::{file_name}"
        if pv_key not in st.session_state:
            st.session_state[pv_key] = False

        st.session_state[pv_key] = st.checkbox(
            preview_label,
            value=st.session_state[pv_key],
            key=f"pv_{file_type}_toggle_{file_name}",
            help="Toggle To Show/Hide The Preview. This Will Persist Until You Process A New File.",
        )

        if st.session_state[pv_key]:
            st.markdown("### Preview")
            if preview_renderer:
                preview_renderer(file_bytes, file_name)
            else:
                try:
                    preview_text = file_bytes.decode("utf-8", errors="replace")
                except Exception:
                    preview_text = ""

                st.text_area(
                    label="Redacted Text Preview",
                    value=preview_text,
                    height=300,
                    label_visibility="collapsed",
                    key=f"txt_area_preview_{file_name}",
                )
    else:
        if st.button(
            preview_label,
            key=f"pv_{file_type}_{file_name}",
            use_container_width=True,
        ):
            st.session_state[f"show_{file_type}_preview"] = True

        if st.session_state.get(f"show_{file_type}_preview"):
            st.markdown("### Preview")
            if preview_renderer:
                preview_renderer(file_bytes, file_name)
            else:
                if HAS_PDF_VIEWER:
                    pdf_viewer(file_bytes, width=900, height=800, key=f"pdfv_{file_name}")
                else:
                    b64_pdf = base64.b64encode(file_bytes).decode("utf-8")
                    iframe_html = f"""
                    <iframe
                        src="data:application/pdf;base64,{b64_pdf}#toolbar=1&navpanes=0&statusbar=1"
                        width="100%"
                        height="800"
                        style="border:none;"
                    ></iframe>
                    """
                    components.html(iframe_html, height=800, scrolling=True)


def render_text_actions_and_preview():
    files_list = st.session_state.get("last_text_files")
    if files_list:
        render_multiple_files_download(files_list, "text")
        return

    render_download_and_preview("text", "last_text_bytes", "last_text_name")


def render_pdf_actions_and_preview():
    files_list = st.session_state.get("last_pdf_files")
    if files_list:
        render_multiple_files_download(files_list, "pdf")
        return

    render_download_and_preview("pdf", "last_pdf_bytes", "last_pdf_name")


def render_image_actions_and_preview():
    image_bytes = st.session_state.get("last_image_bytes")
    image_name = st.session_state.get("last_image_name")

    if not image_bytes or not image_name:
        return

    st.download_button(
        label="⬇️ Download Redacted Image",
        data=image_bytes,
        file_name=image_name,
        mime="image/png",
        key=f"dl_image_{image_name}",
        use_container_width=True,
    )

    if st.button(
        "👁️ Preview Redacted Image",
        key=f"pv_image_{image_name}",
        use_container_width=True,
    ):
        st.session_state["show_image_preview"] = True

    if st.session_state.get("show_image_preview"):
        st.markdown("### Preview")
        st.image(image_bytes, use_column_width=True, caption="Redacted Image")


def render_multiple_files_download(files_list, file_type):

    if not files_list:
        return

    mime_types = {
        "text": "text/plain",
        "pdf": "application/pdf",
        "image": "image/png",
        "csv": "text/csv"
    }

    mime_type = mime_types.get(file_type, "application/octet-stream")

    if len(files_list) == 1:
        file_data = files_list[0]
        st.download_button(
            label=f"⬇️ Download {file_data['name']}",
            data=file_data['bytes'],
            file_name=file_data['name'],
            mime=mime_type,
            key=f"dl_{file_type}_{file_data['name']}",
            use_container_width=True,
        )
    else:
        st.markdown(f"### 📦 {len(files_list)} Files Processed")

        col1, col2 = st.columns([1, 1])

        with col1:
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_data in files_list:
                    zip_file.writestr(file_data['name'], file_data['bytes'])
            zip_buffer.seek(0)

            st.download_button(
                label=f"📦 Download All As ZIP ({len(files_list)} files)",
                data=zip_buffer.getvalue(),
                file_name=f"redacted_{file_type}_batch.zip",
                mime="application/zip",
                key=f"dl_zip_{file_type}_batch",
                use_container_width=True,
            )

        with col2:
            show_individual = st.checkbox(
                "Show Individual Downloads",
                value=False,
                key=f"show_individual_{file_type}"
            )

        if show_individual:
            st.markdown("#### Individual Files")
            for idx, file_data in enumerate(files_list):
                status_icon = "✅" if file_data.get('success', True) else "⚠️"
                st.download_button(
                    label=f"{status_icon} {file_data['name']}",
                    data=file_data['bytes'],
                    file_name=file_data['name'],
                    mime=mime_type,
                    key=f"dl_individual_{file_type}_{idx}_{file_data['name']}",
                    use_container_width=True,
                )
