from __future__ import annotations
import io, json, os, re, textwrap
from pathlib import Path
from typing import Any

import streamlit as st
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image as PDFImage,
                                PageBreak, Table, TableStyle, KeepTogether, HRFlowable)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

APP_DIR = Path(__file__).parent
ASSET_DIR = APP_DIR / 'assets'

DEFAULT_PAGES = [
 {"name":"Cover", "title":"ABRAHAM\nEDUCATION SYSTEM", "subtitle":"SCHOOL PROSPECTUS  |  ACADEMIC SESSION 2027–2028", "body":"Building Knowledge. Developing Character.\nPreparing for the Future.\n\nAFFILIATED WITH THE FEDERAL BOARD OF INTERMEDIATE AND SECONDARY EDUCATION (FBISE)\n\nZammar Valley, Islamabad\n\nAdmissions Open  |  Playgroup to Class 10", "image":"image1.jpeg", "image_caption":"Our campus"},
 {"name":"Our School", "title":"A place to learn, grow & thrive", "subtitle":"ABOUT ABRAHAM EDUCATION SYSTEM", "body":"## About Us\nAbraham Education System is committed to providing quality, affordable and meaningful education in a supportive, disciplined and student-friendly environment.\n\nWe believe that every child has the potential to succeed. Our aim is to nurture knowledgeable, confident, responsible and creative individuals equipped with the modern skills and values needed to contribute positively to society.\n\n## Our Vision\nTo become a leading educational institution that develops knowledgeable, capable, confident and socially responsible individuals.\n\n## Our Mission\nTo provide quality, affordable and inclusive education that meets students' learning needs through effective teaching, modern AI based learning approaches and character development, enabling every student to realize their full potential.\n\n## Academic Programs\nWe offer general education from early childhood through secondary level:\n- Junior Section: Playgroup, Nursery, KG / Prep\n- Senior Section: Classes 1–5 (Primary), Classes 6–8 (Middle), Classes 9–10 (Secondary)", "image":"image2.jpg", "image_caption":"Classroom learning"},
 {"name":"The Experience", "title":"Learning for life—not just for exams", "subtitle":"OUR EDUCATIONAL PRIORITIES", "body":"## What We Focus On\n**Academic Excellence:** Strong foundations in core subjects and effective classroom teaching.\n\n**Character Development:** Discipline, honesty, respect, responsibility and good manners.\n\n**Student-Centered Learning:** Encouraging participation, creativity, confidence and critical thinking.\n\n**Digital Literacy:** Developing essential computer and technology skills.\n\n**Co-curricular Development:** Encouraging sports, creative activities, teamwork and leadership.\n\n**Individual Attention:** Recognizing students' learning needs and supporting their progress.\n\n## A Supportive Environment\n- Dedicated classrooms and learning spaces\n- Computer and practical learning facilities\n- Solar-powered campus infrastructure\n- A disciplined and supportive school environment\n- Parent–teacher communication and student progress monitoring\n\n## Our Commitment to Parents\nWe recognize parents as important partners in their children's education. We are committed to transparent admission and fee procedures, regular progress updates, positive behavior, responsive communication, and a safe and respectful learning environment.", "image":"image3.jpg", "image_caption":"Teacher-guided learning"},
 {"name":"Admissions & Fees", "title":"Your child’s next chapter starts here", "subtitle":"ADMISSION INFORMATION  |  SESSION 2027–2028", "body":"## Admissions\n**Academic session:** March – February\n\nAdmissions are offered from Playgroup to Class 10, subject to available seats and admission requirements.\n\n### Admission Process\n1. Obtain the admission form.\n2. Submit the completed form with required documents.\n3. Attend the prescribed age/grade assessment, where applicable.\n4. Complete admission formalities and fee submission.\n5. Receive confirmation and class placement.\n\n## Monthly Tuition Fees\n| Class group | Monthly tuition (Rs.) |\n| --- | ---: |\n| Pre-N to KG | 5,500 |\n| G-I to G-IV | 6,500 |\n| G-V to G-VII | 7,000 |\n| G-VIII (Pre 9th) to G-X | 8,000 |\n\nFees shown are monthly tuition fees. Admission, annual, examination and other applicable charges will be communicated separately. Affordable fee arrangements; eligible concessions considered under approved policy. The school reserves the right to revise fees with prior notice.\n\n## School Timings\n| Classes | Monday – Thursday | Friday |\n| --- | --- | --- |\n| Pre-Nursery, Nursery & KG | 8:00 AM – 12:30 PM | 8:00 AM – 11:30 AM |\n| Classes I – V | 8:00 AM – 1:30 PM | 8:00 AM – 12:00 PM |\n| Classes VI – X | 8:00 AM – 2:00 PM | 8:00 AM – 12:30 PM |", "image":"image4.jpg", "image_caption":"Collaborative classroom activity"},
 {"name":"School Life & Contact", "title":"A bright future begins with a great school day", "subtitle":"OUR PROMISE TO EVERY FAMILY", "body":"## Weekly Academic Schedule\n- **Monday:** Regular academic classes and weekly learning objectives\n- **Tuesday:** Academic classes, English communication and reading\n- **Wednesday:** Academic classes, computer education and practical learning\n- **Thursday:** Academic classes, quizzes, assignments and revision\n- **Friday:** Weekly assessment, character building, moral education and co-curricular activities\n- **Saturday & Sunday:** Weekly holiday\n\n## Important Instructions for Parents\n- Students should arrive at least 10 minutes before classes begin.\n- Regular attendance and punctuality are compulsory. Students must wear the prescribed uniform.\n- Parents should arrange timely pickup of their children.\n- Timings may be adjusted during Ramadan, summer and winter. Changes will be shared through official school channels.\n\n## Our Promise\nAt Abraham Education System, education is not limited to textbooks and examinations. We strive to develop the knowledge, confidence, character and practical abilities that help children succeed in life.\n\n> “Give your child the opportunity to learn, grow and achieve.”\n\n**ADMISSIONS OPEN  |  ABRAHAM EDUCATION SYSTEM**\n\nZammar Valley, Islamabad  |  Cell: ____________________  |  WhatsApp: ____________________\n\nEmail: ______________________________", "image":"image5.jpg", "image_caption":"Sports and co-curricular activities"}
]
DEFAULT = {"school_name":"Abraham Education System", "accent":"#C28A32", "navy":"#102B46", "paper":"#FCFAF6", "font":"Helvetica", "body_size":10, "heading_size":23, "logo_path":"", "pages":DEFAULT_PAGES}

