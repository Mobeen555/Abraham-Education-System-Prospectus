"""Abraham Education System — Prospectus Studio v2: content model.

Every word below is transcribed verbatim from the original Word prospectus
``Abraham_Education_System_Prospectus_2027-2028_Editable_5_Pages.docx``
(5 pages, Letter). Nothing has been added, removed or reworded — except two
typing artefacts in the source file, cleaned to what they plainly meant:

* the tagline and the cover address box contain a literal ``\\n`` typed in the
  text (``Building Knowledge. Developing Character.\\nPreparing for the
  Future.``) — rendered here as a real line break;
* the fee-table header reads ``Admission Charges\\(New admission,``
  in the source — rendered as ``Admission Charges (New admission,``.

Two facts from the original are kept exactly as they are, blanks included:

* the "Admission Charges" column is blank in the original — the cells stay
  blank until the school fills them in (the editor warns about this);
* Cell / WhatsApp / Email are blank lines in the original — they stay blank
  until the school fills them in. No number or address has been invented.

Page order follows the original document's own page breaks, not a regrouping:

  Page 1  Cover
  Page 2  1. About Us · 2. Our Vision · 3. Our Mission · 4. Academic Programs
          · 5. Our Educational Priorities
  Page 3  6. Our Learning Environment · 7. Our Commitment to Parents
          · 8. Admission Information · Admission Process (+ photo)
  Page 4  Fee Structure · 9. School Timings & Weekly Schedule
          (Timings table · Weekly Academic Schedule · Daily School Routine)
  Page 5  Important Instructions for Parents · (two photos) · 9. Our Promise
          · Admissions Open banner + contact lines

Note the original numbers two different sections "9." — that numbering is
kept as-is. See README.md "Content notes".
"""

from __future__ import annotations

import copy

# ---------------------------------------------------------------------------
# Brand / school details (editable in the portal's Brand tab)
# ---------------------------------------------------------------------------

BRAND = {
    "school_name": "Abraham Education System",
    "short_name": "ABRAHAM EDUCATION SYSTEM",
    "tagline": "Building Knowledge. Developing Character.\nPreparing for the Future.",
    "session": "ACADEMIC SESSION 2027–2028",
    "address": "Zammar Valley, Islamabad",
    "affiliation": (
        "AFFILIATED WITH THE FEDERAL BOARD OF INTERMEDIATE AND "
        "SECONDARY EDUCATION (FBISE)"
    ),
    "motto": "LEARN  •  GROW  •  EXCEL",
    # Colours are the original document's own palette (navy #123B70,
    # blue #1E5A99) plus a restrained gold rule, matching the school website.
    "navy": "#123B70",
    "blue": "#1E5A99",
    "gold": "#C28A32",
    # Contact lines are blank in the original. Fill them in the portal
    # before printing a final prospectus — nothing is invented here.
    "cell": "____________________",
    "whatsapp": "____________________",
    "email": "______________________________",
}

# ---------------------------------------------------------------------------
# Photos — one fixed slot per picture in the original document.
#
# frame_w_mm / frame_h_mm is the exact box the photo is printed in.
# The photo is centre-cropped to that box (never stretched, never floated),
# so what the editor preview shows is exactly what the PDF prints.
# focus: "centre" crops evenly; "top" keeps the top of the picture
# (used for image6, which carries text across its top).
# ---------------------------------------------------------------------------

PHOTO_SLOTS = [
    {
        "key": "cover",
        "label": "Cover — campus hero",
        "file": "assets/image1.jpeg",
        "page": 1,
        "frame_w_mm": 174.0,
        "frame_h_mm": 97.9,  # 16:9, the picture's own ratio — no crop at all
        "focus": "centre",
        "caption": "",
        "note": "Full-width hero. 960 × 540 px — good for this size.",
    },
    {
        "key": "classroom",
        "label": "Page 2 — Classroom learning",
        "file": "assets/image2.jpg",
        "page": 2,
        "frame_w_mm": 54.0,
        "frame_h_mm": 40.5,  # 4:3
        "focus": "centre",
        "caption": "Classroom learning",
        "note": "Small file from the original (172 × 150 px), so it is printed "
                "small on purpose — the same size as in the original document.",
    },
    {
        "key": "teacher",
        "label": "Page 3 — Teacher-guided learning",
        "file": "assets/image3.jpg",
        "page": 3,
        "frame_w_mm": 54.0,
        "frame_h_mm": 40.5,  # 4:3
        "focus": "centre",
        "caption": "Teacher-guided learning",
        "note": "Small file from the original (148 × 153 px), so it is printed "
                "small on purpose — the same size as in the original document.",
    },
    {
        "key": "collaborative",
        "label": "Page 3 — Collaborative classroom activity",
        "file": "assets/image4.jpg",
        "page": 3,
        "frame_w_mm": 82.0,
        "frame_h_mm": 61.5,  # 4:3
        "focus": "centre",
        "caption": "Collaborative classroom activity (illustrative image; "
                   "replace with actual school photograph)",
        "note": "Centred figure with its original caption, as in the document.",
    },
    {
        "key": "sports",
        "label": "Page 5 — Sports and co-curricular activities",
        "file": "assets/image5.jpg",
        "page": 5,
        "frame_w_mm": 85.0,
        "frame_h_mm": 72.0,  # 1.18:1 — matches the paired photo beside it
        "focus": "centre",
        "caption": "Sports and co-curricular activities (illustrative)",
        "note": "Paired with the photo beside it: same height, same frame.",
    },
    {
        "key": "together",
        "label": "Page 5 — Students learning and growing together",
        "file": "assets/image6.jpg",
        "page": 5,
        "frame_w_mm": 85.0,
        "frame_h_mm": 72.0,  # 1.18:1 — matches the paired photo beside it
        "focus": "top",
        "caption": "Students learning and growing together (illustrative)",
        "note": "This picture carries text across its top, so it is cropped "
                "from the bottom only — the wording is never cut off.",
    },
]

