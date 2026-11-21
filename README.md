# Abraham Education System — Prospectus Studio

A ready-to-deploy Streamlit app for editing the Abraham Education System 2027–2028 school prospectus and exporting a branded PDF. The starter copy and six photographs are sourced from the supplied Word prospectus.

## What it does

- Edit five prospectus sections: cover, school overview, learning experience, admissions/fees, and school life/contact.
- Change page titles, labels, body copy, captions, and per-page photos.
- Use Markdown-like headings, bold/italic text, lists, quotes, and pipe-delimited tables in the content editor.
- Set school name, accent and text colors, typeface, text sizes, and upload an official logo.
- Export a print-ready PDF or save/reopen a portable JSON project. Uploaded pictures and logos are embedded in project JSON backups.
- Start with the original source document's copy and embedded images in `assets/`.

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

1. Create a GitHub repository (public or private) and upload/push this entire project, including `app.py`, `requirements.txt`, `.streamlit/config.toml`, and the `assets/` directory.
2. Open [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
3. Choose **Create app**, select the repository and branch, and set the main file path to `app.py`.
4. Deploy. Streamlit Cloud installs dependencies from `requirements.txt` automatically.

No secrets, API keys, database, or external services are required. Keep the repository's `assets/` folder intact; it contains the images used by the initial prospectus. If using a private repository, authorize Streamlit Cloud to access it.

## Working with the editor

Choose a section in the left sidebar. Edit its heading, subtitle, text, and photo. In **Brand & design**, set the school name, PDF colors, fonts and sizes, and optionally upload the school's official logo. **Preview & export** builds the PDF using the current in-session project state. Use **Save project (.json)** to make a portable backup; use **Open a saved project** to resume it in a later session.

For structured content, enter one Markdown-style paragraph per line. Start headings with `##`, bullets with `- `, numbered steps with `1. `, bold words with `**words**`, italic words with `*words*`, and table rows with `|` separators. In table syntax, the separator line can be `| --- | --- |`.

## Deployment caveats

- Streamlit Community Cloud is suitable for a small team and offers an ephemeral app session. Download a JSON project backup after important edits; the app does not save changes to GitHub automatically.
- The original document has no separate logo asset, so a typographic school name is used. Upload the official logo in the design panel.
- The provided school contact fields are blank in the source. Fill the correct phone, WhatsApp, and email details before publishing a final prospectus.
- Confirm fee amounts, affiliation wording, dates, and all school details with the administration before printing or distributing.
- Images from the supplied document may be illustrative. Replace them with current, school-owned photos where appropriate.

## Repository layout

```text
app.py                    Streamlit editor and PDF generator
requirements.txt          Runtime dependencies
.streamlit/config.toml    App theme and server configuration
assets/                   Images extracted from the provided Word prospectus
README.md                 Setup, usage and deployment instructions
.gitignore                Local Python/cache exclusions
```