st.set_page_config(page_title="Prospectus Studio | Abraham Education System", page_icon="✦", layout="wide", initial_sidebar_state="expanded")

def fresh_state():
    st.session_state.project = json.loads(json.dumps(DEFAULT))
    st.session_state.active_page = 0
    st.session_state.assets_override = {}

def ensure_state():
    if 'project' not in st.session_state: fresh_state()
ensure_state()

# ---------- PDF rendering ----------
def esc(s: str) -> str:
    return (s or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def inline_md(s: str) -> str:
    s=esc(s)
    s=re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s=re.sub(r'\*(.+?)\*', r'<i>\1</i>', s)
    return s

def parse_table(lines, accent):
    rows=[]
    for line in lines:
        cells=[x.strip() for x in line.strip().strip('|').split('|')]
        if all(re.fullmatch(r':?-{2,}:?', c.replace(' ','')) for c in cells): continue
        rows.append([Paragraph(inline_md(c), ParagraphStyle('cell',fontName='Helvetica',fontSize=8.3,leading=11,textColor=colors.HexColor('#243448'))) for c in cells])
    if not rows: return []
    widths=[(A4[0]-42*mm)/len(rows[0])]*len(rows[0])
    t=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(accent)),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#E4E7EB')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F5F7FA')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    return [t,Spacer(1,7)]

def body_flowables(text, styles, accent):
    out=[]; lines=(text or '').splitlines(); i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line: out.append(Spacer(1,4));i+=1;continue
        if line.startswith('|'):
            group=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                group.append(lines[i]);i+=1
            out.extend(parse_table(group,accent));continue
        if line.startswith('### '): out.append(Paragraph(inline_md(line[4:]),styles['h3']))
        elif line.startswith('## '): out.extend([Spacer(1,5),Paragraph(inline_md(line[3:]),styles['h2'])])
        elif line.startswith('# '): out.append(Paragraph(inline_md(line[2:]),styles['h1']))
        elif line.startswith('> '): out.append(Paragraph(inline_md(line[2:]),styles['quote']))
        elif re.match(r'^[-*] ',line): out.append(Paragraph('•  '+inline_md(line[2:]),styles['bullet']))
        elif re.match(r'^\d+\. ',line): out.append(Paragraph(inline_md(line),styles['bullet']))
        else: out.append(Paragraph(inline_md(line),styles['body']))
        i+=1
    return out

