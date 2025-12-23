import streamlit as st
st.write("App loading...")

from processor import run_pipeline_and_zip, previous_month_str

st.set_page_config(page_title="View Reports Processor", layout="centered")

st.title("View Reports – Excel Processor")
st.write("Upload platform Excel files + DB file + Template file, then download the processed results as a ZIP.")

st.subheader("1) Upload inputs")

platform_files = st.file_uploader(
    "Platform files (Excel) – you can upload multiple",
    type=["xlsx", "xls", "csv"],
    accept_multiple_files=True,
)

db_file = st.file_uploader(
    "DB file (Excel) – the mapping file",
    type=["xlsx", "xls"],
    accept_multiple_files=False,
)

template_file = st.file_uploader(
    "Template file (Excel) – the formatted template to fill",
    type=["xlsx", "xls"],
    accept_multiple_files=False,
)

st.subheader("2) Options")
include_intermediate = st.checkbox(
    "Include intermediate files in ZIP (cleaned_*, mapped_*)",
    value=False,
)

st.caption(f"Default month used in template B1 is previous month: {previous_month_str()}")

st.subheader("3) Run")

can_run = bool(platform_files) and (db_file is not None) and (template_file is not None)

if not can_run:
    st.info("To run: upload at least 1 platform file + DB file + Template file.")
else:
    if st.button("Process and generate ZIP", type="primary"):
        with st.spinner("Processing..."):
            platform_payload = [(f.name, f.getvalue()) for f in platform_files]
            result = run_pipeline_and_zip(
                platform_files=platform_payload,
                db_excel_bytes=db_file.getvalue(),
                template_excel_bytes=template_file.getvalue(),
                include_intermediate=include_intermediate,
            )

        st.success("Done!")
        st.text(result.summary)

        st.download_button(
            label="Download results ZIP",
            data=result.zip_bytes,
            file_name="view_reports_outputs.zip",
            mime="application/zip",
        )
