"""Streamlit UI for NyayaDraft."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

try:
    from .processor import (
        extract_placeholders,
        list_templates,
        load_template,
        placeholder_label,
        replace_placeholders,
        render_template_to_docx_bytes,
    )
except ImportError:
    from processor import (
        extract_placeholders,
        list_templates,
        load_template,
        placeholder_label,
        replace_placeholders,
        render_template_to_docx_bytes,
    )


st.set_page_config(page_title="NyayaDraft", layout="wide")


def template_title(path: Path) -> str:
    return path.stem.replace("_", " ").title()


def get_template_options() -> list[Path]:
    return list_templates()


def build_placeholder_values(template_name: str, placeholders: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for placeholder in placeholders:
        key = f"{template_name}__{placeholder}"
        values[placeholder] = st.session_state.get(key, "")
    return values


def main() -> None:
    st.title("NyayaDraft")
    st.caption("Select a sanitized legal template, fill the placeholders, and download a DOCX draft.")

    templates = get_template_options()
    if not templates:
        st.info("No .txt templates found in drafting_module/templates/. Run the ingestion pipeline first.")
        return

    if st.button("Refresh templates"):
        st.experimental_rerun()

    selected_template = st.selectbox(
        "Template",
        templates,
        format_func=template_title,
        help="Choose a sanitized template to edit and export.",
    )

    template_text = load_template(selected_template)
    placeholders = extract_placeholders(template_text)
    placeholder_values = build_placeholder_values(selected_template.name, placeholders)

    left, right = st.columns([0.45, 0.55], gap="large")

    with left:
        st.subheader("Fields")
        if placeholders:
            with st.form("nyayadraft_fields"):
                for placeholder in placeholders:
                    input_key = f"{selected_template.name}__{placeholder}"
                    st.text_input(
                        placeholder_label(placeholder),
                        value=placeholder_values[placeholder],
                        key=input_key,
                        help=f"Enter value for {{placeholder}}.",
                    )
                submitted = st.form_submit_button("Update draft")
                if submitted:
                    st.success("Draft values updated. Scroll to the preview to download the DOCX.")

            filled_count = sum(1 for value in placeholder_values.values() if value.strip())
            completion = int((filled_count / len(placeholders)) * 100) if placeholders else 0
            st.markdown(f"**{len(placeholders)} fields · {completion}% completed**")
        else:
            st.warning("This template does not contain any {{placeholder}} fields.")

    with right:
        st.subheader("Preview")
        preview_text = replace_placeholders(template_text, placeholder_values, keep_unfilled=True)
        st.text_area("Document text", preview_text, height=520)

        if not placeholders or any(value.strip() for value in placeholder_values.values()):
            draft_bytes = render_template_to_docx_bytes(
                template_text=template_text,
                values=placeholder_values,
                title=template_title(selected_template),
                keep_unfilled=True,
            )
            st.download_button(
                "Download .docx",
                data=draft_bytes,
                file_name=f"{selected_template.stem}_draft.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        else:
            st.info("Enter at least one placeholder value to enable DOCX download.")


if __name__ == "__main__":
    main()