def get_img_bytes(path):
    if not path: return None
    if path.startswith('data:image/') and ',' in path:
        import base64
        try: return base64.b64decode(path.split(',',1)[1])
        except Exception: return None
    if path in st.session_state.get('assets_override',{}): return st.session_state.assets_override[path]
    p=Path(path)
    if not p.is_absolute(): p=APP_DIR/path
    return p.read_bytes() if p.exists() else None

def portable_project(project):
    """Embed session-uploaded images so JSON backups remain self-contained."""
    import base64, mimetypes
    result=json.loads(json.dumps(project,ensure_ascii=False))
    paths=[result.get('logo_path','')]+[pg.get('image','') for pg in result.get('pages',[])]
    for path in paths:
        raw=st.session_state.get('assets_override',{}).get(path)
        if raw:
            mime=mimetypes.guess_type(path)[0] or 'image/jpeg'
            embedded='data:'+mime+';base64,'+base64.b64encode(raw).decode('ascii')
            if result.get('logo_path')==path: result['logo_path']=embedded
            for pg in result.get('pages',[]):
                if pg.get('image')==path: pg['image']=embedded
    return result

def export_pdf(project):
    out=io.BytesIO(); accent=colors.HexColor(project['accent']); navy=colors.HexColor(project['navy'])
    doc=SimpleDocTemplate(out,pagesize=A4,rightMargin=21*mm,leftMargin=21*mm,topMargin=19*mm,bottomMargin=18*mm,title=f"{project['school_name']} Prospectus")
    base=getSampleStyleSheet()
    styles={
     'body':ParagraphStyle('body',parent=base['BodyText'],fontName=project.get('font','Helvetica'),fontSize=int(project.get('body_size',10)),leading=int(project.get('body_size',10))*1.48,textColor=navy,spaceAfter=5),
     'h1':ParagraphStyle('h1',fontName='Helvetica-Bold',fontSize=int(project.get('heading_size',23)),leading=int(project.get('heading_size',23))*1.12,textColor=navy,spaceAfter=6),
     'h2':ParagraphStyle('h2',fontName='Helvetica-Bold',fontSize=15,leading=18,textColor=navy,spaceBefore=8,spaceAfter=4),
     'h3':ParagraphStyle('h3',fontName='Helvetica-Bold',fontSize=11,leading=14,textColor=accent,spaceBefore=5,spaceAfter=3),
     'bullet':ParagraphStyle('bullet',fontName=project.get('font','Helvetica'),fontSize=int(project.get('body_size',10)),leading=int(project.get('body_size',10))*1.42,leftIndent=12,firstLineIndent=-8,textColor=navy,spaceAfter=3),
     'quote':ParagraphStyle('quote',fontName='Helvetica-Oblique',fontSize=13,leading=18,textColor=accent,leftIndent=10,rightIndent=8,spaceBefore=7,spaceAfter=8)}
    story=[];pages=project['pages']; school=esc(project['school_name'])
    for pi,page in enumerate(pages):
        if pi: story.append(PageBreak())
        if pi==0:
            story.extend([Spacer(1,15*mm)])
            logo=get_img_bytes(project.get('logo_path',''))
            if logo:
                try:
                    im=Image.open(io.BytesIO(logo)); im.thumbnail((340,160)); b=io.BytesIO(); im.save(b,format='PNG'); b.seek(0); story.append(PDFImage(b,width=55*mm,height=26*mm,kind='proportional'));story.append(Spacer(1,8*mm))
                except Exception: pass
            story.append(Paragraph(esc(page['title']).replace('\n','<br/>'),ParagraphStyle('cover',fontName='Helvetica-Bold',fontSize=30,leading=34,textColor=navy,alignment=TA_CENTER,spaceAfter=9)))
            story.append(HRFlowable(width='30%',thickness=3,color=accent,hAlign='CENTER',spaceBefore=1,spaceAfter=9))
            story.append(Paragraph(esc(page['subtitle']),ParagraphStyle('sub',fontName='Helvetica-Bold',fontSize=10,leading=14,textColor=accent,alignment=TA_CENTER,spaceAfter=13)))
            image=get_img_bytes(page.get('image',''))
            if image:
                try:
                    im=Image.open(io.BytesIO(image)); im.thumbnail((1200,700)); b=io.BytesIO(); im.save(b,format='JPEG',quality=88); b.seek(0); story.append(PDFImage(b,width=158*mm,height=80*mm,kind='proportional',hAlign='CENTER'));story.append(Spacer(1,5*mm))
                except Exception: pass
            for ln in page['body'].splitlines():
                if ln.strip():story.append(Paragraph(inline_md(ln),ParagraphStyle('coverbody',fontName='Helvetica',fontSize=10,leading=15,textColor=navy,alignment=TA_CENTER,spaceAfter=4)))
        else:
            story.extend([Paragraph(school.upper(),ParagraphStyle('brand',fontName='Helvetica-Bold',fontSize=8,leading=10,textColor=accent,spaceAfter=6)),Paragraph(esc(page['title']),styles['h1']),Paragraph(esc(page['subtitle']),ParagraphStyle('subpage',fontName='Helvetica-Bold',fontSize=8,leading=11,textColor=accent,spaceAfter=10)),HRFlowable(width='100%',thickness=.8,color=colors.HexColor('#E5E7EB'),spaceAfter=9)])
            image=get_img_bytes(page.get('image',''))
            if image:
                try:
                    im=Image.open(io.BytesIO(image)); im.thumbnail((900,400)); b=io.BytesIO();im.save(b,format='JPEG',quality=86);b.seek(0);story.append(PDFImage(b,width=62*mm,height=37*mm,kind='proportional',hAlign='RIGHT'));story.append(Spacer(1,3*mm))
                except Exception: pass
            story.extend(body_flowables(page['body'],styles,project['accent']))
            story.extend([Spacer(1,8),HRFlowable(width='100%',thickness=.5,color=colors.HexColor('#D9DEE5')),Paragraph(f"{school}  •  Zammar Valley, Islamabad",ParagraphStyle('foot',fontName='Helvetica',fontSize=7.5,textColor=colors.HexColor('#667085'),alignment=TA_CENTER,spaceBefore=5))])
    def decorate(canvas,doc):
        canvas.saveState();w,h=A4
        if doc.page>1:
            canvas.setFillColor(accent);canvas.rect(0,h-3*mm,w,3*mm,fill=1,stroke=0)
            canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#718096'));canvas.drawRightString(w-20*mm,10*mm,f"{doc.page:02d}")
        canvas.restoreState()
    doc.build(story,onFirstPage=decorate,onLaterPages=decorate)
    return out.getvalue()

