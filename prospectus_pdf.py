"""Abraham Education System — Prospectus Studio v2: PDF engine.

Design rules (these are what the v1 portal got wrong, fixed here):

1. FIXED PAGES, NOT FLOWING TEXT. The prospectus is always exactly five
   pages, in the original document's own page order (see content.py).
   Each page is built and *measured* on its own before anything is printed.

2. PAGE-FIT ENGINE. Every page is measured against its A4 frame. If a page
   is too tall at the preferred type size, the engine steps down through
   four levels (smaller type, tighter leading, slightly smaller photos)
   until it fits. The chosen level is reported per page, so a tight page
   is visible instead of silently spilling onto a sixth page — the v1
   fault that left the timings table split across two pages, with two
   orphaned rows alone on an almost-blank page 5.

3. FIXED PHOTO FRAMES. Every photo lives in a fixed millimetre box and is
   centre-cropped to that box (never stretched, never floated to one side,
   never left with a gap beside it). The editor preview shows the exact
   crop the PDF will print. Photos keep their captions, in a caption bar
   under the frame. Small source photos are printed small on purpose so
   they stay as sharp as the original allowed.

4. TABLES STAY TABLES. Fees, timings, weekly and daily schedules are real
   tables with a navy header row. They are never split across pages and
   never re-typed as bullets. The Daily School Routine table, which v1
   dropped entirely, is restored; so is the blank "Admission Charges"
   column, which v1 dropped.

No streamlit import here on purpose: this module is pure reportlab +
Pillow, so it can be tested on its own and reused anywhere.
"""

from __future__ import annotations

import base64
import io
import re
from pathlib import Path

from PIL import Image, ImageOps
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image as RLImage,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from content import default_project, verify_content

# ---------------------------------------------------------------------------
# Page geometry — A4, the standard prospectus size in Pakistan.
# ---------------------------------------------------------------------------

PAGE_W, PAGE_H = A4
MARGIN_L = MARGIN_R = 18 * mm
MARGIN_T = 15 * mm
MARGIN_B = 16 * mm
FRAME_W = PAGE_W - MARGIN_L - MARGIN_R          # 174 mm
FRAME_H = PAGE_H - MARGIN_T - MARGIN_B          # 266 mm
FRAME_X, FRAME_Y = MARGIN_L, MARGIN_B

# Fit levels: (body pt, leading pt, photo scale, table font pt,
# table row padding pt). The engine tries them in order and takes the first
# level at which the whole page fits its frame. Table size is in the levels
# because tables dominate the dense pages — shrinking body text alone
# would barely move them.
LEVELS = [
    (10.2, 14.6, 1.00, 9.2, 4.2),
    (9.8, 14.0, 0.94, 8.9, 3.7),
    (9.4, 13.5, 0.88, 8.6, 3.6),
    (9.0, 13.0, 0.82, 8.3, 3.3),
]
FIT_SAFETY_PT = 6.0  # keep a hair of slack inside the frame


def _hex(code: str) -> colors.HexColor:
    return colors.HexColor(code)


# ---------------------------------------------------------------------------
# Image handling
# ---------------------------------------------------------------------------

def resolve_bytes(ref: str | bytes | None, app_dir: Path,
                  uploads: dict | None = None) -> bytes | None:
    """Turn a project image reference into raw bytes.

    A reference may be a ``data:image/...;base64,`` URI (uploaded in the
    session), a path relative to the project root (``assets/image1.jpeg``),
    or an absolute path. Uploads win over files on disk.
    """
    if ref is None:
        return None
    if isinstance(ref, bytes):
        return ref
    if isinstance(ref, str):
        if not ref.strip():
            return None  # an emptied slot: no photo, not an error
    if isinstance(ref, str) and ref.startswith("data:image/") and "," in ref:
        try:
            return base64.b64decode(ref.split(",", 1)[1])
        except Exception:
            return None
    if uploads and ref in uploads:
        return uploads[ref]
    path = Path(ref)
    if not path.is_absolute():
        path = app_dir / path
    return path.read_bytes() if path.is_file() else None


def _focus_centering(focus: str) -> tuple[float, float]:
    return {
        "centre": (0.5, 0.5),
        "center": (0.5, 0.5),
        "top": (0.5, 0.12),
        "bottom": (0.5, 0.88),
    }.get((focus or "centre").lower(), (0.5, 0.5))