# ---------------------------------------------------------------------------
# Page content — verbatim from the original, in the original's page order.
# Lists are "Lead: rest" strings; tables are rows of cell strings.
# ---------------------------------------------------------------------------

PAGES = [
    {
        "key": "cover",
        "name": "Cover",
        "title": "ABRAHAM\nEDUCATION SYSTEM",
        "kicker": "SCHOOL PROSPECTUS  |  ACADEMIC SESSION 2027–2028",
        "body": {
            "admissions_open": "Admissions Open  |  Playgroup to Class 10",
        },
    },
    {
        "key": "about",
        "name": "About, Vision & Priorities",
        "title": "About Us, Our Vision & Our Priorities",
        "kicker": "ABRAHAM EDUCATION SYSTEM  •  PAGE 2",
        "body": {
            "about_heading": "1. ABOUT US",
            "about_paras": [
                "Abraham Education System is committed to providing quality, "
                "affordable and meaningful education in a supportive, "
                "disciplined and student-friendly environment.",
                "We believe that every child has the potential to succeed. "
                "Our aim is to nurture knowledgeable, confident, responsible "
                "and creative individuals equipped with the modern skills and "
                "values needed to contribute positively to society.",
            ],
            "vision_heading": "2. OUR VISION",
            "vision": "To become a leading educational institution that develops "
                      "knowledgeable, capable, confident and socially responsible "
                      "individuals.",
            "mission_heading": "3. OUR MISSION",
            "mission": "To provide quality, affordable and inclusive education "
                       "that meets students' learning needs through effective "
                       "teaching, modern AI based learning approaches and "
                       "character development, enabling every student to realize "
                       "their full potential.",
            "programs_heading": "4. ACADEMIC PROGRAMS",
            "programs_intro": "We offer general education from early childhood "
                              "through secondary level:",
            "programs_junior": ["Playgroup", "Nursery", "KG / Prep"],
            "programs_senior": [
                "Classes 1–5 (Primary)",
                "Classes 6–8 (Middle)",
                "Classes 9–10 (Secondary)",
            ],
            "priorities_heading": "5. OUR EDUCATIONAL PRIORITIES",
            "priorities_intro": "Our educational approach focuses on:",
            "priorities": [
                "Academic Excellence: Strong foundations in core subjects and "
                "effective classroom teaching.",
                "Character Development: Discipline, honesty, respect, "
                "responsibility and good manners.",
                "Student-Centered Learning: Encouraging participation, "
                "creativity, confidence and critical thinking.",
                "Digital Literacy: Developing essential computer and technology "
                "skills.",
                "Co-curricular Development: Encouraging sports, creative "
                "activities, teamwork and leadership.",
                "Individual Attention: Recognizing students' learning needs and "
                "supporting their progress.",
            ],
        },
    },
    {
        "key": "admissions",
        "name": "Environment, Commitment & Admission",
        "title": "Learning Environment, Commitment & Admission",
        "kicker": "ABRAHAM EDUCATION SYSTEM  •  PAGE 3",
        "body": {
            "environment_heading": "6. OUR LEARNING ENVIRONMENT",
            "environment_intro": "We aim to provide a safe, welcoming and "
                                 "supportive environment supported by:",
            "environment_items": [
                "Dedicated classrooms and learning spaces.",
                "Computer and practical learning facilities.",
                "Solar-powered campus infrastructure.",
                "A disciplined and supportive school environment.",
                "Parent–teacher communication and student progress monitoring.",
            ],
            "commitment_heading": "7. OUR COMMITMENT TO PARENTS",
            "commitment_intro": "We recognize parents as important partners in "
                                "their children's education. Abraham Education "
                                "System is committed to:",
            "commitment_items": [
                "Maintaining transparent admission and fee procedures.",
                "Providing regular information about academic progress.",
                "Promoting discipline and positive behavior.",
                "Addressing parents' concerns responsibly.",
                "Maintaining a safe and respectful learning environment.",
            ],
            "admission_heading": "8. ADMISSION INFORMATION",
            "admission_rows": [
                ["Academic Session", "March – February"],
                ["Admissions", "Playgroup to Class 10, subject to available "
                               "seats and admission requirements."],
                ["Fee Structure", "Affordable fee arrangements, with eligible "
                                  "concessions considered under the institution's "
                                  "approved policy."],
            ],
            "process_heading": "Admission Process",
            "process_steps": [
                "Obtain the admission form.",
                "Submit the completed form with required documents.",
                "Attend the prescribed age/grade assessment, where applicable.",
                "Complete admission formalities and fee submission.",
                "Receive confirmation and class placement.",
            ],
        },
    },
    {
        "key": "fees",
        "name": "Fees, Timings & Schedules",
        "title": "Fees, Timings & Weekly Schedule",
        "kicker": "ABRAHAM EDUCATION SYSTEM  •  PAGE 4",
        "body": {
            "fee_heading": "FEE STRUCTURE – ACADEMIC SESSION 2027–2028",
            # The third column is blank in the original. It is kept — with
            # blank cells — rather than dropped. Fill it in the editor.
            "fee_header": ["Class", "Monthly Tuition Fee (Rs.)",
                           "Admission Charges\n(New admission, Non-Refundable)"],
            "fee_rows": [
                ["Pre-N to KG", "5,500", ""],
                ["G-I to G-IV", "6,500", ""],
                ["G-V to G-VII", "7,000", ""],
                ["G-VIII (Pre 9th) to G-X", "8,000", ""],
            ],
            "fee_note_1": "Note: The above fees are monthly tuition fees. "
                          "Admission fee, annual charges, examination fee and "
                          "other applicable charges, if any, will be "
                          "communicated separately.",
            "fee_note_2": "Abraham Education System reserves the right to revise "
                          "the fee structure with prior notice.",
            "timings_heading": "9. SCHOOL TIMINGS & WEEKLY SCHEDULE",
            "timings_session": "Academic Session 2027–2028",
            "timings_intro": "The following proposed schedule is suitable for "
                             "Abraham Education System, covering Pre-Nursery to "
                             "Class X. It provides a balanced routine for academic "
                             "learning, character development, physical activities "
                             "and extracurricular engagement.",
            "timings_subheading": "School Timings",
            "timings_header": ["Classes", "Monday – Thursday", "Friday"],
            "timings_rows": [
                ["Pre-Nursery, Nursery & KG", "8:00 AM – 12:30 PM",
                 "8:00 AM – 11:30 AM"],
                ["Classes I – V", "8:00 AM – 1:30 PM", "8:00 AM – 12:00 PM"],
                ["Classes VI – X", "8:00 AM – 2:00 PM", "8:00 AM – 12:30 PM"],
            ],
            "weekly_subheading": "Weekly Academic Schedule",
            "weekly_header": ["Day", "Main Activities"],
            "weekly_rows": [
                ["Monday", "Regular academic classes and weekly learning objectives"],
                ["Tuesday", "Academic classes, English communication and reading"],
                ["Wednesday", "Academic classes, computer education and practical learning"],
                ["Thursday", "Academic classes, quizzes, assignments and revision"],
                ["Friday", "Weekly assessment, character building, moral education "
                           "and co-curricular activities"],
                ["Saturday", "Weekly holiday"],
                ["Sunday", "Weekly holiday"],
            ],
            "daily_subheading": "Daily School Routine",
            "daily_header": ["Activity", "Suggested Duration"],
            "daily_rows": [
                ["Morning Assembly", "15 minutes"],
                ["Academic Lessons", "As per class timetable"],
                ["Short Break / Refreshment", "15–20 minutes"],
                ["Lunch / Prayer Break", "As applicable"],
                ["Sports & Physical Activities", "Scheduled periods"],
                ["Closing / Dispersal", "As per school timings"],
            ],
        },
    },
    {
        "key": "promise",
        "name": "Instructions, Promise & Contact",
        "title": "Instructions, Our Promise & Contact",
        "kicker": "ABRAHAM EDUCATION SYSTEM  •  PAGE 5",
        "body": {
            "instructions_heading": "IMPORTANT INSTRUCTIONS FOR PARENTS",
            "instructions_items": [
                "Students should arrive at school at least 10 minutes before "
                "the commencement of classes.",
                "Regular attendance and punctuality are compulsory.",
                "Students must wear the prescribed school uniform.",
                "Parents should arrange timely pickup of their children.",
                "School timings may be adjusted during Ramadan, summer and "
                "winter seasons.",
            ],
            "instructions_note": "Any changes in school timings or holidays will be "
                                 "communicated to parents through official school "
                                 "channels.",
            # The original numbers this section "9." as well — kept as-is.
            "promise_heading": "9. OUR PROMISE",
            "promise_para": "At Abraham Education System, education is not limited "
                            "to textbooks and examinations. We strive to develop "
                            "the knowledge, confidence, character and practical "
                            "abilities that help children succeed in life.",
            "quote": "“Give your child the opportunity to learn, grow and achieve.”",
            "banner": "ADMISSIONS OPEN  |  ABRAHAM EDUCATION SYSTEM",
        },
    },
]