# ---------- editor interface ----------
P=st.session_state.project
st.markdown(f"""<style>
:root{{--navy:{P['navy']};--accent:{P['accent']};--paper:{P['paper']}}}
[data-testid='stAppViewContainer']{{background:linear-gradient(155deg,#f7f8fa 0%,#f3f4f6 100%)}}
[data-testid='stSidebar']{{background:#102B46}}
[data-testid='stSidebar'] *{{color:#f5f7fa}}
.hero{{background:linear-gradient(125deg,#102B46 0%,#1b4568 62%,#284d67 100%);padding:28px 34px;border-radius:20px;color:white;margin-bottom:22px;box-shadow:0 16px 40px #122b4622;position:relative;overflow:hidden}}
.hero:after{{content:'✦';position:absolute;right:35px;top:-40px;font-size:180px;color:#ffffff12}}
.eyebrow{{text-transform:uppercase;letter-spacing:.18em;font-size:10px;color:#e0b861;font-weight:700}}
.hero h1{{color:white;font-family:Georgia,serif;font-size:34px;margin:7px 0 4px}}
.hero p{{color:#dce7f1;margin:0;font-size:14px}}
.pill{{display:inline-block;border:1px solid #ffffff44;border-radius:30px;padding:5px 11px;margin-top:15px;font-size:11px;color:#fff}}
.card{{background:#fff;border:1px solid #e9edf1;border-radius:16px;padding:18px 20px;box-shadow:0 8px 24px #0d263b0b}}
.page-heading{{font-family:Georgia,serif;color:#102b46;font-size:26px;font-weight:700}}
.small-muted{{color:#748294;font-size:12px}}
.stButton button{{border-radius:10px;font-weight:650}}
</style>""",unsafe_allow_html=True)