def prepare_image(raw: bytes, w_mm: float, h_mm: float,
                  focus: str = "centre", dpi: int = 200) -> io.BytesIO:
    """Centre-crop ``raw`` to exactly ``w_mm`` x ``h_mm`` (no stretching).

    Returns a JPEG buffer sized for print at ``dpi``. The crop is the whole
    point: a photo that does not match the frame is cropped, never squeezed.
    """
    target_px = (max(8, int(w_mm / 25.4 * dpi)), max(8, int(h_mm / 25.4 * dpi)))
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img = ImageOps.fit(img, target_px, method=Image.LANCZOS,
                       centering=_focus_centering(focus))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=88)
    out.seek(0)
    return out


def render_frame_preview(raw: bytes, w_mm: float, h_mm: float,
                         focus: str = "centre") -> bytes:
    """The exact cropped frame the PDF will print, as JPEG bytes (for the
    editor preview)."""
    return prepare_image(raw, w_mm, h_mm, focus).getvalue()


def photo_report(raw: bytes, w_mm: float) -> dict:
    """Native size and effective print resolution of a photo in its frame."""
    img = Image.open(io.BytesIO(raw))
    width_in = w_mm / 25.4
    dpi = img.size[0] / width_in if width_in else 0
    return {
        "native": f"{img.size[0]} × {img.size[1]} px",
        "print_dpi": round(dpi),
        "sharp": dpi >= 120,
    }


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def _styles(brand: dict, body_pt: float, leading_pt: float,
            table_pt: float = 9.2, table_pad: float = 5.0) -> dict:
    navy = _hex(brand["navy"])
    blue = _hex(brand["blue"])
    gold = _hex(brand["gold"])
    ink = colors.HexColor("#22303F")
    muted = colors.HexColor("#5B6B7A")
    return {
        "navy": navy, "blue": blue, "gold": gold, "ink": ink, "muted": muted,
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=body_pt,
                               leading=leading_pt, textColor=ink, spaceAfter=5),
        "bullet": ParagraphStyle("bullet", fontName="Helvetica",
                                 fontSize=body_pt, leading=leading_pt,
                                 textColor=ink, leftIndent=13,
                                 firstLineIndent=-9, spaceAfter=3.5),
        "numbered": ParagraphStyle("numbered", fontName="Helvetica",
                                   fontSize=body_pt, leading=leading_pt,
                                   textColor=ink, leftIndent=13,
                                   firstLineIndent=-9, spaceAfter=3.5),
        "subhead": ParagraphStyle("subhead", fontName="Helvetica-Bold",
                                  fontSize=body_pt + 0.6, leading=leading_pt + 1,
                                  textColor=blue, spaceBefore=7, spaceAfter=4),
        "bar": ParagraphStyle("bar", fontName="Helvetica-Bold", fontSize=11,
                              leading=14, textColor=colors.white),
        "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=table_pt,
                               leading=table_pt * 1.35, textColor=ink),
        "cell_b": ParagraphStyle("cell_b", fontName="Helvetica-Bold",
                                 fontSize=table_pt, leading=table_pt * 1.35,
                                 textColor=ink),
        "cell_h": ParagraphStyle("cell_h", fontName="Helvetica-Bold",
                                 fontSize=table_pt, leading=table_pt * 1.32,
                                 textColor=colors.white),
        "tpad": table_pad,
        "caption": ParagraphStyle("caption", fontName="Helvetica-Oblique",
                                  fontSize=7.8, leading=10.5, textColor=muted,
                                  alignment=TA_CENTER, spaceBefore=4),
        "note": ParagraphStyle("note", fontName="Helvetica-Oblique",
                               fontSize=8.6, leading=12.2, textColor=muted,
                               spaceAfter=4),
        "quote": ParagraphStyle("quote", fontName="Helvetica-BoldOblique",
                                fontSize=13, leading=18, textColor=blue,
                                alignment=TA_CENTER, spaceBefore=8,
                                spaceAfter=6),
    }


