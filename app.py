"""Abraham Education System — Prospectus Studio v2 (Streamlit app).

Edit the 2027–2028 prospectus and export a print-ready five-page PDF.

What is different from v1 (and why the old PDF looked wrong):

* The prospectus keeps the ORIGINAL document's five pages, in the
  original's order. v1 regrouped the content into five different pages,
  which is what pushed the timings table over onto a sixth, almost-blank
  page.
* Every page is measured before it is printed. The Fit Check tab shows,
  per page, whether it fits and at what type size — a page can no longer
  silently spill over.
* Every photo sits in a fixed frame and is centre-cropped to it. The
  Photos tab shows the exact crop the PDF will print — no more small
  photos floating on one side with a gap beside them.
* Fees, timings, weekly and daily schedules are edited as tables and
  printed as tables. Nothing from the original is dropped: the Daily
  School Routine table and the (blank) Admission Charges column are back.
* A content check runs on every export: all passages from the original
  document must still be present, or the PDF is refused with a clear
  list of what is missing.

Deploy: push this folder to GitHub, then import the repo at
share.streamlit.io with main file ``app.py``. No secrets or services.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import mimetypes
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image

from content import PHOTO_SLOTS, default_project, verify_content
from prospectus_pdf import (
    build_pdf,
    check_fit,
    photo_report,
    render_frame_preview,
    resolve_bytes,
)

APP_DIR = Path(__file__).parent
ASSET_DIR = APP_DIR / "assets"

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def _fresh_state():
    st.session_state.project = default_project()
    st.session_state.uploads = {}          # ref -> raw image bytes
    st.session_state.active_page = 0
    st.session_state.fit_report = None
    st.session_state.preview_cache = {}    # cache key -> jpeg bytes
    st.session_state.last_pdf = None
    st.session_state.last_pdf_name = "Abraham_Education_System_Prospectus_2027-2028.pdf"


if "project" not in st.session_state:
    _fresh_state()


def _photo_bytes(slot: dict) -> bytes | None:
    # Image references are relative to the project root (APP_DIR).
    return resolve_bytes(slot.get("file", ""), APP_DIR,
                         st.session_state.uploads)


def _preview(slot: dict) -> bytes | None:
    raw = _photo_bytes(slot)
    if not raw:
        return None
    key = hashlib.md5(
        raw + f"|{slot['frame_w_mm']}x{slot['frame_h_mm']}|"
        f"{slot.get('focus', 'centre')}".encode()).hexdigest()
    if key not in st.session_state.preview_cache:
        st.session_state.preview_cache[key] = render_frame_preview(
            raw, slot["frame_w_mm"], slot["frame_h_mm"],
            slot.get("focus", "centre"))
    return st.session_state.preview_cache[key]


def _lines(text: str) -> list[str]:
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]


def _str_rows(values) -> list[list[str]]:
    """data_editor values -> rows of strings (a cleared cell is '')."""
    return [[("" if v is None else str(v)) for v in row] for row in values]


def _portable(project: dict) -> dict:
    """Project JSON with session-uploaded images embedded (self-contained)."""
    result = json.loads(json.dumps(project, ensure_ascii=False))
    for slot in result.get("photos", []):
        ref = slot.get("file", "")
        raw = st.session_state.uploads.get(ref)
        if raw:
            mime = mimetypes.guess_type(ref)[0] or "image/jpeg"
            slot["file"] = ("data:" + mime + ";base64,"
                            + base64.b64encode(raw).decode("ascii"))
    return result


def _load_portable(data: dict):
    project = json.loads(json.dumps(data, ensure_ascii=False))
    uploads = {}
    for slot in project.get("photos", []):
        ref = slot.get("file", "")
        if isinstance(ref, str) and ref.startswith("data:image/"):
            raw = resolve_bytes(ref, APP_DIR, {})
            if raw is not None:
                new_ref = f"uploads/{slot['key']}_restored.jpg"
                uploads[new_ref] = raw
                slot["file"] = new_ref
    st.session_state.project = project
    st.session_state.uploads = uploads
    st.session_state.active_page = 0
    st.session_state.fit_report = None
    st.session_state.last_pdf = None


P = st.session_state.project
BRAND = P["brand"]

# ---------------------------------------------------------------------------
# Page chrome
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Prospectus Studio | Abraham Education System",
                   page_icon="✦", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown(
    """<style>
    [data-testid='stSidebar']{background:#123B70}
    [data-testid='stSidebar'] *{color:#f5f7fa}
    .hero{background:linear-gradient(125deg,#123B70 0%,#1E5A99 62%,#2a6cb0 100%);
      padding:26px 32px;border-radius:18px;color:white;margin-bottom:20px;
      box-shadow:0 14px 34px #123b7022;position:relative;overflow:hidden}
    .hero:after{content:'✦';position:absolute;right:32px;top:-46px;font-size:170px;color:#ffffff12}
    .eyebrow{text-transform:uppercase;letter-spacing:.18em;font-size:10px;color:#e8c87a;font-weight:700}
    .hero h1{color:white;font-family:Georgia,serif;font-size:32px;margin:6px 0 4px}
    .hero p{color:#dce7f1;margin:0;font-size:14px}
    .pill{display:inline-block;border:1px solid #ffffff44;border-radius:30px;
      padding:5px 11px;margin-top:14px;font-size:11px;color:#fff}
    .card{background:#fff;border:1px solid #e9edf1;border-radius:14px;
      padding:16px 18px;box-shadow:0 8px 22px #0d263b0b}
    .page-heading{font-family:Georgia,serif;color:#123B70;font-size:25px;font-weight:700}
    .small-muted{color:#748294;font-size:12px}
    .warn{background:#FFF7E6;border:1px solid #F0D9A0;border-radius:12px;padding:12px 14px}
    .ok{background:#EDF7EE;border:1px solid #BFE3C2;border-radius:12px;padding:12px 14px}
    </style>""",
    unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### ✦ Prospectus Studio")
    st.caption("ABRAHAM EDUCATION SYSTEM  •  2027–2028")
    st.markdown("---")
    st.markdown("**The five pages — as in your original document**")
    fit = st.session_state.fit_report
    for i, page in enumerate(P["pages"]):
        badge = ""
        if fit:
            row = fit[i]
            badge = "  ✓ fits" if row["fits"] else "  ⚠ overflows"
        if st.button(f"{i + 1:02d}  ·  {page['name']}{badge}",
                     key=f"nav_{i}", width="stretch",
                     type="primary" if st.session_state.active_page == i
                     else "secondary"):
            st.session_state.active_page = i
            st.rerun()
    st.markdown("---")
    st.markdown("**Project files**")
    uploaded_json = st.file_uploader("Open a saved project", type=["json"],
                                     key="json_open")
    if uploaded_json:
        try:
            _load_portable(json.load(uploaded_json))
            st.success("Project loaded")
            st.rerun()
        except Exception as exc:  # noqa: BLE001 - show the user the cause
            st.error(f"Could not read project: {exc}")
    st.download_button(
        "↓  Save project (.json)",
        data=json.dumps(_portable(P), ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="abraham-prospectus-project-v2.json",
        mime="application/json", width="stretch")
    if st.button("↺  Restore original content", width="stretch"):
        _fresh_state()
        st.rerun()
    st.markdown("---")
    st.caption("Content is the original Word prospectus, word for word. "
               "Nothing is sent anywhere — the PDF is built in this app.")

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

st.markdown(
    "<div class='hero'><div class='eyebrow'>A thoughtful start to a brighter future</div>"
    "<h1>Prospectus Studio</h1>"
    "<p>Edit your school prospectus, place its photos properly, and export a "
    "print-ready PDF — five pages, every page complete.</p>"
    "<span class='pill'>2027 — 2028 &nbsp;·&nbsp; EDITABLE MASTER &nbsp;·&nbsp; v2</span></div>",
    unsafe_allow_html=True)

editor_tab, photos_tab, design_tab, export_tab = st.tabs(
    ["✎  Content editor", "🖼  Photos — fixed frames", "◈  Brand & design",
     "▧  Fit check & export"])

idx = st.session_state.active_page
page = P["pages"][idx]
body = page["body"]

# ---------------------------------------------------------------------------
# Tab 1 — Content editor (structured: tables stay tables)
# ---------------------------------------------------------------------------

with editor_tab:
    st.markdown(
        f"<div class='page-heading'>{idx + 1:02d} / 05 &nbsp;·&nbsp; {page['name']}</div>"
        "<div class='small-muted'>Page order and headings follow your original "
        "document. Edit the words — the layout, page breaks and tables stay put.</div>",
        unsafe_allow_html=True)
    st.markdown("")

    if idx == 0:
        BRAND["tagline"] = st.text_area(
            "Tagline (one line per line)", BRAND["tagline"], height=68,
            help="Shown under the school name on the cover.")
        body["admissions_open"] = st.text_input(
            "Admissions line (bottom of the cover)",
            body["admissions_open"])
        st.info("The cover photo, affiliation line and address strip are set "
                "in the Photos and Brand tabs. The cover always stays one page.")

    elif idx == 1:
        body["about_heading"] = st.text_input("Section heading", body["about_heading"])
        for n, para in enumerate(body["about_paras"]):
            body["about_paras"][n] = st.text_area(
                f"About paragraph {n + 1}", para, height=80, key=f"about_p{n}")
        c1, c2 = st.columns(2)
        with c1:
            body["vision_heading"] = st.text_input("Vision heading", body["vision_heading"])
            body["vision"] = st.text_area("Vision", body["vision"], height=90)
        with c2:
            body["mission_heading"] = st.text_input("Mission heading", body["mission_heading"])
            body["mission"] = st.text_area("Mission", body["mission"], height=90)
        st.markdown("#### Academic Programs")
        c1, c2 = st.columns(2)
        with c1:
            body["programs_junior"] = _lines(st.text_area(
                "Junior Section (one class per line)",
                "\n".join(body["programs_junior"]), height=90))
        with c2:
            body["programs_senior"] = _lines(st.text_area(
                "Senior Section (one class per line)",
                "\n".join(body["programs_senior"]), height=90))
        body["priorities_heading"] = st.text_input(
            "Priorities heading", body["priorities_heading"])
        body["priorities_intro"] = st.text_input(
            "Priorities introduction", body["priorities_intro"])
        body["priorities"] = _lines(st.text_area(
            "Educational priorities — one per line, as “Lead: description”",
            "\n".join(body["priorities"]), height=180))

    elif idx == 2:
        body["environment_heading"] = st.text_input(
            "Section heading", body["environment_heading"])
        body["environment_intro"] = st.text_input(
            "Introduction", body["environment_intro"])
        body["environment_items"] = _lines(st.text_area(
            "Learning environment — one point per line",
            "\n".join(body["environment_items"]), height=120))
        body["commitment_heading"] = st.text_input(
            "Commitment heading", body["commitment_heading"])
        body["commitment_intro"] = st.text_area(
            "Commitment introduction", body["commitment_intro"], height=70)
        body["commitment_items"] = _lines(st.text_area(
            "Commitment to parents — one point per line",
            "\n".join(body["commitment_items"]), height=120))
        body["admission_heading"] = st.text_input(
            "Admission heading", body["admission_heading"])
        st.markdown("#### Admission summary table")
        df = pd.DataFrame(body["admission_rows"],
                          columns=["Item", "Detail"])
        edited = st.data_editor(df, width="stretch", num_rows="dynamic",
                                key="admission_rows")
        body["admission_rows"] = _str_rows(edited.values.tolist())
        body["process_heading"] = st.text_input(
            "Process heading", body["process_heading"])
        body["process_steps"] = _lines(st.text_area(
            "Admission process — one step per line, in order",
            "\n".join(body["process_steps"]), height=120))

    elif idx == 3:
        body["fee_heading"] = st.text_input("Fee heading", body["fee_heading"])
        st.markdown("#### Fee table")
        st.caption("The Admission Charges column is blank in your original — "
                   "fill it in here if the school has fixed those charges, "
                   "or leave it blank and it will print blank, as before.")
        df = pd.DataFrame([body["fee_header"]] + body["fee_rows"],
                          columns=["Class", "Monthly Tuition Fee (Rs.)",
                                   "Admission Charges"])
        edited = st.data_editor(df, width="stretch", num_rows="dynamic",
                                key="fee_table")
        vals = _str_rows(edited.values.tolist())
        if vals:
            body["fee_header"] = vals[0]
            body["fee_rows"] = vals[1:]
        body["fee_note_1"] = st.text_area("Fee note 1", body["fee_note_1"], height=70)
        body["fee_note_2"] = st.text_area("Fee note 2", body["fee_note_2"], height=60)
        body["timings_heading"] = st.text_input(
            "Timings heading", body["timings_heading"])
        body["timings_session"] = st.text_input(
            "Session line", body["timings_session"])
        body["timings_intro"] = st.text_area(
            "Timings introduction", body["timings_intro"], height=80)
        st.markdown("#### School Timings table")
        df = pd.DataFrame(body["timings_rows"], columns=body["timings_header"])
        edited = st.data_editor(df, width="stretch", num_rows="dynamic",
                                key="timings_table")
        body["timings_rows"] = _str_rows(edited.values.tolist())
        st.markdown("#### Weekly Academic Schedule table")
        df = pd.DataFrame(body["weekly_rows"], columns=body["weekly_header"])
        edited = st.data_editor(df, width="stretch", num_rows="dynamic",
                                key="weekly_table")
        body["weekly_rows"] = _str_rows(edited.values.tolist())
        st.markdown("#### Daily School Routine table")
        df = pd.DataFrame(body["daily_rows"], columns=body["daily_header"])
        edited = st.data_editor(df, width="stretch", num_rows="dynamic",
                                key="daily_table")
        body["daily_rows"] = _str_rows(edited.values.tolist())

    elif idx == 4:
        body["instructions_heading"] = st.text_input(
            "Section heading", body["instructions_heading"])
        body["instructions_items"] = _lines(st.text_area(
            "Instructions for parents — one per line",
            "\n".join(body["instructions_items"]), height=130))
        body["instructions_note"] = st.text_area(
            "Closing note", body["instructions_note"], height=70)
        body["promise_heading"] = st.text_input(
            "Promise heading", body["promise_heading"])
        body["promise_para"] = st.text_area(
            "Our Promise", body["promise_para"], height=90)
        body["quote"] = st.text_input("Quote", body["quote"])
        body["banner"] = st.text_input("Admissions banner", body["banner"])
        st.info("The two photos on this page and the contact lines at the "
                "bottom are set in the Photos and Brand tabs.")

# ---------------------------------------------------------------------------
# Tab 2 — Photos: fixed frames, exact-crop previews
# ---------------------------------------------------------------------------

with photos_tab:
    st.markdown(
        "<div class='page-heading'>Photos — fixed frames</div>"
        "<div class='small-muted'>Each photo is printed in a fixed-size frame "
        "and cropped to fit it — never stretched, never floating. What you see "
        "below is exactly what the PDF prints, at the exact size.</div>",
        unsafe_allow_html=True)
    st.markdown("")
    for slot in P["photos"]:
        raw = _photo_bytes(slot)
        with st.expander(
                f"Page {slot['page']}  ·  {slot['label']}  —  "
                f"frame {slot['frame_w_mm']:.0f} × {slot['frame_h_mm']:.0f} mm",
                expanded=(slot["page"] == idx + 1)):
            c1, c2 = st.columns([0.9, 1.1], gap="large")
            with c1:
                preview = _preview(slot)
                if preview:
                    st.image(preview, width="stretch",
                             caption="Exact frame as printed (cropped, not stretched)")
                else:
                    st.warning("No photo found for this slot.")
                if raw:
                    rep = photo_report(raw, slot["frame_w_mm"])
                    st.caption(f"Original file: {rep['native']}  ·  "
                               f"prints at about {rep['print_dpi']} dpi")
                    if not rep["sharp"]:
                        st.warning("Small file — printed small on purpose so it "
                                   "stays sharp. For best print quality, replace "
                                   "it with a photo at least 1200 px wide.")
            with c2:
                st.caption(slot.get("note", ""))
                slot["focus"] = st.selectbox(
                    "Crop focus — which part of the photo to keep",
                    ["centre", "top", "bottom"], index=["centre", "top", "bottom"].index(
                        slot.get("focus", "centre")),
                    key=f"focus_{slot['key']}",
                    help="“Top” keeps the top of the picture — use it when a "
                         "photo carries text or faces near the top.")
                slot["caption"] = st.text_input(
                    "Caption under the photo", slot.get("caption", ""),
                    key=f"caption_{slot['key']}")
                replacement = st.file_uploader(
                    "Replace with a photo from your device",
                    type=["png", "jpg", "jpeg", "webp"],
                    key=f"photo_{slot['key']}")
                if replacement:
                    ref = f"uploads/{slot['key']}_{replacement.name}"
                    st.session_state.uploads[ref] = replacement.getvalue()
                    slot["file"] = ref
                    st.session_state.preview_cache.clear()
                    st.success("Photo replaced for this session — save the "
                               "project JSON to keep it.")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Restore original photo",
                                 key=f"restore_{slot['key']}"):
                        orig = next(s for s in PHOTO_SLOTS
                                    if s["key"] == slot["key"])
                        slot["file"] = orig["file"]
                        slot["focus"] = orig["focus"]
                        slot["caption"] = orig["caption"]
                        st.session_state.preview_cache.clear()
                        st.rerun()
                with col_b:
                    if st.button("Remove photo from this slot",
                                 key=f"remove_{slot['key']}"):
                        slot["file"] = ""
                        st.rerun()
    st.markdown("")
    st.markdown(
        "<div class='warn'><b>A note on the photos themselves.</b> The pictures "
        "in your original document are illustrative stock photos, not photos of "
        "Abraham Education System — the cover photo even shows another school's "
        "name. They are kept here because they came with your file, and the "
        "captions say so where your original said so. For the final printed "
        "prospectus, replace them with real photos of your own campus, "
        "classrooms and students.</div>",
        unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Tab 3 — Brand & design
# ---------------------------------------------------------------------------

with design_tab:
    st.markdown(
        "<div class='page-heading'>Your visual identity</div>"
        "<div class='small-muted'>Set the school details and colours once; "
        "they flow through all five pages and the cover.</div>",
        unsafe_allow_html=True)
    st.markdown("")
    c1, c2 = st.columns(2)
    with c1:
        BRAND["school_name"] = st.text_input("School / institution name",
                                             BRAND["school_name"])
        BRAND["address"] = st.text_input("Address", BRAND["address"])
        BRAND["affiliation"] = st.text_area("Affiliation line (cover)",
                                            BRAND["affiliation"], height=70)
    with c2:
        BRAND["session"] = st.text_input("Academic session", BRAND["session"])
        BRAND["motto"] = st.text_input("Footer motto", BRAND["motto"])
    st.markdown("#### Contact details — fill these in before printing")
    st.caption("They are blank lines in your original document. Nothing has "
               "been invented; the PDF prints exactly what you enter here.")
    c1, c2, c3 = st.columns(3)
    BRAND["cell"] = c1.text_input("Cell number", BRAND["cell"])
    BRAND["whatsapp"] = c2.text_input("WhatsApp number", BRAND["whatsapp"])
    BRAND["email"] = c3.text_input("Email", BRAND["email"])
    st.markdown("#### Colours")
    c1, c2, c3 = st.columns(3)
    BRAND["navy"] = c1.color_picker("Main navy (headings, bars)", BRAND["navy"])
    BRAND["blue"] = c2.color_picker("Blue (subheadings, tagline)", BRAND["blue"])
    BRAND["gold"] = c3.color_picker("Gold (rules, photo frames)", BRAND["gold"])
    st.markdown(
        f"<div class='card'><span style='color:{BRAND['gold']};font-size:11px;"
        f"letter-spacing:.15em'>BRAND PREVIEW</span>"
        f"<h2 style='color:{BRAND['navy']};font-family:Georgia,serif'>"
        f"{BRAND['school_name']}</h2>"
        f"<p style='color:{BRAND['blue']};font-style:italic'>"
        f"{BRAND['tagline'].replace(chr(10), '<br/>')}</p>"
        f"<p style='color:#5B6B7A'>{BRAND['address']}  ·  {BRAND['session']}</p></div>",
        unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Tab 4 — Fit check & export
# ---------------------------------------------------------------------------

with export_tab:
    st.markdown(
        "<div class='page-heading'>Fit check & export</div>"
        "<div class='small-muted'>First check that every page fits, then "
        "generate the PDF. A page that does not fit is never printed "
        "unchecked.</div>",
        unsafe_allow_html=True)
    st.markdown("")

    # Standing warnings from the original document
    fee_blank = all(not c.strip() for row in
                    P["pages"][3]["body"]["fee_rows"] for c in row[2:])
    contact_blank = ("____" in BRAND["cell"] or "____" in BRAND["whatsapp"]
                     or "____" in BRAND["email"])
    warnings = []
    if fee_blank:
        warnings.append("The Admission Charges column is still blank (it was "
                        "blank in your original). Fill it in on page 4, or it "
                        "will print blank.")
    if contact_blank:
        warnings.append("Cell / WhatsApp / Email are still blank lines. Fill "
                        "them in under Brand & design before printing.")
    if warnings:
        st.markdown("<div class='warn'>" + "<br/>".join("• " + w for w in warnings)
                    + "</div>", unsafe_allow_html=True)
        st.markdown("")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("①  Check page fit", type="primary", width="stretch"):
            with st.spinner("Measuring all five pages…"):
                st.session_state.fit_report = check_fit(
                    P, APP_DIR, st.session_state.uploads)
            st.rerun()
    with c2:
        if st.button("②  Generate prospectus PDF", width="stretch"):
            with st.spinner("Building the five-page PDF…"):
                try:
                    pdf, fit, count = build_pdf(
                        P, APP_DIR, st.session_state.uploads)
                    st.session_state.fit_report = fit
                    st.session_state.last_pdf = pdf
                except ValueError as exc:
                    st.error(str(exc))
                    st.session_state.last_pdf = None
            st.rerun()

    fit = st.session_state.fit_report
    if fit:
        st.markdown("#### Page fit — every page must fit its own frame")
        rows = []
        for r in fit:
            rows.append({
                "Page": f"{r['page']} — {r['name']}",
                "Fits?": "✓ Fits" if r["fits"] else "✗ Overflows",
                "Type size used": (f"{r['body_pt']} pt (level {r['level'] + 1} of 4)"
                                   if r["level"] is not None else "—"),
                "Height used": f"{r['height_pt']} / {r['frame_pt']} pt",
                "Over by": (f"{r['overflow_pt']} pt" if r["overflow_pt"] else "—"),
            })
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        if all(r["fits"] for r in fit):
            st.markdown("<div class='ok'>✓ All five pages fit — each page is "
                        "complete on its own page, with nothing carried over "
                        "to the next.</div>", unsafe_allow_html=True)
        else:
            st.error("A page overflows. Shorten its copy a little, or shrink "
                     "a photo in the Photos tab, then check again.")
        st.markdown("")

    missing = verify_content(P)
    if missing:
        st.error("Content check: the following passages from your original "
                 "document are missing after editing — restore them before "
                 "exporting:\n\n• " + "\n• ".join(missing[:12]))
    else:
        st.markdown("<div class='ok'>✓ Content check: every passage from your "
                    "original document is present — nothing added, nothing "
                    "lost.</div>", unsafe_allow_html=True)
    st.markdown("")

    if st.session_state.last_pdf:
        st.download_button(
            "↓  Download prospectus PDF (5 pages, A4)",
            data=st.session_state.last_pdf,
            file_name="Abraham_Education_System_Prospectus_2027-2028.pdf",
            mime="application/pdf", type="primary", width="stretch")
        st.caption("Print at 100% on A4. The PDF is built from the current "
                   "content, photos and brand settings above.")
    else:
        st.caption("Press “Generate prospectus PDF” to build the file, then "
                   "download it here.")

st.markdown(
    '<div style="text-align:center;color:#8793a0;font-size:11px;padding:22px 0 5px">'
    "ABRAHAM EDUCATION SYSTEM  ·  PROSPECTUS STUDIO v2  ·  FIVE PAGES, EVERY PAGE COMPLETE"
    "</div>", unsafe_allow_html=True)
