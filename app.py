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
    layout="centered",
)

# -----------------------------
# Minimal "serious" styling (single-page, no sidebar)
# -----------------------------
st.markdown(
    """
    <style>
      /* Hide Streamlit chrome */
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      header {visibility: hidden;}

      /* Page container */
      .block-container {padding-top: 2.2rem; padding-bottom: 2.2rem; max-width: 920px;}

      /* Typography */
      h1 {font-size: 2.1rem; font-weight: 850; letter-spacing: -0.02em; margin-bottom: 0.25rem;}
      h2 {font-size: 1.25rem; font-weight: 800; margin-top: 1.25rem; margin-bottom: 0.5rem;}
      .stMarkdown p {font-size: 0.98rem; line-height: 1.55;}
      .muted {color: rgba(49, 51, 63, 0.75);}

      /* Card */
      .card {
        border: 1px solid rgba(49, 51, 63, 0.18);
        border-radius: 16px;
        padding: 16px 18px;
        background: rgba(255,255,255,0.02);
      }
      .card-title {font-weight: 800; font-size: 1.0rem; margin-bottom: 6px;}
      .card-sub {color: rgba(49, 51, 63, 0.75); font-size: 0.95rem;}

      /* Buttons */
      .stButton button, .stDownloadButton button {padding: 0.62rem 1rem; font-weight: 750;}
      .stFileUploader label {font-weight: 750;}
      .stCheckbox label {font-weight: 650;}

      /* Remove extra top whitespace above first widget sometimes */
      div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stFileUploader"]) {margin-top: 0.25rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Built-in template (users won't upload)
# Put your template here: assets/template.xlsx
# -----------------------------
TEMPLATE_PATH = Path("assets/template.xlsx")
if not TEMPLATE_PATH.exists():
    st.error(
        "Template file not found. Add it to your repo at `assets/template.xlsx` and redeploy."
    )
    st.stop()

TEMPLATE_BYTES = TEMPLATE_PATH.read_bytes()

# -----------------------------
# Header
# -----------------------------
st.title("View Reports Processor")
st.markdown(
    "<div class='muted'>Upload platform files and a mapping (DB) file. "
    "The report template is built-in.</div>",
    unsafe_allow_html=True,
)

st.write("")  # small spacer

# -----------------------------
# Inputs (single interface)
# -----------------------------
st.markdown(
    """
    <div class="card">
      <div class="card-title">Inputs</div>
      <div class="card-sub">Upload the files below, then click <b>Process</b>.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

platform_files = st.file_uploader(
    "Platform files (Excel/CSV) — you can upload multiple",
    type=["xlsx", "xls", "csv"],
    accept_multiple_files=True,
    help="Upload one or more platform files. Each file may contain multiple sheets.",
)

db_file = st.file_uploader(
    "Mapping file (DB Excel)",
    type=["xlsx", "xls"],
    accept_multiple_files=False,
    help="This file is used to enrich/resolve HOUSE_NUMBER and platform names.",
)

st.write("")

with st.expander("Options", expanded=False):
    include_intermediate = st.checkbox(
        "Include intermediate outputs (cleaned_*, mapped_*) in ZIP",
        value=False,
    )
    st.caption(f"Template month (B1) defaults to previous month: **{previous_month_str()}**")
    st.caption("Template is built-in from: `assets/template.xlsx`")
else:
    # when expander closed, keep variable defined
    include_intermediate = False

st.write("")

# -----------------------------
# Run + Output area (single interface)
# -----------------------------
st.markdown(
    """
    <div class="card">
      <div class="card-title">Run</div>
      <div class="card-sub">When processing finishes, a ZIP download button will appear here.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

can_run = bool(platform_files) and (db_file is not None)

col1, col2 = st.columns([1, 1])

with col1:
    if not can_run:
        st.button("Process", type="primary", use_container_width=True, disabled=True)
    else:
        process_clicked = st.button("Process", type="primary", use_container_width=True)

with col2:
    st.caption("Tip: If you get unexpected results, enable intermediate outputs and inspect the cleaned/mapped files.")

# Session state for result
if "result_zip" not in st.session_state:
    st.session_state["result_zip"] = None
if "result_summary" not in st.session_state:
    st.session_state["result_summary"] = None

# Processing
if can_run and process_clicked:
    with st.spinner("Processing..."):
        platform_payload = [(f.name, f.getvalue()) for f in platform_files]
        result = run_pipeline_and_zip(
            platform_files=platform_payload,
            db_excel_bytes=db_file.getvalue(),
            template_excel_bytes=TEMPLATE_BYTES,
            include_intermediate=include_intermediate,
        )

    st.session_state["result_zip"] = result.zip_bytes
    st.session_state["result_summary"] = result.summary

st.write("")

# Results area
if st.session_state["result_zip"]:
    st.success("Processing complete.")
    st.text(st.session_state["result_summary"])

    st.download_button(
        label="Download results ZIP",
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
    st.info("Upload platform files + mapping (DB) file, then click **Process**.")