def _esc(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _lead_bold(text: str) -> str:
    """Bold the lead-in of a ``Lead: rest`` item, leave the rest plain."""
    if ": " in text:
        lead, rest = text.split(": ", 1)
        return f"<b>{_esc(lead)}:</b> {_esc(rest)}"
    return _esc(text)


# ---------------------------------------------------------------------------
# Flowable builders
# ---------------------------------------------------------------------------

def _bar(text: str, styles: dict, brand: dict) -> Table:
    t = Table([[Paragraph(_esc(text), styles["bar"])]],
              colWidths=[FRAME_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _hex(brand["navy"])),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _data_table(header: list[str], rows: list[list[str]],
                col_widths_mm: list[float], styles: dict, brand: dict,
                header_style=None) -> Table:
    """A real table: navy header row, alternating body rows, never split."""
    header_style = header_style or styles["cell_h"]
    data = [[Paragraph(_esc(c).replace("\n", "<br/>"), header_style)
             for c in header]]
    for row in rows:
        data.append([
            Paragraph(_esc(c).replace("\n", "<br/>") if c.strip() else "—",
                      styles["cell_b"] if j == 0 else styles["cell"])
            for j, c in enumerate(row)
        ])
    t = Table(data, colWidths=[w * mm for w in col_widths_mm],
              repeatRows=1, hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), _hex(brand["navy"])),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D2DC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F2F5F9")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), styles["tpad"]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), styles["tpad"]),
    ]
    t.setStyle(TableStyle(style))
    return t


def _bullets(items: list[str], styles: dict, numbered: bool = False) -> list:
    out = []
    for i, item in enumerate(items):
        prefix = f"{i + 1}.&nbsp;&nbsp;" if numbered else "•&nbsp;&nbsp;"
        style = styles["numbered"] if numbered else styles["bullet"]
        out.append(Paragraph(prefix + _lead_bold(item), style))
    return out


def _figure(raw: bytes | None, slot: dict, styles: dict,
            scale: float) -> list:
    """One photo in its fixed frame, with its caption bar underneath.

    Returns [] when there is no photo, so a missing file can never leave a
    hole or a broken frame in the page.
    """
    if not raw:
        return []
    w = slot["frame_w_mm"] * scale
    h = slot["frame_h_mm"] * scale
    buf = prepare_image(raw, w, h, slot.get("focus", "centre"))
    img = RLImage(buf, width=w * mm, height=h * mm)
    cell = Table([[img]], colWidths=[w * mm])
    cell.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.7, _hex("#C28A32")),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    parts = [cell]
    if slot.get("caption"):
        parts.append(Paragraph(_esc(slot["caption"]), styles["caption"]))
    return parts