def default_project() -> dict:
    """A fresh, deep-copied project: brand + photo slots + five pages."""
    return {
        "brand": copy.deepcopy(BRAND),
        "photos": copy.deepcopy(PHOTO_SLOTS),
        "pages": copy.deepcopy(PAGES),
    }


# ---------------------------------------------------------------------------
# Content check — every passage below must be present in the project.
# The portal runs this on every export so no original text can be lost
# by an edit. (Checked against the project data; the PDF is built from
# exactly that data, so a pass here is a pass for the PDF.)
# ---------------------------------------------------------------------------

REQUIRED_PASSAGES = [
    "ABRAHAM", "EDUCATION SYSTEM",
    "Building Knowledge. Developing Character.",
    "Preparing for the Future.",
    "FEDERAL BOARD OF INTERMEDIATE AND SECONDARY EDUCATION (FBISE)",
    "Zammar Valley, Islamabad",
    "Admissions Open",
    "Playgroup to Class 10",
    "1. ABOUT US",
    "quality, affordable and meaningful education",
    "every child has the potential to succeed",
    "2. OUR VISION",
    "leading educational institution",
    "3. OUR MISSION",
    "modern AI based learning approaches",
    "4. ACADEMIC PROGRAMS",
    "Playgroup", "Nursery", "KG / Prep",
    "Classes 1–5 (Primary)", "Classes 6–8 (Middle)",
    "Classes 9–10 (Secondary)",
    "5. OUR EDUCATIONAL PRIORITIES",
    "Academic Excellence", "Character Development",
    "Student-Centered Learning", "Digital Literacy",
    "Co-curricular Development", "Individual Attention",
    "6. OUR LEARNING ENVIRONMENT",
    "Solar-powered campus infrastructure",
    "7. OUR COMMITMENT TO PARENTS",
    "transparent admission and fee procedures",
    "8. ADMISSION INFORMATION",
    "March – February",
    "Admission Process",
    "Obtain the admission form.",
    "Receive confirmation and class placement.",
    "Collaborative classroom activity",
    "FEE STRUCTURE – ACADEMIC SESSION 2027–2028",
    "Monthly Tuition Fee (Rs.)",
    "Admission Charges",
    "5,500", "6,500", "7,000", "8,000",
    "reserves the right to revise the fee structure with prior notice",
    "9. SCHOOL TIMINGS & WEEKLY SCHEDULE",
    "balanced routine for academic learning",
    "School Timings",
    "8:00 AM – 12:30 PM", "8:00 AM – 2:00 PM",
    "Weekly Academic Schedule",
    "Weekly holiday",
    "Daily School Routine",
    "Morning Assembly",
    "15 minutes",
    "Sports & Physical Activities",
    "IMPORTANT INSTRUCTIONS FOR PARENTS",
    "at least 10 minutes before the commencement of classes",
    "prescribed school uniform",
    "Ramadan, summer and winter seasons",
    "Sports and co-curricular activities",
    "Students learning and growing together",
    "9. OUR PROMISE",
    "not limited to textbooks and examinations",
    "Give your child the opportunity to learn, grow and achieve.",
    "ADMISSIONS OPEN  |  ABRAHAM EDUCATION SYSTEM",
    "LEARN", "GROW", "EXCEL",
]


def _project_text(project: dict) -> str:
    parts = []

    def walk(value):
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, dict):
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)

    walk(project)
    return "\n".join(parts)


def verify_content(project: dict) -> list[str]:
    """Return the required passages that are missing from the project."""
    text = _project_text(project)
    return [p for p in REQUIRED_PASSAGES if p not in text]
