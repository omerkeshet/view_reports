# app.py
from pathlib import Path
from datetime import date
import streamlit as st

from processor import run_pipeline_and_zip, previous_month_str

# -----------------------------
# Config
# -----------------------------
LOGO_PATH = Path("assets/logo.png")  # optional (favicon already set by you)
TEMPLATE_PATH = Path("assets/template_view_reports.xlsx")

st.set_page_config(
    page_title="View Reports Processor",
    page_icon="📊",  # keep your logo favicon if you already set it elsewhere
    layout="centered",
)

if not TEMPLATE_PATH.exists():
    st.error("Missing template: `assets/template_view_reports.xlsx`")
    st.stop()

TEMPLATE_BYTES = TEMPLATE_PATH.read_bytes()

# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
      /* Hide Streamlit chrome (optional; keep if you want) */
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      header {visibility: hidden;}

      /* App background */
      [data-testid="stAppViewContainer"] {
        background: radial-gradient(1200px 600px at 20% -10%, rgba(31,79,216,0.10), rgba(255,255,255,0) 60%),
                    radial-gradient(1000px 700px at 90% 10%, rgba(34,197,94,0.08), rgba(255,255,255,0) 55%),
                    linear-gradient(180deg, rgba(250,250,252,1), rgba(255,255,255,1));
      }

      /* Layout container */
      .block-container {
        max-width: 980px;
        padding-top: 2.0rem;
        padding-bottom: 2.0rem;
      }

      /* Typography */
      h1 {
        font-size: 2.05rem;
        font-weight: 900;
        letter-spacing: -0.03em;
        margin-bottom: 0.25rem;
      }
      .muted { color: rgba(49, 51, 63, 0.72); }
      .tiny { font-size: 0.82rem; color: rgba(49, 51, 63, 0.65); }

      /* Cards */
      .card {
        border: 1px solid rgba(49, 51, 63, 0.14);
        border-radius: 18px;
        padding: 16px 18px;
        background: rgba(255,255,255,0.70);
        backdrop-filter: blur(6px);
        box-shadow: 0 6px 22px rgba(0,0,0,0.04);
      }
      .card h2 {
        font-size: 1.05rem;
        font-weight: 850;
        margin: 0 0 0.35rem 0;
      }

      /* Button */
      .stButton button[kind="primary"]{
        background: linear-gradient(180deg, #1f4fd8, #1a3fa8);
        color: white;
        border: none;
        border-radius: 14px;
        padding: 0.66rem 1rem;
        font-weight: 800;
      }
      .stButton button[kind="primary"]:hover{
        background: linear-gradient(180deg, #245ef5, #1f4fd8);
        color: white;
      }

      /* Inputs */
      .stFileUploader label { font-weight: 750; }
      .stDownloadButton button { border-radius: 14px; font-weight: 800; padding: 0.66rem 1rem; }

      /* Status chip */
      .chip {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        border: 1px solid rgba(49,51,63,0.16);
        background: rgba(255,255,255,0.6);
        font-size: 0.85rem;
        font-weight: 700;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Header (app shell)
# -----------------------------
colA, colB = st.columns([0.12, 0.88], vertical_alignment="center")
with colA:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=56)
    else:
        st.write("")  # keep spacing

with colB:
    st.title("View Reports Processor")
    st.markdown(
        "<div class='muted'>Generate standardized monthly view reports from platform exports. "
        "Upload files, choose month, process, and download results.</div>",
        unsafe_allow_html=True,
    )

st.write("")

# -----------------------------
# Inputs (two cards)
# -----------------------------
left, right = st.columns(2, gap="large")

with left:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h2>Platform files</h2>", unsafe_allow_html=True)
    st.markdown("<div class='muted'>Upload one or more Excel/CSV exports (multiple sheets supported).</div>", unsafe_allow_html=True)
    st.write("")
    platform_files = st.file_uploader(
        "Platform files",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h2>Mapping file (DB)</h2>", unsafe_allow_html=True)
    st.markdown("<div class='muted'>Used to resolve HOUSE_NUMBER and program naming.</div>", unsafe_allow_html=True)
    st.write("")
    db_file = st.file_uploader(
        "Mapping file",
        type=["xlsx", "xls"],
        accept_multiple_files=False,
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# -----------------------------
# Controls bar (month + options) in one line
# -----------------------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.1, 1.0, 1.2], vertical_alignment="center")
with c1:
    st.markdown("**Output month**")
    chosen_date = st.date_input(
        "Month",
        value=date.today().replace(day=1),
        label_visibility="collapsed",
        help="This month will be written into the template (B1) and the date column.",
    )
    selected_month_str = f"{chosen_date.month:02d}/{chosen_date.year}"

with c2:
    st.markdown("**Options**")
    include_intermediate = st.checkbox(
        "Include intermediate outputs",
        value=False,
        help="Adds cleaned_* and mapped_* files into the ZIP for troubleshooting.",
    )

with c3:
    st.markdown("**Template**")
    st.markdown(f"<span class='chip'>Using built-in template</span>", unsafe_allow_html=True)
    st.markdown(f"<div class='tiny'>Selected month: <b>{selected_month_str}</b></div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# -----------------------------
# Run section
# -----------------------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
r1, r2 = st.columns([1, 1], vertical_alignment="center")
with r1:
    st.markdown("**Run**")
    can_run = bool(platform_files) and (db_file is not None)
    st.markdown(
        f"<span class='chip'>{'Ready to process' if can_run else 'Waiting for files'}</span>",
        unsafe_allow_html=True,
    )
with r2:
    st.markdown("<div class='muted'>Click Process. The ZIP download will appear below.</div>", unsafe_allow_html=True)

process_clicked = st.button(
    "Process",
    type="primary",
    use_container_width=True,
    disabled=not can_run,
)
st.markdown("</div>", unsafe_allow_html=True)

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
    with st.spinner("Processing..."):
        platform_payload = [(f.name, f.getvalue()) for f in platform_files]
        result = run_pipeline_and_zip(
            platform_files=platform_payload,
            db_excel_bytes=db_file.getvalue(),
            template_excel_bytes=TEMPLATE_BYTES,
            include_intermediate=include_intermediate,
            month_str=selected_month_str,
        )
    st.session_state["result_zip"] = result.zip_bytes
    st.session_state["result_summary"] = result.summary

st.write("")

# -----------------------------
# Output
# -----------------------------
if st.session_state["result_zip"]:
    st.success("Done. Your ZIP is ready.")
    st.text(st.session_state["result_summary"])

    st.download_button(
        label="Download results ZIP",
        data=st.session_state["result_zip"],
        file_name="view_reports_outputs.zip",
        mime="application/zip",
        use_container_width=True,
    )
else:
    st.info("Upload files above, choose month, and click **Process**.")

# -----------------------------
# Subtle footer trademark
# -----------------------------
st.markdown(
    """
    <div style="
      margin-top: 24px;
      text-align: center;
      font-size: 0.75rem;
      color: rgba(49,51,63,0.35);
      letter-spacing: 0.02em;">
      © Keshet Data Team
    </div>
    """,
    unsafe_allow_html=True,
)