def _side_by_side(left_flowables: list, raw: bytes | None, slot: dict,
                  styles: dict, scale: float) -> Table:
    """Text on the left, one framed photo on the right — the layout the
    original document uses for its Vision/Mission and Environment photos.
    The photo column is a fixed width; the text never wraps under the photo.
    """
    img_w = slot["frame_w_mm"] * scale
    text_w = FRAME_W / mm - img_w - 6
    right = _figure(raw, slot, styles, scale)
    t = Table([[left_flowables, right]],
              colWidths=[text_w * mm, img_w * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 6),
        ("LEFTPADDING", (1, 0), (1, 0), 0),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


# ---------------------------------------------------------------------------
# One page at a time
# ---------------------------------------------------------------------------

def _page_flowables(key: str, project: dict, level: tuple,
                    resolver) -> list:
    body_pt, leading_pt, img_scale, table_pt, table_pad = level
    brand = project["brand"]
    styles = _styles(brand, body_pt, leading_pt, table_pt, table_pad)
    navy = _hex(brand["navy"])
    pages = {p["key"]: p for p in project["pages"]}
    photos = {s["key"]: s for s in project["photos"]}
    body = pages[key]["body"]
    out: list = []

    if key == "cover":
        out.append(Spacer(1, 8 * mm))
        out.append(Paragraph(_esc(brand["address"]).upper(),
                             ParagraphStyle("eyebrow", fontName="Helvetica-Bold",
                                            fontSize=9, leading=12,
                                            textColor=_hex(brand["gold"]),
                                            alignment=TA_CENTER, spaceAfter=6)))
        out.append(Paragraph("ABRAHAM", ParagraphStyle(
            "cover1", fontName="Helvetica-Bold", fontSize=32, leading=34,
            textColor=navy, alignment=TA_CENTER, spaceAfter=1)))
        out.append(Paragraph("EDUCATION SYSTEM", ParagraphStyle(
            "cover2", fontName="Helvetica-Bold", fontSize=25, leading=28,
            textColor=_hex(brand["blue"]), alignment=TA_CENTER, spaceAfter=7)))
        out.append(HRFlowable(width="28%", thickness=2.5,
                              color=_hex(brand["gold"]), hAlign="CENTER",
                              spaceBefore=2, spaceAfter=8))
        out.append(_bar("SCHOOL PROSPECTUS  |  ACADEMIC SESSION 2027–2028",
                        styles, brand))
        out.append(Spacer(1, 6 * mm))
        for line in brand["tagline"].split("\n"):
            out.append(Paragraph(f"<i>{_esc(line)}</i>", ParagraphStyle(
                "tagline", fontName="Helvetica-Oblique", fontSize=13,
                leading=17, textColor=_hex(brand["blue"]),
                alignment=TA_CENTER, spaceAfter=1)))
        out.append(Spacer(1, 5 * mm))
        slot = photos["cover"]
        out.extend(_figure(resolver(slot), slot, styles, img_scale))
        out.append(Spacer(1, 5 * mm))
        out.append(Paragraph(f"<b>{_esc(brand['affiliation'])}</b>",
                             ParagraphStyle("affil", fontName="Helvetica-Bold",
                                            fontSize=9.5, leading=13.5,
                                            textColor=navy, alignment=TA_CENTER,
                                            spaceAfter=5 * mm)))
        strip = Table([[
            Paragraph(f"<b>COMPLETE ADDRESS</b><br/>{_esc(brand['address'])}",
                      styles["cell"]),
            Paragraph(f"<b>CELL NUMBER</b><br/>{_esc(brand['cell'])}",
                      styles["cell"]),
            Paragraph(f"<b>WHATSAPP NUMBER</b><br/>{_esc(brand['whatsapp'])}",
                      styles["cell"]),
        ]], colWidths=[FRAME_W / 3.0] * 3)
        strip.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EAF2FA")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#C9D2DC")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D2DC")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        out.append(strip)
        out.append(Spacer(1, 6 * mm))
        out.append(_bar(body.get("admissions_open",
                                 "Admissions Open  |  Playgroup to Class 10"),
                        styles, brand))
        slack = FRAME_H - 12.0 - _measure(out)
        if slack > 20:
            # out[0] is the top spacer; out[-2] is the spacer above the
            # Admissions bar. Share the slack between them.
            out[0] = Spacer(1, 8 * mm + slack * 0.5)
            out[-2] = Spacer(1, 6 * mm + slack * 0.5)
        return out

    if key == "about":
        out.append(_bar(body["about_heading"], styles, brand))
        out.append(Spacer(1, 3))
        for para in body["about_paras"]:
            out.append(Paragraph(_esc(para), styles["body"]))
        out.append(Spacer(1, 4))
        left = [
            Paragraph(_esc(body["vision_heading"]), styles["subhead"]),
            Paragraph(_esc(body["vision"]), styles["body"]),
            Paragraph(_esc(body["mission_heading"]), styles["subhead"]),
            Paragraph(_esc(body["mission"]), styles["body"]),
        ]
        out.append(_side_by_side(left, resolver(photos["classroom"]),
                                 photos["classroom"], styles, img_scale))
        out.append(Spacer(1, 7))
        out.append(_bar(body["programs_heading"], styles, brand))
        out.append(Spacer(1, 3))
        out.append(Paragraph(_esc(body["programs_intro"]), styles["body"]))
        prog_rows = [[j, s] for j, s in zip(
            body["programs_junior"],
            body["programs_senior"] + [""] * (len(body["programs_junior"])
                                             - len(body["programs_senior"])))]
        out.append(_data_table(["Junior Section", "Senior Section"],
                               prog_rows, [87, 87], styles, brand))
        out.append(Spacer(1, 7))
        out.append(_bar(body["priorities_heading"], styles, brand))
        out.append(Spacer(1, 3))
        out.append(Paragraph(_esc(body["priorities_intro"]), styles["body"]))
        out.extend(_bullets(body["priorities"], styles))
        return _balance_page(out)

    if key == "admissions":
        out.append(_bar(body["environment_heading"], styles, brand))
        out.append(Spacer(1, 3))
        out.append(Paragraph(_esc(body["environment_intro"]), styles["body"]))
        left = [Paragraph("•&nbsp;&nbsp;" + _esc(i), styles["bullet"])
                for i in body["environment_items"]]
        out.append(_side_by_side(left, resolver(photos["teacher"]),
                                 photos["teacher"], styles, img_scale))
        out.append(Spacer(1, 5))
        out.append(_bar(body["commitment_heading"], styles, brand))
        out.append(Spacer(1, 3))
        out.append(Paragraph(_esc(body["commitment_intro"]), styles["body"]))
        out.extend(_bullets(body["commitment_items"], styles))
        out.append(Spacer(1, 5))
        out.append(_bar(body["admission_heading"], styles, brand))
        out.append(Spacer(1, 3))
        out.append(_plain_table(body["admission_rows"], [38, 136], styles))
        out.append(Spacer(1, 3))
        out.append(Paragraph(_esc(body["process_heading"]), styles["subhead"]))
        out.extend(_bullets(body["process_steps"], styles, numbered=True))
        out.append(Spacer(1, 4))
        slot = photos["collaborative"]
        fig = _figure(resolver(slot), slot, styles, img_scale)
        if fig:
            centred = Table([[fig]], colWidths=[FRAME_W])
            centred.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            out.append(centred)
        return _balance_page(out)

    if key == "fees":
        out.append(_bar(body["fee_heading"], styles, brand))
        out.append(Spacer(1, 4))
        out.append(_data_table(body["fee_header"], body["fee_rows"],
                               [62, 48, 64], styles, brand))
        out.append(Spacer(1, 3))
        out.append(Paragraph(f"<i>{_esc(body['fee_note_1'])}</i>",
                             styles["note"]))
        out.append(Paragraph(f"<b>{_esc(body['fee_note_2'])}</b>",
                             ParagraphStyle("note_b", parent=styles["note"],
                                            fontName="Helvetica-Bold",
                                            textColor=styles["ink"])))
        out.append(Spacer(1, 3))
        out.append(_bar(body["timings_heading"], styles, brand))
        out.append(Spacer(1, 3))
        out.append(Paragraph(f"<b>{_esc(body['timings_session'])}</b>",
                             ParagraphStyle("sess", parent=styles["body"],
                                            fontName="Helvetica-Bold",
                                            textColor=navy)))
        out.append(Paragraph(_esc(body["timings_intro"]), styles["body"]))
        out.append(Paragraph(_esc(body["timings_subheading"]),
                             styles["subhead"]))
        out.append(_data_table(body["timings_header"], body["timings_rows"],
                               [62, 56, 56], styles, brand))
        out.append(Spacer(1, 3))
        out.append(Paragraph(_esc(body["weekly_subheading"]),
                             styles["subhead"]))
        out.append(_data_table(body["weekly_header"], body["weekly_rows"],
                               [38, 136], styles, brand))
        out.append(Spacer(1, 3))
        out.append(Paragraph(_esc(body["daily_subheading"]),
                             styles["subhead"]))
        out.append(_data_table(body["daily_header"], body["daily_rows"],
                               [62, 112], styles, brand))
        return _balance_page(out)

    if key == "promise":
        out.append(_bar(body["instructions_heading"], styles, brand))
        out.append(Spacer(1, 3))
        out.extend(_bullets(body["instructions_items"], styles))
        out.append(Paragraph(f"<i>{_esc(body['instructions_note'])}</i>",
                             styles["note"]))
        out.append(Spacer(1, 4))
        duo = Table([[
            _figure(resolver(photos["sports"]), photos["sports"],
                    styles, img_scale),
            _figure(resolver(photos["together"]), photos["together"],
                    styles, img_scale),
        ]], colWidths=[FRAME_W / 2.0, FRAME_W / 2.0])
        duo.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (0, 0), 0),
            ("RIGHTPADDING", (0, 0), (0, 0), 4),
            ("LEFTPADDING", (1, 0), (1, 0), 4),
            ("RIGHTPADDING", (1, 0), (1, 0), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        out.append(duo)
        out.append(Spacer(1, 5))
        out.append(_bar(body["promise_heading"], styles, brand))
        out.append(Spacer(1, 3))
        out.append(Paragraph(_esc(body["promise_para"]), styles["body"]))
        out.append(Paragraph(_esc(body["quote"]), styles["quote"]))
        out.append(_bar(body["banner"], styles, brand))
        out.append(Spacer(1, 5))
        contact = ParagraphStyle("contact", fontName="Helvetica-Bold",
                                 fontSize=10.5, leading=15, textColor=navy,
                                 alignment=TA_CENTER, spaceAfter=2)
        contact2 = ParagraphStyle("contact2", fontName="Helvetica",
                                  fontSize=10, leading=15, textColor=navy,
                                  alignment=TA_CENTER, spaceAfter=2)
        out.append(Paragraph(_esc(brand["address"]), contact))
        out.append(Paragraph(
            f"Cell Number: {_esc(brand['cell'])}&nbsp;&nbsp;&nbsp;&nbsp;"
            f"WhatsApp: {_esc(brand['whatsapp'])}", contact2))
        out.append(Paragraph(f"Email: {_esc(brand['email'])}", contact2))
        return _balance_page(out)

    raise ValueError(f"unknown page key: {key}")


def _plain_table(rows: list[list[str]], col_widths_mm: list[float],
                 styles: dict) -> Table:
    """A two-column key/value table with no header row (the original's
    Admission Information summary)."""
    data = [[Paragraph(_esc(c).replace("\n", "<br/>"),
                       styles["cell_b"] if j == 0 else styles["cell"])
             for j, c in enumerate(row)] for row in rows]
    t = Table(data, colWidths=[w * mm for w in col_widths_mm], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D2DC")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.white, colors.HexColor("#F2F5F9")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), styles["tpad"]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), styles["tpad"]),
    ]))
    return t


