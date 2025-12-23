# app.py
from pathlib import Path
import streamlit as st
from datetime import date
from pathlib import Path



from processor import run_pipeline_and_zip, previous_month_str

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="View Reports Processor",
    page_icon=Path("assets/logo.png"),
    layout="centered",
)

# -----------------------------
# Minimal styling (single-page)
# -----------------------------
st.markdown(
    """
    <style>
      /* Hide Streamlit chrome */
      /* Hide Streamlit branding & chrome */
      #MainMenu {display: none;}
      header {display: none;}
      footer {display: none;}
        
      /* Extra safety for Community Cloud footer */
      div[data-testid="stFooter"] {display: none;}
      div[data-testid="stToolbar"] {display: none;}

      /* Page container */
      .block-container {
        padding-top: 2.2rem;
        padding-bottom: 2.2rem;
        max-width: 920px;
      }

      /* Typography */
      h1 {
        font-size: 2.1rem;
        font-weight: 850;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
      }
      h2 {
        font-size: 1.25rem;
        font-weight: 800;
        margin-top: 1.25rem;
        margin-bottom: 0.5rem;
      }
      .stMarkdown p {
        font-size: 0.98rem;
        line-height: 1.55;
      }
      .muted {
        color: rgba(49, 51, 63, 0.75);
      }

      /* Card */
      .card {
        border: 1px solid rgba(49, 51, 63, 0.18);
        border-radius: 16px;
        padding: 16px 18px;
        background: rgba(255,255,255,0.02);
      }
      .card-title {
        font-weight: 800;
        font-size: 1.0rem;
        margin-bottom: 6px;
      }
      .card-sub {
        color: rgba(49, 51, 63, 0.75);
        font-size: 0.95rem;
      }

      /* Buttons & inputs */
      .stButton button,
      .stDownloadButton button {
        padding: 0.62rem 1rem;
        font-weight: 750;
      }
      .stFileUploader label {
        font-weight: 750;
      }
      .stCheckbox label {
        font-weight: 650;
      }
      /* Primary action button (Process) */
     .stButton button[kind="primary"] {
       background: linear-gradient(180deg, #1f4fd8, #1a3fa8);
       color: white;
       border-radius: 14px;
       border: none;
      }
    
     .stButton button[kind="primary"]:hover {
       background: linear-gradient(180deg, #245ef5, #1f4fd8);
       color: white;
      }
      /* Subtle footer trademark */
     .keshet-footer {
       position: fixed;
       bottom: 8px;
       left: 0;
       right: 0;
       text-align: center;
       font-size: 0.72rem;
       color: rgba(49, 51, 63, 0.35);
       pointer-events: none;
       letter-spacing: 0.02em;
      }


    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Built-in template (users won't upload)
# -----------------------------
TEMPLATE_PATH = Path("assets/template_view_reports.xlsx")
if not TEMPLATE_PATH.exists():
    st.error(
        "Template file not found. Please add it to the repo at `assets/template_view_reports.xlsx` "
        "and redeploy the app."
    )
    st.stop()

TEMPLATE_BYTES = TEMPLATE_PATH.read_bytes()

# -----------------------------
# Header
# -----------------------------
st.title("View Reports Processor")
st.markdown(
    "<div class='muted'>Upload platform files and a mapping (KeshetTV) file. "
    "The report template is built in.</div>",
    unsafe_allow_html=True,
)

st.write("")

# -----------------------------
# Inputs
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

st.markdown("### Platform files")
st.markdown(
    "<div class='muted'>Upload one or more platform Excel / CSV files.</div>",
    unsafe_allow_html=True,
)

platform_files = st.file_uploader(
    "",
    type=["xlsx", "xls", "csv"],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

st.write("")

st.markdown("### Mapping file (KeshetTV)")
st.markdown(
    "<div class='muted'>Used to resolve HOUSE_NUMBER and platform program names.</div>",
    unsafe_allow_html=True,
)

db_file = st.file_uploader(
    "",
    type=["xlsx", "xls"],
    accept_multiple_files=False,
    label_visibility="collapsed",
)

st.write("")

# -----------------------------
# Options
# -----------------------------
include_intermediate = False
selected_month_str = previous_month_str()

with st.expander("Options", expanded=False):
    include_intermediate = st.checkbox(
        "Include intermediate outputs (cleaned_*, mapped_*) in ZIP",
        value=False,
    )

    st.markdown("**Output month (written into the template)**")
    # pick any day within the month; we'll format it as MM/YYYY
    chosen_date = st.date_input(
        "Month",
        value=date.today().replace(day=1),
        help="Choose the month that will be written into the output files (template cell B1 and date column).",
    )
    selected_month_str = f"{chosen_date.month:02d}/{chosen_date.year}"

    st.caption(f"Selected month: **{selected_month_str}**")
    st.caption("Template source: `assets/template.xlsx`")


st.write("")

# -----------------------------
# Run + Output
# -----------------------------
st.markdown(
    """
    <div class="card">
      <div class="muted" style="font-size: 0.9rem;">
        Click <b>Process</b>. The ZIP download will appear below when ready.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

can_run = bool(platform_files) and (db_file is not None)

process_clicked = st.button(
    "Process",
    type="primary",
    use_container_width=True,
    disabled=not can_run,
)

# -----------------------------
# Session state
# -----------------------------
if "result_zip" not in st.session_state:
    st.session_state["result_zip"] = None
if "result_summary" not in st.session_state:
    st.session_state["result_summary"] = None

# -----------------------------
# Processing
# -----------------------------
if can_run and process_clicked:
    with st.spinner("Processing files..."):
        platform_payload = [(f.name, f.getvalue()) for f in platform_files]
        result = run_pipeline_and_zip(
            platform_files=platform_payload,
            db_excel_bytes=db_file.getvalue(),
            template_excel_bytes=TEMPLATE_BYTES,
            include_intermediate=include_intermediate,
            month_str=selected_month_str,   # NEW
        )

    st.session_state["result_zip"] = result.zip_bytes
    st.session_state["result_summary"] = result.summary

st.write("")

# -----------------------------
# Results
# -----------------------------
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
    st.info("Upload platform files + mapping (KeshetTV) file, then click **Process**.")


st.markdown(
    """
    <div class="keshet-footer">
      © Keshet Digital Data Team
    </div>
    """,
    unsafe_allow_html=True,
)
