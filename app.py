# app.py
from pathlib import Path
import streamlit as st

from processor import run_pipeline_and_zip, previous_month_str

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="View Reports Processor",
    page_icon="📊",
    layout="wide",
)

# -----------------------------
# Minimal "serious" styling
# - Bigger headers / cleaner spacing
# - Hide Streamlit chrome (menu/footer/header) to feel like a real app
# -----------------------------
st.markdown(
    """
    <style>
      /* Hide Streamlit chrome */
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      header {visibility: hidden;}

      /* Page width + typography tweaks */
      .block-container {padding-top: 2.0rem; padding-bottom: 2.0rem; max-width: 1200px;}
      h1 {font-size: 2.1rem; font-weight: 800; letter-spacing: -0.02em;}
      h2 {font-size: 1.35rem; font-weight: 800; margin-top: 1.2rem;}
      h3 {font-size: 1.05rem; font-weight: 700; margin-top: 0.8rem;}
      .stMarkdown p {font-size: 0.98rem; line-height: 1.5;}

      /* Make widgets a bit tighter */
      .stButton button {padding: 0.6rem 1rem; font-weight: 700;}
      .stDownloadButton button {padding: 0.6rem 1rem; font-weight: 700;}
      .stFileUploader label {font-weight: 700;}
      .stCheckbox label {font-weight: 600;}

      /* Subtle card feel */
      .card {
        border: 1px solid rgba(49, 51, 63, 0.2);
        border-radius: 14px;
        padding: 16px 18px;
        background: rgba(255,255,255,0.02);
      }
      .muted {color: rgba(49, 51, 63, 0.75);}
      .mono {font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Built-in template (users won't upload)
# Put your template here: assets/template_view_reports.xlsx
# -----------------------------
TEMPLATE_PATH = Path("assets/template_view_reports.xlsx")

if not TEMPLATE_PATH.exists():
    st.error(
        "Template file not found. Add it to your repo at: "
        "`assets/template.xlsx` (commit & redeploy)."
    )
    st.stop()

TEMPLATE_BYTES = TEMPLATE_PATH.read_bytes()

# -----------------------------
# Header
# -----------------------------
st.title("View Reports Processor")
st.markdown(
    "<div class='muted'>Upload platform Excel files and a mapping (DB) Excel file. "
    "The app generates the final report files from the built-in template.</div>",
    unsafe_allow_html=True,
)

st.divider()

# -----------------------------
# Sidebar: Inputs
# -----------------------------
with st.sidebar:
    st.markdown("## Inputs")

    platform_files = st.file_uploader(
        "Platform files (Excel/CSV)",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True,
        help="Upload one or more platform files. Each file may contain multiple sheets.",
    )

    db_file = st.file_uploader(
        "Mapping file (DB Excel)",
        type=["xlsx", "xls"],
        accept_multiple_files=False,
        help="Upload the mapping Excel used for HOUSE_NUMBER enrichment.",
    )

    st.markdown("---")
    st.markdown("## Options")
    include_intermediate = st.checkbox(
        "Include intermediate outputs (cleaned_*, mapped_*) in ZIP",
        value=False,
    )

    st.markdown("---")
    st.markdown("## Info")
    st.caption(f"Template month (B1) defaults to previous month: **{previous_month_str()}**")
    st.caption("Template is built-in: `assets/template.xlsx`")

# -----------------------------
# Main: Status + Run
# -----------------------------
left, right = st.columns([1.2, 1])

with left:
    st.markdown("## Run")
    st.markdown(
        "<div class='card'>"
        "<b>Step 1.</b> Upload platform files<br/>"
        "<b>Step 2.</b> Upload mapping (DB) file<br/>"
        "<b>Step 3.</b> Click <span class='mono'>Process</span> and download the ZIP"
        "</div>",
        unsafe_allow_html=True,
    )

    can_run = bool(platform_files) and (db_file is not None)

    if not can_run:
        st.warning("To run: upload at least 1 platform file + the mapping (DB) file.")
    else:
        process_clicked = st.button("Process", type="primary", use_container_width=True)

with right:
    st.markdown("## Output")
    st.markdown(
        "<div class='card'>"
        "<div class='muted'>After processing completes, your ZIP will appear here.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

# -----------------------------
# Processing
# -----------------------------
if "result_zip" not in st.session_state:
    st.session_state["result_zip"] = None
if "result_summary" not in st.session_state:
    st.session_state["result_summary"] = None

if can_run and process_clicked:
    with st.spinner("Processing files..."):
        platform_payload = [(f.name, f.getvalue()) for f in platform_files]
        result = run_pipeline_and_zip(
            platform_files=platform_payload,
            db_excel_bytes=db_file.getvalue(),
            template_excel_bytes=TEMPLATE_BYTES,
            include_intermediate=include_intermediate,
        )

    st.session_state["result_zip"] = result.zip_bytes
    st.session_state["result_summary"] = result.summary

# -----------------------------
# Show results (if available)
# -----------------------------
if st.session_state["result_zip"]:
    st.success("Processing complete.")
    st.text(st.session_state["result_summary"])

    st.download_button(
        label="Download results (ZIP)",
        data=st.session_state["result_zip"],
        file_name="view_reports_outputs.zip",
        mime="application/zip",
        use_container_width=True,
    )

    with st.expander("What’s inside the ZIP?", expanded=False):
        st.markdown(
            "- Final outputs: `template_*.xlsx`\n"
            "- Optional (if enabled): `cleaned_*.xlsx`, `mapped_*.xlsx`"
        )
else:
    st.caption("No output yet. Upload files in the sidebar and click Process.")