# ---------------------------------------------------------------------------
# Measuring + building
# ---------------------------------------------------------------------------

def _measure(flowables: list) -> float:
    """Total height (pt) the flowables need at the frame width.

    Measured with ``wrapOn`` against a throwaway canvas: some flowables
    need a canvas to measure themselves, and a plain ``wrap()`` call
    raises without one.

    Crucially, ``wrap()`` returns the content height WITHOUT the
    flowable's space-before and space-after — Platypus adds those when it
    places the flowable in the frame (see ``Frame._add``). Measuring
    wrap heights alone under-counts by the sum of those spaces (about
    50 pt on the fees page), which is exactly how v1's timings table
    ended up split across two pages. So the spaces are added here: every
    flowable's space-before (except the first on the page, which the
    frame drops) plus every flowable's space-after.
    """
    from reportlab.pdfgen.canvas import Canvas

    canv = Canvas(io.BytesIO(), pagesize=A4)
    total = 0.0
    for i, f in enumerate(flowables):
        _, h = f.wrapOn(canv, FRAME_W, FRAME_H)
        sb = f.getSpaceBefore() if i > 0 else 0.0
        sa = f.getSpaceAfter()
        total += h + sb + sa
    return total


def _balance_page(out: list) -> list:
    """Spread a loose page's leftover space across its section gaps.

    Pages 2 and 5 carry less copy than the frame holds, so they would end
    a third of the way up the page. Rather than shrinking the type or
    inventing content, the slack is shared across the page's existing
    spacers (at most ~24 pt each), so sections sit further apart and the
    page reads as deliberately airy instead of unfinished. Dense pages
    have almost no slack, so they are left untouched. The cover has its
    own centring and never comes through here.
    """
    total = _measure(out)
    slack = FRAME_H - 24.0 - total
    if slack <= 24:
        return out
    spacers = [f for f in out if isinstance(f, Spacer)]
    if not spacers:
        return out
    add_each = min(24.0, slack / len(spacers))
    for f in spacers:
        f.height += add_each
    return out