with st.sidebar:
    st.markdown('### ✦ Prospectus Studio')
    st.caption('ABRAHAM EDUCATION SYSTEM')
    st.markdown('---')
    st.markdown('**Your prospectus**')
    p=st.session_state.project
    for i,page in enumerate(p['pages']):
        if st.button(f"{i+1:02d}  ·  {page['name']}",key=f'nav_{i}',width='stretch',type='primary' if st.session_state.active_page==i else 'secondary'):
            st.session_state.active_page=i;st.rerun()
    st.markdown('---')
    st.markdown('**Project files**')
    uploaded_json=st.file_uploader('Open a saved project',type=['json'],key='json_open')
    if uploaded_json:
        try:
            loaded=json.load(uploaded_json); st.session_state.project=loaded; st.session_state.active_page=0; st.success('Project loaded'); st.rerun()
        except Exception as e: st.error(f'Could not read project: {e}')
    st.download_button('↓  Save project (.json)',data=json.dumps(portable_project(st.session_state.project),ensure_ascii=False,indent=2).encode('utf-8'),file_name='abraham-prospectus-project.json',mime='application/json',width='stretch')
    if st.button('↺ Restore original content',width='stretch'): fresh_state();st.rerun()

st.markdown("<div class='hero'><div class='eyebrow'>A thoughtful start to a brighter future</div><h1>Prospectus Studio</h1><p>Edit your school prospectus, shape its look, and export a print-ready PDF whenever you need it.</p><span class='pill'>2027 — 2028  &nbsp;·&nbsp;  EDITABLE MASTER</span></div>",unsafe_allow_html=True)
editor_tab,design_tab,preview_tab=st.tabs(['✎  Content editor','◈  Brand & design','▧  Preview & export'])
idx=st.session_state.active_page; page=st.session_state.project['pages'][idx]
with editor_tab:
    left,right=st.columns([1.15,.85],gap='large')
    with left:
        st.markdown(f"<div class='page-heading'>{idx+1:02d} / 05 &nbsp; {page['name']}</div><div class='small-muted'>Make changes here—your PDF preview updates from the same project.</div>",unsafe_allow_html=True)
        page['title']=st.text_input('Page title',page['title'],key=f'title_{idx}')
        page['subtitle']=st.text_input('Section label / subtitle',page['subtitle'],key=f'subtitle_{idx}')
        st.caption('Copy supports headings (#, ##), bold (**text**), italics (*text*), bullet lists (- item), numbered lists, quotes (> text), and tables using | separators.')
        page['body']=st.text_area('Page copy',page['body'],height=420,key=f'body_{idx}',label_visibility='collapsed')
        page['image_caption']=st.text_input('Image caption (optional)',page.get('image_caption',''),key=f'caption_{idx}')
    with right:
        st.markdown('#### Page photograph')
        current=get_img_bytes(page.get('image',''))
        if current:
            try: st.image(current,width='stretch',caption=page.get('image_caption',''))
            except Exception: st.info('Image preview unavailable')
        replacement=st.file_uploader('Replace with a photo from your device',type=['png','jpg','jpeg','webp'],key=f'photo_{idx}')
        if replacement:
            path=f"uploads/page_{idx+1}_{replacement.name}"
            st.session_state.assets_override[path]=replacement.getvalue();page['image']=path
            st.success('Photo ready for this session')
        colA,colB=st.columns(2)
        with colA:
            choices=['(No image)']+[f for f in os.listdir(ASSET_DIR) if f.lower().endswith(('.jpg','.jpeg','.png')) and f!='contact.jpg']
            current_name=Path(page.get('image','')).name
            selected=st.selectbox('Use an original photo',choices,index=(choices.index(current_name) if current_name in choices else 0),key=f'photo_pick_{idx}')
            if selected!='(No image)':page['image']=f'assets/{selected}'
            elif not replacement:page['image']=''
        with colB:
            if st.button('Remove page photo',key=f'remove_photo_{idx}'):
                page['image']='';st.rerun()
        st.info('The original prospectus photos are included as starting assets. Use a school-owned, high-resolution photo for your final print version.')

