# Abraham Education System — Prospectus Studio v2

A ready-to-deploy Streamlit app for editing the Abraham Education System
2027–2028 school prospectus and exporting a branded, print-ready PDF.
The starter copy and six photographs come from the supplied Word prospectus
(`Abraham_Education_System_Prospectus_2027-2028_Editable_5_Pages.docx`).

## What was wrong with v1 — and what v2 fixes

The first portal produced a **6-page** PDF from a 5-page prospectus, with the
School Timings table split across pages 4 and 5 — two orphaned rows alone
on an almost-blank page. Its photos floated small on the right with a large
empty gap beside them, one photo was never used at all, and two pieces of
content were silently dropped (the Daily School Routine table and the
Admission Charges column).

v2 is rebuilt around three rules:

1. **Fixed pages, not flowing text.** The prospectus is always exactly
   five pages, in the original document's own page order and page breaks.
   Each page is built and measured on its own before anything is printed.
2. **A page-fit engine.** Every page is measured against its A4 frame. If
   a page is too tall at the preferred type size, the engine steps down
   through four levels (smaller type, tighter leading, slightly smaller
   photos) until it fits, and reports the level used per page. A page can
   no longer silently spill onto a sixth page — the Fit Check tab shows
   every page's status before you export.
3. **Fixed photo frames.** Every photo sits in a fixed millimetre frame
   and is centre-cropped to it — never stretched, never floated, never
   leaving a gap. The Photos tab shows the exact crop the PDF will print.
   Small source photos are printed small on purpose so they stay sharp.
   The photo carrying text across its top is cropped from the bottom only,
   so its wording is never cut off.

Content is kept word for word from the original. A content check runs on
every export: all passages from the original must still be present, or the
PDF is refused with a clear list of what is missing.

## The five pages (as in the original document)

| Page | Contents |
| --- | --- |
| 1 | Cover — school name, prospectus line, tagline, campus hero photo, FBISE affiliation, address / cell / WhatsApp strip, Admissions Open |
| 2 | 1. About Us · 2. Our Vision · 3. Our Mission (with classroom photo) · 4. Academic Programs · 5. Our Educational Priorities |
| 3 | 6. Our Learning Environment (with teacher photo) · 7. Our Commitment to Parents · 8. Admission Information · Admission Process · collaborative classroom photo |
| 4 | Fee Structure · 9. School Timings & Weekly Schedule — Timings, Weekly Academic Schedule, and Daily School Routine tables |
| 5 | Important Instructions for Parents · two photos side by side · 9. Our Promise · quote · Admissions Open banner · contact lines |

## Run on your computer

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository (public or private) and upload/push this
   entire project, including `app.py`, `prospectus_pdf.py`, `content.py`,
   `requirements.txt`, `.streamlit/config.toml`, and the `assets/` directory.
2. Open [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
3. Choose **Create app**, select the repository and branch, and set the main
   file path to `app.py`.
4. Deploy. Streamlit Cloud installs dependencies from `requirements.txt`
   automatically.

No secrets, API keys, database, or external services are required. Keep the
repository's `assets/` folder intact; it contains the images used by the
initial prospectus. If using a private repository, authorize Streamlit Cloud
to access it.

## Working with the editor

- **Content editor** — choose a page in the left sidebar. Text is edited
  in place; fees, timings, weekly and daily schedules are edited as
  tables, so they print as tables. Page order, headings and page breaks
  never move.
- **Photos — fixed frames** — each slot shows the exact cropped frame the
  PDF will print, at its exact size. Replace a photo, change its crop
  focus (Centre / Top / Bottom), or edit its caption. “Top” keeps the top
  of a picture — use it for photos carrying text near the top.
- **Brand & design** — school name, address, affiliation, session, motto,
  contact details and the navy / blue / gold colours.
- **Fit check & export** — press **Check page fit** to measure all five
  pages, then **Generate prospectus PDF**. The app also runs a content
  check (every original passage present?) and warns about anything still
  blank. Use **Save project (.json)** for a portable backup that includes
  any photos you uploaded; **Open a saved project** resumes it later.

Streamlit Cloud sessions are ephemeral: the app does not save changes to
GitHub automatically. Download a JSON project backup after important edits.

## Content notes — read before printing

- **Content is unchanged from the original Word file.** Two typing
  artefacts in the source were cleaned to what they plainly meant: a
  literal `\n` typed inside the tagline and the cover address box is
  rendered as a real line break, and `Admission Charges\(New admission,`
  is rendered as `Admission Charges (New admission,`.
- **The Admission Charges column is blank in the original**, so its cells
  print blank. Fill the figures in on page 4 of the editor if the school
  has fixed them.
- **Cell / WhatsApp / Email are blank lines in the original.** Fill them
  in under Brand & design. No number or address has been invented.
- **The original numbers two sections “9.”** (“9. School Timings &
  Weekly Schedule” and “9. Our Promise”). That numbering is kept as-is;
  renumber in the editor if the school prefers.
- **The photos are illustrative stock photos, not photos of Abraham
  Education System** — the cover photo even shows another school's name.
  They are kept because they came with the source file, and the captions
  say so where the original said so. For the final printed prospectus,
  replace them with real photos of your own campus, classrooms and
  students. Images 2–5 are small files (148–217 px), so they are printed
  small on purpose; replace them with photos at least 1200 px wide for
  the sharpest print.
- Confirm fee amounts, affiliation wording, dates and all school details
  with the administration before printing or distributing.

## Repository layout

```text
app.py                    Streamlit editor (UI only)
prospectus_pdf.py         PDF engine: fixed pages, fit engine, photo frames
content.py                The prospectus content, verbatim from the original
requirements.txt          Runtime dependencies
.streamlit/config.toml    App theme and server configuration
assets/                   The six images from the original Word prospectus
README.md                 Setup, usage and deployment instructions
.gitignore                Local Python/cache exclusions
```