def check_fit(project: dict, app_dir: Path,
              uploads: dict | None = None) -> list[dict]:
    """Measure every page at each fit level; report the level it fits at.

    A page that needs level 3 is a warning sign (very tight). A page that
    fits at no level is reported with its overflow — it must never be
    printed unchecked.
    """
    # The resolver takes a photo slot dict; _page_flowables calls it with
    # a slot, so keep that contract: resolver(slot) -> bytes.
    resolver = lambda slot: resolve_bytes(  # noqa: E731
        slot.get("file", ""), app_dir, uploads)
    report = []
    for page in project["pages"]:
        chosen = None
        heights = []
        for li, level in enumerate(LEVELS):
            flow = _page_flowables(page["key"], project, level, resolver)
            h = _measure(flow)
            heights.append(round(h, 1))
            if h <= FRAME_H - FIT_SAFETY_PT:
                chosen = {"level": li, "body_pt": level[0],
                          "height_pt": round(h, 1),
                          "overflow_pt": 0.0}
                break
        if chosen is None:
            chosen = {"level": None, "body_pt": LEVELS[-1][0],
                      "height_pt": heights[-1],
                      "overflow_pt": round(heights[-1] - FRAME_H, 1)}
        report.append({
            "page": len(report) + 1,
            "key": page["key"],
            "name": page["name"],
            "fits": chosen["level"] is not None,
            "level": chosen["level"],
            "body_pt": chosen["body_pt"],
            "height_pt": chosen["height_pt"],
            "frame_pt": round(FRAME_H, 1),
            "overflow_pt": chosen["overflow_pt"],
            "tried_heights_pt": heights,
        })
    return report