with design_tab:
    st.markdown('<div class="page-heading">Your visual identity</div><div class="small-muted">Set brand colors and typography once; they flow through the full PDF.</div>',unsafe_allow_html=True)
    p=st.session_state.project
    c1,c2,c3=st.columns(3)
    p['school_name']=c1.text_input('School / institution name',p['school_name'])
    p['accent']=c2.color_picker('Accent color',p['accent'])
    p['navy']=c3.color_picker('Main text color',p['navy'])
    p['paper']=st.color_picker('Canvas background (preview)',p.get('paper','#FCFAF6'))
    c1,c2,c3=st.columns(3)
    p['font']=c1.selectbox('Body font',['Helvetica','Times-Roman','Courier'],index=['Helvetica','Times-Roman','Courier'].index(p.get('font','Helvetica')))
    p['body_size']=c2.slider('Body text size',8,14,int(p.get('body_size',10)))
    p['heading_size']=c3.slider('Page title size',18,34,int(p.get('heading_size',23)))
    st.markdown('#### Logo / school mark')
    logo_up=st.file_uploader('Upload a logo (PNG with transparent background works best)',type=['png','jpg','jpeg','webp'],key='logo_upload')
    if logo_up:
        path=f'uploads/logo_{logo_up.name}';st.session_state.assets_override[path]=logo_up.getvalue();p['logo_path']=path;st.success('Logo added to this session')
    elif p.get('logo_path'):
        data=get_img_bytes(p['logo_path'])
        if data:
            st.image(data,width=180)
            if st.button('Remove logo'):p['logo_path']='';st.rerun()
    st.caption('The Word document did not contain a separate, standalone logo file. The app uses a typographic school mark until you upload your official logo.')
    st.markdown('#### Contact details')
    st.caption('Edit phone, WhatsApp, email, address, admissions dates and fee figures directly in the relevant page copy.')
    st.markdown(f"<div class='card' style='background:{p['paper']}'><span style='color:{p['accent']};font-size:11px;letter-spacing:.15em'>BRAND PREVIEW</span><h2 style='color:{p['navy']};font-family:Georgia,serif'>{p['school_name']}</h2><p style='color:{p['navy']};font-size:{p['body_size']}px'>Learning with purpose. Growing with confidence.</p></div>",unsafe_allow_html=True)

with preview_tab:
    st.markdown('<div class="page-heading">Preview & export</div><div class="small-muted">Download a shareable project file or generate the print-ready prospectus PDF.</div>',unsafe_allow_html=True)
    c1,c2=st.columns([1,1])
    with c1:
        pdf=export_pdf(st.session_state.project)
        st.download_button('↓  Generate & download prospectus PDF',data=pdf,file_name='Abraham_Education_System_Prospectus_2027-2028.pdf',mime='application/pdf',type='primary',width='stretch')
    with c2:
        st.download_button('↓  Save editable project JSON',data=json.dumps(portable_project(st.session_state.project),ensure_ascii=False,indent=2).encode('utf-8'),file_name='abraham-prospectus-project.json',mime='application/json',width='stretch')
    st.success('Your PDF is assembled from the current content and design settings. Download it to review before printing or sharing.')
    page=st.session_state.project['pages'][idx]
    col1,col2=st.columns([1.15,.85],gap='large')
    with col1:
        st.markdown(f"<div style='background:{st.session_state.project['paper']};padding:28px;border-radius:15px;border-top:5px solid {st.session_state.project['accent']}'><div style='color:{st.session_state.project['accent']};font-size:11px;letter-spacing:.15em'>{page['subtitle']}</div><h1 style='font-family:Georgia,serif;color:{st.session_state.project['navy']}'>{esc(page['title']).replace(chr(10),'<br/>')}</h1></div>",unsafe_allow_html=True)
        st.markdown(page['body'])
    with col2:
        img=get_img_bytes(page.get('image',''))
        if img:st.image(img,width='stretch',caption=page.get('image_caption',''))
        st.markdown(f"<div class='card'><div style='color:{st.session_state.project['accent']};font-size:11px;letter-spacing:.15em'>SCHOOL</div><h3 style='color:{st.session_state.project['navy']}'>{st.session_state.project['school_name']}</h3><div class='small-muted'>Zammar Valley, Islamabad</div></div>",unsafe_allow_html=True)
    st.markdown('#### All five prospectus sections')
    for n,pg in enumerate(st.session_state.project['pages']):
        with st.expander(f"{n+1:02d}  {pg['name']} — {pg['title'].replace(chr(10),' ')}"):
            st.markdown(pg['body'])
            image=get_img_bytes(pg.get('image',''))
            if image:st.image(image,width=260)

st.markdown('<div style="text-align:center;color:#8793a0;font-size:11px;padding:22px 0 5px">ABRAHAM EDUCATION SYSTEM  ·  PROSPECTUS STUDIO  ·  BUILT FOR EASY UPDATES</div>',unsafe_allow_html=True)