def build_pdf(project: dict, app_dir: Path,
              uploads: dict | None = None) -> tuple[bytes, list[dict], int]:
    """Build the five-page PDF. Returns (pdf bytes, fit report, page count).

    Raises ValueError if any page cannot be fitted — a broken prospectus
    is never silently produced.
    """
    missing = verify_content(project)
    if missing:
        raise ValueError(
            "Original content is missing from the project: "
            + "; ".join(missing[:8]))
    fit = check_fit(project, app_dir, uploads)
    bad = [r for r in fit if not r["fits"]]
    if bad:
        raise ValueError(
            "Page(s) do not fit even at the smallest type size: "
            + ", ".join(f"page {r['page']} (over by {r['overflow_pt']} pt)"
                        for r in bad)
            + ". Shorten the copy or shrink a photo in the Photos tab.")

    brand = project["brand"]
    resolver = lambda slot: resolve_bytes(  # noqa: E731
        slot.get("file", ""), app_dir, uploads)

    def decorate(canvas, doc):
        canvas.saveState()
        page_no = canvas.getPageNumber()
        if page_no > 1:
            canvas.setFillColor(_hex(brand["gold"]))
            canvas.rect(0, PAGE_H - 2.2 * mm, PAGE_W, 2.2 * mm, fill=1, stroke=0)
            canvas.setFont("Helvetica-Bold", 7.5)
            canvas.setFillColor(_hex(brand["navy"]))
            canvas.drawString(MARGIN_L, PAGE_H - 11 * mm,
                              "ABRAHAM EDUCATION SYSTEM  |  ZAMMAR VALLEY, ISLAMABAD")
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#667085"))
        canvas.drawCentredString(
            PAGE_W / 2, 10 * mm,
            f"{brand['motto']}     |     ACADEMIC SESSION 2027–2028"
            f"     |     PAGE {page_no:02d}")
        canvas.restoreState()

    out = io.BytesIO()
    doc = BaseDocTemplate(
        out, pagesize=A4, leftMargin=MARGIN_L, rightMargin=MARGIN_R,
        topMargin=MARGIN_T, bottomMargin=MARGIN_B,
        title=f"{brand['school_name']} Prospectus 2027–2028",
        author=brand["school_name"])
    frame = Frame(FRAME_X, FRAME_Y, FRAME_W, FRAME_H,
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame],
                                       onPage=decorate)])
    story: list = []
    for i, page in enumerate(project["pages"]):
        if i:
            story.append(PageBreak())
        level = LEVELS[fit[i]["level"]]
        story.extend(_page_flowables(page["key"], project, level, resolver))
    doc.build(story)
    return out.getvalue(), fit, doc.page


def default_app_dir() -> Path:
    return Path(__file__).parent


if __name__ == "__main__":
    pdf, fit, count = build_pdf(default_project(), default_app_dir())
    print(f"pages: {count}")
    for row in fit:
        print(row)
    Path("Abraham_Education_System_Prospectus_2027-2028.pdf").write_bytes(pdf)
    print("wrote Abraham_Education_System_Prospectus_2027-2028.pdf",
          f"{len(pdf)//1024} KB")
