import ast, json, re
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame, Image, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Preformatted, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = "/home/claude/exam-analytics/"
FD = "/usr/share/fonts/truetype/"
for n, f in (("Carlito", "Regular"), ("Carlito-Bold", "Bold"), ("Carlito-Italic", "Italic"), ("Carlito-BoldItalic", "BoldItalic")):
    pdfmetrics.registerFont(TTFont(n, f"{FD}crosextra/Carlito-{f}.ttf"))
pdfmetrics.registerFont(TTFont("Mono", f"{FD}dejavu/DejaVuSansMono.ttf"))
pdfmetrics.registerFontFamily("Carlito", normal="Carlito", bold="Carlito-Bold", italic="Carlito-Italic", boldItalic="Carlito-BoldItalic")

BLUE = colors.HexColor("#1a73e8"); DARK = colors.HexColor("#202124"); GREY = colors.HexColor("#5f6368")
LIGHT = colors.HexColor("#f1f3f4"); LINE = colors.HexColor("#c4c7c5"); RED = colors.HexColor("#ea4335")
TITLE_TXT = "Cloud-Based Examination Result Analytics System"; AUTHOR = "Namdeo Hiya Harish"
W, H = A4; LM = RM = 20 * mm; FW = W - LM - RM

S = lambda name, **kw: ParagraphStyle(name, **{**dict(fontName="Carlito", fontSize=10.5, leading=15, textColor=DARK), **kw})
body = S("body", alignment=TA_JUSTIFY, spaceAfter=7)
bullet = S("bullet", alignment=TA_JUSTIFY, leftIndent=14, bulletIndent=2, spaceAfter=4)
H1 = S("H1", fontName="Carlito-Bold", fontSize=17, leading=21, spaceBefore=12, spaceAfter=0, keepWithNext=1)
H2 = S("H2", fontName="Carlito-Bold", fontSize=13.5, leading=17, textColor=BLUE, spaceBefore=10, spaceAfter=5, keepWithNext=1)
cap = S("cap", fontName="Carlito-Italic", fontSize=8.8, leading=11, textColor=GREY, alignment=TA_CENTER, spaceBefore=3, spaceAfter=10)
cell = S("cell", fontSize=9.3, leading=12); cellb = S("cellb", fontName="Carlito-Bold", fontSize=9.3, leading=12, textColor=colors.white)
code = ParagraphStyle("code", fontName="Mono", fontSize=6.9, leading=9.0, textColor=DARK, backColor=colors.HexColor("#f6f8fa"),
                      borderColor=colors.HexColor("#d0d7de"), borderWidth=0.6, borderPadding=6, leftIndent=6, rightIndent=6, spaceBefore=6, spaceAfter=6)

# ---------------- helpers ----------------
def P(t, st=body): return Paragraph(t, st)
def B(t): return Paragraph(t, bullet, bulletText="•")
def h1(t):
    r, sp = Rule(), Spacer(1, 6); r.keepWithNext = 1; sp.keepWithNext = 1
    return [Paragraph(t, H1), r, sp]
def h2(t): return Paragraph(t, H2)
class Rule(Flowable):
    def __init__(self, w=None, color=BLUE, th=1.4): super().__init__(); self.w, self.color, self.th = w or FW, color, th
    def wrap(self, aw, ah): return self.w, self.th + 3
    def draw(self): self.canv.setStrokeColor(self.color); self.canv.setLineWidth(self.th); self.canv.line(0, 2, self.w, 2)
def img(name, caption, frac=1.0):
    path = ROOT + "report_build/" + name; w0, h0 = PILImage.open(path).size; w = FW * frac
    return KeepTogether([Image(path, width=w, height=w * h0 / w0, hAlign="CENTER"), Paragraph(caption, cap)])
def table(rows, widths, head=True, align_right=()):
    data = [[Paragraph(str(c), cellb if (head and r == 0) else cell) for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=[FW * w for w in widths], repeatRows=1 if head else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.6, DARK), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("LEFTPADDING", (0, 0), (-1, -1), 7)]
    if head: st += [("BACKGROUND", (0, 0), (-1, 0), BLUE)]
    st += [("BACKGROUND", (0, r), (-1, r), LIGHT) for r in range(2, len(rows), 2)]
    t.setStyle(TableStyle(st)); return KeepTogether([t, Spacer(1, 2)])

def src(path, name):
    text = open(ROOT + path).read(); tree = ast.parse(text); lines = text.splitlines()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef,)) and n.name == name:
            start = min([n.lineno] + [d.lineno for d in n.decorator_list]); return "\n".join(lines[start - 1:n.end_lineno])
    raise KeyError(name)
def sql_block(name):
    m = re.search(rf"(-- [^\n]*\n)?CREATE OR REPLACE VIEW exam_analytics\.{name} AS.*?;", open(ROOT + "bigquery/views.sql").read(), re.S)
    return m.group(0)
def listing(text, caption):
    for l in text.splitlines(): assert len(l) <= 104, (len(l), l)
    return [KeepTogether([Preformatted(text, code), Paragraph(caption, cap)])]

class Placeholder(Flowable):
    def __init__(self, w, h, label): super().__init__(); self.w, self.h, self.label = w, h, label
    def wrap(self, aw, ah): return self.w, self.h
    def draw(self):
        c = self.canv; c.setDash(4, 3); c.setStrokeColor(GREY); c.setFillColor(colors.HexColor("#fafafa")); c.roundRect(0, 0, self.w, self.h, 5, fill=1)
        c.setDash(); c.setFillColor(GREY); c.setFont("Carlito-Bold", 9); c.drawCentredString(self.w / 2, self.h / 2 + 5, "INSERT SCREENSHOT")
        c.setFont("Carlito-Italic", 8.5); c.drawCentredString(self.w / 2, self.h / 2 - 8, self.label)

# ---------------- data ----------------
import subprocess
_c = subprocess.run(["python3", "-m", "pytest", ROOT + "tests", "--collect-only", "-q", "-p", "no:cacheprovider"], capture_output=True, text=True).stdout
N_TESTS = int(re.search(r"(\d+) tests? collected", _c).group(1))
D = json.load(open(ROOT + "analytics_output.json"))
subj = sorted(D["subj"], key=lambda r: r["subject_code"]); cls = sorted(D["cls"], key=lambda r: r["class_id"]); sup = D["support"]
N_STU, N_REC = D["n_students"], D["n_records"]
passed_all = D["students_passed_all"]; pass_all_pct = 100 * passed_all / N_STU
n_sup = len(sup); fail_rec = D["fail_records"]
A_, B_ = cls[0], cls[1]
weak = min(subj, key=lambda r: r["avg_percentage"]); strong = max(subj, key=lambda r: r["avg_percentage"])
b_support = int(B_["needing_support"]); a_support = int(A_["needing_support"])
three_plus = sum(1 for s in sup if s["subjects_failed"] >= 3)
print("sanity:", N_STU, N_REC, passed_all, n_sup, b_support, a_support, three_plus)

# ---------------- doc ----------------
class Doc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        super().__init__(fn, pagesize=A4, leftMargin=LM, rightMargin=RM, topMargin=24 * mm, bottomMargin=20 * mm,
                         title=f"{TITLE_TXT} — {AUTHOR}", author=AUTHOR, subject="Cloud Computing assignment report", **kw)
        fr = Frame(LM, 20 * mm, FW, H - 44 * mm, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(id="cover", frames=[Frame(LM, 15 * mm, FW, H - 30 * mm, leftPadding=0, rightPadding=0)]),
                               PageTemplate(id="body", frames=[fr])])
    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and f.style.name in ("H1", "H2"):
            self.notify("TOCEntry", (0 if f.style.name == "H1" else 1, f.getPlainText(), self.page))

class NumberedCanvas(rl_canvas.Canvas):
    def __init__(self, *a, **k): super().__init__(*a, **k); self._saved = []
    def showPage(self): self._saved.append(dict(self.__dict__)); self._startPage()
    def save(self):
        total = len(self._saved)
        for st in self._saved:
            self.__dict__.update(st)
            if self._pageNumber > 1: self._chrome(total)
            super().showPage()
        super().save()
    def _chrome(self, total):
        self.setFont("Carlito", 8.5); self.setFillColor(GREY)
        self.drawString(LM, H - 15 * mm, TITLE_TXT); self.drawRightString(W - RM, H - 15 * mm, AUTHOR)
        self.setStrokeColor(LINE); self.setLineWidth(0.6); self.line(LM, H - 17.5 * mm, W - RM, H - 17.5 * mm)
        self.setFont("Carlito", 9); self.drawCentredString(W / 2, 11 * mm, f"{self._pageNumber} of {total}")

story = []
# ----- cover -----
story += [Spacer(1, 30 * mm),
          Paragraph("DR. VISHWANATH KARAD MIT WORLD PEACE UNIVERSITY, PUNE", S("c1", fontName="Carlito-Bold", fontSize=12, alignment=TA_CENTER, textColor=GREY)),
          Paragraph("B.Tech — Electrical &amp; Computer Engineering", S("c2", fontSize=11, alignment=TA_CENTER, textColor=GREY, spaceBefore=3)),
          Spacer(1, 22 * mm),
          Paragraph("EXAMINATION RESULT", S("t1", fontName="Carlito-Bold", fontSize=31, leading=37, alignment=TA_CENTER)),
          Paragraph("ANALYTICS SYSTEM", S("t2", fontName="Carlito-Bold", fontSize=31, leading=37, alignment=TA_CENTER, textColor=BLUE)),
          Spacer(1, 6 * mm),
          Paragraph("Cloud-Based Result Storage, Analytics &amp; Dashboarding on Google Cloud Platform", S("st", fontName="Carlito-Italic", fontSize=12.5, alignment=TA_CENTER, textColor=GREY)),
          Spacer(1, 14 * mm), img("fig3_flow.png", "", 0.98), Spacer(1, 26 * mm),
          Paragraph(AUTHOR, S("nm", fontName="Carlito-Bold", fontSize=15, alignment=TA_CENTER)),
          Paragraph("Google Cloud Stack: Cloud Run · Firestore · Cloud Functions · BigQuery · Looker Studio", S("gs", fontSize=10.5, alignment=TA_CENTER, textColor=GREY, spaceBefore=3)),
          NextPageTemplate("body"), PageBreak()]

# ----- TOC -----
story += [Paragraph("Table of Contents", S("tocT", fontName="Carlito-Bold", fontSize=17, leading=21, spaceAfter=4)), Rule(), Spacer(1, 8)]
toc = TableOfContents(); toc.dotsMinLevel = 0
toc.levelStyles = [S("toc0", fontName="Carlito-Bold", fontSize=10.5, leading=17, leftIndent=0),
                   S("toc1", fontSize=10, leading=15, leftIndent=14, textColor=GREY)]
story += [toc, PageBreak()]

# ----- Abstract / Intro -----
story += h1("Abstract")
story += [P(f"This report documents the design, implementation, and testing of a Cloud-Based Examination Result Analytics System built on "
            f"Google Cloud Platform (GCP). The system stores examination results in Firestore through a REST API hosted on Cloud Run; a Cloud Function "
            f"subscribed to Firestore writes grades each result, assigns a PASS/FAIL status, and appends it to BigQuery; a set of BigQuery views then "
            f"derives subject-wise performance, class averages, pass percentages, and a list of students requiring additional support; and a Looker Studio "
            f"dashboard presents these analytics to faculty. The architecture is event-driven and serverless — no component runs continuously — which keeps "
            f"the design low-cost and straightforward to extend to more classes, subjects, and examinations."),
          P(f"The prototype was exercised with a reproducible synthetic dataset of {N_STU} students in two classes across five subjects ({N_REC} result records). "
            f"The grading logic and API validation are covered by {N_TESTS} automated tests, and the analytics SQL was executed against the sample data and "
            f"cross-checked against an independent calculation. On this dataset the system reports a class average of {A_['class_avg_percentage']:.1f}% for {A_['class_id']} and "
            f"{B_['class_avg_percentage']:.1f}% for {B_['class_id']}, {pass_all_pct:.1f}% of students passing every subject, and {n_sup} students automatically flagged for additional support.")]
story += h1("1. Introduction")
story += [P("Examination results are one of the richest sources of information an institution holds, yet they are often kept in spreadsheets that are "
            "tedious to consolidate and slow to analyse. By the time a faculty member has worked out which subject a class struggled with, or which students "
            "are drifting toward failure, the opportunity for timely help has often passed. A cloud-based pipeline that stores results once and turns them into "
            "analytics automatically removes that delay."),
          P("<b>Objectives.</b> The assignment brief called for a system that would: (1) store examination results in a cloud database; (2) generate analytics "
            "such as subject-wise performance, class averages, pass percentages, and students requiring additional support; and (3) present those analytics "
            "through a dashboard, using Cloud SQL/Firestore, BigQuery, Looker Studio, and Cloud Run. This project satisfies these requirements and adds "
            "Cloud Functions to grade results automatically as they arrive. Each requirement is addressed in the sections that follow."),
          img("fig1_concept.png", "Figure 1 — Conceptual summary of the insights the system produces from raw examination results (values from the sample dataset in Section 5).")]

# ----- 2 Architecture -----
story += h1("2. System Architecture")
story += [P("The system follows a linear, event-driven pipeline in which each stage reacts to the one before it. A client submits results to a REST API on "
            "Cloud Run, which validates them and writes them to Firestore. Every write to Firestore triggers a Cloud Function that grades the result and "
            "appends it to BigQuery. BigQuery views compute the analytics, and Looker Studio queries those views to render the dashboard. The same views are "
            "also exposed through read-only endpoints on the Cloud Run API."),
          img("fig2_arch.png", "Figure 2 — High-level system architecture on Google Cloud Platform."),
          img("fig3_flow.png", "Figure 3 — Detailed end-to-end data flow, including the validation and PASS/FAIL decisions."),
          KeepTogether([h2("2.1 Component Overview"),
          table([["Component", "Role", "Output"],
                 ["Data generator / upload client", "Produces (or reads) result records and posts them to the API in batches", "JSON result records"],
                 ["Cloud Run (Flask API)", "Validates payloads, writes to Firestore, serves analytics endpoints", "Stored documents, JSON analytics"],
                 ["Firestore", "Operational store; a write event fires for every document created or updated", "results collection"],
                 ["Cloud Functions", "Computes percentage, grade and PASS/FAIL; appends the row to BigQuery", "Graded rows"],
                 ["BigQuery", "Analytical warehouse holding every graded result plus the analytics views", "Queryable dataset and views"],
                 ["Looker Studio", "Visualises subject-wise, class-wise and at-risk analytics", "Monitoring dashboard"]],
                [0.27, 0.48, 0.25])]), Spacer(1, 8),
          h2("2.2 Design Decisions"),
          P("The brief allows either Cloud SQL or Firestore as the result store. Firestore was chosen; the reasoning is summarised below."),
          table([["Decision", "Choice", "Rationale"],
                 ["Operational store", "Firestore (native mode)", "Serverless with no instance to run; each document write emits an event that can trigger a Cloud Function directly; the document model makes it easy to add new exams or fields."],
                 ["Alternative considered", "Cloud SQL", "Better when strict relational constraints and joins are needed, but it runs on an always-on instance and has no built-in write trigger, so an extra Pub/Sub or polling step would be required."],
                 ["Analytics store", "BigQuery", "Columnar warehouse suited to aggregations across all exams; native Looker Studio connector."],
                 ["Write pattern", "Append-only + “latest wins” view", "Corrections re-write the Firestore document and append a new version; the v_latest_results view keeps only the newest, leaving an audit trail."],
                 ["Region", "asia-south1 (Mumbai)", "Nearest GCP region to the institution, minimising latency."]],
                [0.20, 0.23, 0.57])]

# ----- 3 Implementation -----
story += h1("3. Implementation Details")
story += [h2("3.1 Data Generator and Upload Client"),
          P("A Python script stands in for the examination cell. It creates a reproducible dataset (fixed random seed) for two classes of 60 students and five "
            "subjects, with each student given an overall ability level and each subject a difficulty offset so that the resulting marks look realistic. "
            "Student identifiers are pseudonymous (S001–S120); no personal data is used. Given a Cloud Run URL, the script posts the records in batches of 200."),
          *listing(src("data_generator/generate_results.py", "generate"), "Listing 1 — Synthetic result generation (data_generator/generate_results.py)."),
          h2("3.2 Cloud Run — Ingestion and Analytics API"),
          P("The API is a small Flask application packaged with a Dockerfile and deployed to Cloud Run, which scales it to zero when idle. "
            "<b>POST /results</b> accepts one result or a batch of up to 500. Each record is validated before anything is written (all fields present, marks numeric and "
            "between 0 and the maximum), and a single invalid record rejects the whole request with HTTP 422 so that a batch is never half-stored. "
            "The Firestore document ID is deterministic — <i>exam__student__subject</i> — so re-uploading a corrected mark updates the same document instead of creating a duplicate. "
            "Three read-only endpoints (<b>/analytics/subjects</b>, <b>/analytics/classes</b>, <b>/analytics/support</b>) return the BigQuery views as JSON, with an optional <i>exam_id</i> filter passed as a query parameter."),
          *listing(src("cloud_run/app.py", "validate") + "\n\n" + src("cloud_run/app.py", "add_results"), "Listing 2 — Payload validation and the ingestion endpoint (cloud_run/app.py)."),
          h2("3.3 Firestore — Operational Store"),
          P("Results are stored in a single <i>results</i> collection with one document per student per subject per exam. Keeping the document flat means the "
            "Cloud Function receives everything it needs in the trigger event without extra reads."),
          table([["Field", "Type", "Description"],
                 ["exam_id", "string", "Examination identifier (e.g. MID-SEM-2026)"],
                 ["class_id", "string", "Class or division (e.g. ECE-A)"],
                 ["student_id", "string", "Pseudonymous student identifier"],
                 ["subject_code / subject_name", "string", "Subject identifier and display name"],
                 ["marks / max_marks", "number", "Marks obtained and maximum marks"],
                 ["submitted_at", "timestamp", "Server time at which the API accepted the record"],
                 ["<i>document ID</i>", "string", "{exam_id}__{student_id}__{subject_code} — makes uploads idempotent"]],
                [0.28, 0.14, 0.58]),
          Spacer(1, 4)]
story += [h2("3.4 Cloud Functions — Grading and Processing"),
          P("The Cloud Function (2nd generation, Python) is triggered by every create or update of a document in <i>results/{docId}</i>. It decodes the Firestore event, "
            "calls a pure <i>evaluate()</i> function that computes the percentage, letter grade, and PASS/FAIL status, and appends the enriched row to BigQuery. "
            "Because <i>evaluate()</i> has no cloud dependencies it can be unit-tested locally. The Firestore event ID is passed as the BigQuery insert ID, so a retried "
            "delivery of the same event is de-duplicated. The pass mark is read from the <i>PASS_PERCENTAGE</i> environment variable (default 40)."),
          img("fig5_rules.png", "Figure 4 — Grading and support rules applied by the Cloud Function and the BigQuery views."),
          *listing(src("cloud_function/main.py", "grade_for") + "\n\n" + src("cloud_function/main.py", "evaluate"), "Listing 3 — Grading logic (cloud_function/main.py)."),
          *listing(src("cloud_function/main.py", "process_result"), "Listing 4 — Firestore-triggered entry point (cloud_function/main.py)."),
          KeepTogether([h2("3.5 BigQuery — Analytics Layer"),
          P("Every graded result is appended to one BigQuery table. Because the table is append-only, a corrected mark simply adds a newer version; the "
            "<i>v_latest_results</i> view keeps the most recent version of each (exam, student, subject), and all other views are built on top of it."),
          table([["Field", "Type", "Description"],
                 ["result_id", "STRING", "Firestore document ID, for traceability"],
                 ["exam_id / class_id / student_id", "STRING", "Exam, class and (pseudonymous) student identifiers"],
                 ["subject_code / subject_name", "STRING", "Subject identifier and name"],
                 ["marks / max_marks / percentage", "FLOAT", "Raw marks, maximum, and computed percentage"],
                 ["grade", "STRING", "O, A+, A, B+, B, C or F — assigned by the Cloud Function"],
                 ["result_status", "STRING", "PASS or FAIL — assigned by the Cloud Function"],
                 ["submitted_at / processed_at", "TIMESTAMP", "API acceptance time and Cloud Function processing time"]],
                [0.30, 0.14, 0.56])]), Spacer(1, 8),
          table([["View", "Answers the question", "Key columns"],
                 ["v_latest_results", "What is the current version of every result?", "all table columns"],
                 ["v_subject_performance", "How did each subject perform?", "avg_marks, highest, lowest, pass_percentage"],
                 ["v_student_summary", "How did each student do overall?", "avg_percentage, subjects_failed"],
                 ["v_class_summary", "What are the class averages and pass rates?", "class_avg_percentage, overall_pass_percentage"],
                 ["v_students_needing_support", "Who needs additional help, and why?", "reason, avg_percentage, subjects_failed"],
                 ["v_grade_distribution", "How are grades spread in each subject?", "grade, students"]],
                [0.27, 0.40, 0.33]),
          *listing(sql_block("v_subject_performance") + "\n\n" + sql_block("v_students_needing_support"), "Listing 5 — Two of the analytics views (bigquery/views.sql)."),
          h2("3.6 Looker Studio — Visualization"),
          P("Looker Studio connects directly to the BigQuery views. The dashboard is organised as scorecards for headline numbers (students, overall average, "
            "percentage passing every subject, students needing support), bar charts for subject-wise average and pass percentage, a class comparison, a grade "
            "distribution, and a conditionally formatted table of students requiring additional support. Drop-down controls for exam and class let faculty "
            "narrow every chart at once. Data freshness is shortened from the 12-hour default so newly uploaded results appear quickly. "
            "The layout below was prepared from the computed sample data."),
          img("fig6_dashboard.png", "Figure 5 — Looker Studio dashboard layout (design mock built from the sample dataset).", 0.94)]

# ----- 4 Testing -----
story += h1("4. Testing &amp; Validation")
story += [P("Validation was carried out at two levels. First, the business logic and analytics were tested locally with automated tests. Second, the deployed "
            "pipeline is verified on GCP through the console evidence shown in Figure 8."),
          h2("4.1 Automated tests"),
          P(f"The grading function, the Firestore event decoder, the API validation, and the data generator are covered by {N_TESTS} pytest cases. They check every grade boundary (including 39% → F/FAIL "
            "and 40% → C/PASS), conversion of Firestore field values (including timestamps) into JSON-safe values, rejection of out-of-range or missing fields in both the Cloud Function and the API, "
            f"deterministic document IDs, HTTP behaviour of the endpoints for bad requests, and reproducibility of the generated dataset. All {N_TESTS} pass."),
          img("fig7_tests.png", f"Figure 6 — Excerpt of the automated test run ({N_TESTS} tests passed).", 0.9),
          h2("4.2 Analytics validation"),
          P("The SQL in <i>views.sql</i> was executed on the graded sample data using DuckDB as a local stand-in for BigQuery (the only change was the keyword "
            "<i>EXCEPT</i> → <i>EXCLUDE</i>). The subject averages, subject pass percentages, and the complete list of students requiring support were then compared with an "
            "independent pandas calculation, and matched exactly. A correction scenario was also tested: after re-submitting one mark, the table held 601 rows but the "
            "<i>v_latest_results</i> view returned 600, with the corrected value."),
          table([["Check", "Method", "Result"],
                 ["Grade / status boundaries (10 cases)", "pytest on evaluate()", "Passed"],
                 ["Firestore event decoding (incl. timestamps)", "pytest with protobuf Timestamp", "Passed"],
                 ["Invalid input rejected (Function and API)", "pytest, Flask test client", "Passed"],
                 ["Deterministic IDs, reproducible dataset", "pytest", "Passed"],
                 ["View SQL vs independent calculation", "DuckDB + pandas on 600 records", "Identical"],
                 ["Correction handling (latest version wins)", "601 rows appended → view", "600 rows, corrected value"]],
                [0.42, 0.34, 0.24]), Spacer(1, 8),
          h2("4.3 Deployment verification"),
          P("The deployment scripts (<i>deploy.sh</i>, <i>setup_bigquery.sh</i>) create the Firestore database, the BigQuery dataset, table and views, the Cloud Run "
            "service, and the Firestore-triggered Cloud Function. After deployment the sample dataset is uploaded with <i>generate_results.py --url</i>. "
            "The console evidence of this run is captured below."),
          ]
grid = Table([[Placeholder(FW / 2 - 6, 105, "Cloud Run service exam-results-api (URL, healthy revision)"), Placeholder(FW / 2 - 6, 105, "Firestore results collection with documents")],
              [Placeholder(FW / 2 - 6, 105, "Cloud Function process-exam-result logs"), Placeholder(FW / 2 - 6, 105, "Looker Studio dashboard on live BigQuery views")]],
             colWidths=[FW / 2, FW / 2], rowHeights=[112, 112])
grid.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
story += [KeepTogether([grid, Paragraph("Figure 8 — Deployment evidence from the Google Cloud console.", cap)])]

# ----- 5 Results -----
story += h1("5. Results")
story += [P(f"The system was run on the synthetic dataset described in Section 3.1. The figures below are the output of the analytics views for exam MID-SEM-2026. "
            f"Because the data is generated, these numbers demonstrate how the analytics behave rather than describing a real cohort."),
          table([["Measure", "Value"],
                 ["Students / classes / subjects", f"{N_STU} / 2 (60 each) / 5"],
                 ["Result records stored", f"{N_REC}"],
                 ["Records passed / failed (40% pass mark)", f"{N_REC - fail_rec} / {fail_rec}  ({100*(N_REC-fail_rec)/N_REC:.2f}% pass)"],
                 ["Students passing every subject", f"{passed_all} of {N_STU}  ({pass_all_pct:.1f}%)"],
                 ["Overall average", f"{D['overall_avg']:.2f}%"],
                 ["Students flagged for additional support", f"{n_sup}"]], [0.6, 0.4]), Spacer(1, 8),
          h2("5.1 Subject-wise performance"),
          table([["Subject", "Average (%)", "Highest", "Lowest", "Pass (%)"]] +
                [[r["subject_name"], f"{r['avg_percentage']:.2f}", f"{r['highest']:.0f}", f"{r['lowest']:.0f}", f"{r['pass_percentage']:.2f}"] for r in subj],
                [0.36, 0.16, 0.16, 0.16, 0.16]), Spacer(1, 6),
          P(f"{strong['subject_name']} was the strongest subject ({strong['avg_percentage']:.1f}% average) and {weak['subject_name']} the weakest "
            f"({weak['avg_percentage']:.1f}% average, {weak['pass_percentage']:.1f}% pass), which is where a revision session would be best directed."),
          h2("5.2 Class averages and pass percentages"),
          table([["Class", "Students", "Class average (%)", "Passed all subjects", "Overall pass (%)", "Need support"]] +
                [[r["class_id"], f"{r['students']}", f"{r['class_avg_percentage']:.2f}", f"{r['passed_all']:.0f}", f"{r['overall_pass_percentage']:.1f}", f"{r['needing_support']:.0f}"] for r in cls],
                [0.14, 0.14, 0.20, 0.20, 0.17, 0.15]), Spacer(1, 6),
          P(f"{B_['class_id']} trails {A_['class_id']} by {A_['class_avg_percentage'] - B_['class_avg_percentage']:.1f} percentage points and accounts for {b_support} of the "
            f"{n_sup} students flagged for support, so targeted remedial teaching would be most valuable there."),
          img("fig8_results.png", "Figure 7 — Analytics generated by the BigQuery views: subject averages, class averages by subject, and grade distribution.")]
top = sup[:8]
story += [h2("5.3 Students requiring additional support"),
          P(f"A student is flagged when they fail any subject or their overall average is below 50%. Of the {n_sup} flagged students, "
            f"{sum(1 for s in sup if s['reason']=='Failed subject(s) + low average')} both failed a subject and averaged below 50%, "
            f"{sum(1 for s in sup if s['reason']=='Failed subject(s)')} failed at least one subject but averaged 50% or more, and "
            f"{sum(1 for s in sup if s['reason']=='Low average (below 50%)')} passed every subject with a low average. "
            f"{three_plus} students failed three or more subjects. The most urgent cases are listed below (pseudonymous IDs)."),
          table([["Student", "Class", "Average (%)", "Subjects failed", "Lowest (%)", "Reason"]] +
                [[s["student_id"], s["class_id"], f"{s['avg_percentage']:.1f}", f"{int(s['subjects_failed'])}", f"{s['lowest_percentage']:.0f}", s["reason"]] for s in top],
                [0.11, 0.10, 0.14, 0.15, 0.13, 0.37]),
          Paragraph("Table — Highest-priority students from v_students_needing_support (sorted by subjects failed, then lowest average).", cap)]

# ----- 6 Discussion -----
story += h1("6. Discussion &amp; Limitations")
for t in [
    "<b>Synthetic data:</b> all results come from a seeded random generator, so the class and subject comparisons illustrate the system rather than describe real students. The pipeline is data-agnostic and would work unchanged on real results.",
    "<b>Simple support rule:</b> a student is flagged when they fail any subject or average below 50%. This is transparent and easy to change, but it ignores attendance, internal assessment, and trends across exams.",
    "<b>Security and privacy:</b> for demonstration the Cloud Run service is deployed unauthenticated. A real deployment needs authentication (for example Identity Platform or IAM), Firestore security rules, and role-based access so that only authorised faculty can see student-level data. Student identifiers are already pseudonymous.",
    "<b>Append-only growth:</b> keeping every version gives an audit trail and simple correction handling, but the table grows with each edit. Partitioning by exam and periodic archiving would control storage as history accumulates.",
    "<b>At-least-once delivery:</b> Firestore triggers may deliver an event more than once. Passing the event ID as the BigQuery insert ID removes most duplicates, and the “latest wins” view guarantees that any that remain do not affect the analytics.",
    "<b>Per-document invocation:</b> each result document triggers one function call, which is fine at class scale (600 calls for this run). For university-wide bulk loads, a BigQuery batch load job would be more economical.",
    "<b>Dashboard freshness:</b> Looker Studio caches query results; the data-freshness setting must be shortened from the 12-hour default if near-real-time updates are needed.",
    "<b>Serverless by design:</b> Cloud Run, Cloud Functions, Firestore, and BigQuery all scale to zero or bill per use, so an idle system costs almost nothing."]:
    story.append(B(t))

story += h1("7. Future Work")
for t in ["Add a web form or CSV-upload page on Cloud Run for the examination cell, replacing the command-line client.",
          "Notify mentors automatically (email or messaging) when a student is flagged, using an additional Cloud Function.",
          "Track performance across multiple exams and semesters to show trends, and compute SGPA/CGPA.",
          "Use BigQuery ML to predict students at risk of failing before the end-semester examination.",
          "Add authentication with role-based dashboards for faculty, heads of department, and students.",
          "Move student and course master data to Cloud SQL if strict relational constraints become necessary, keeping Firestore for high-volume result events."]:
    story.append(B(t))
story += h1("8. Conclusion")
story += [P("The completed prototype satisfies every requirement of the assignment brief: examination results are stored in Firestore through a Cloud Run API; "
            "a Cloud Function grades each result as it arrives; BigQuery views generate subject-wise performance, class averages, pass percentages, and the list of "
            "students requiring additional support; and Looker Studio presents these analytics as a dashboard. The event-driven, serverless design scales naturally "
            "with the number of students, classes, and examinations, and the automated tests and SQL cross-checks in Section 4 give confidence in the logic. With the "
            "security hardening and refinements noted in Sections 6 and 7, the same architecture is a realistic foundation for a genuine institutional result-analytics service.")]

# ----- references -----
story += h1("References")
for label, url in [("Google Cloud Run Documentation", "https://cloud.google.com/run/docs"),
                   ("Google Cloud Firestore Documentation", "https://cloud.google.com/firestore/docs"),
                   ("Google Cloud Functions Documentation", "https://cloud.google.com/functions/docs"),
                   ("Google BigQuery Documentation", "https://cloud.google.com/bigquery/docs"),
                   ("Looker Studio Help", "https://support.google.com/looker-studio")]:
    story.append(Paragraph(f'<link href="{url}" color="#1a0dab"><u>{label}</u></link>', S("ref", spaceAfter=5)))

story += h1("Project Folder Structure")
tree = f"""exam-analytics/
├── README.md
├── deploy.sh                    # Cloud Run + Cloud Function + Firestore deployment
├── setup_bigquery.sh            # dataset, table and views
├── looker_studio_guide.md       # dashboard set-up steps
├── cloud_run/
│   ├── app.py                   # ingestion + analytics API (Flask)
│   ├── Dockerfile
│   └── requirements.txt
├── cloud_function/
│   ├── main.py                  # Firestore trigger: grade + append to BigQuery
│   └── requirements.txt
├── bigquery/
│   ├── schema.json              # exam_results table
│   └── views.sql                # analytics views
├── data_generator/
│   └── generate_results.py      # synthetic dataset + batch uploader
└── tests/
    ├── test_logic.py            # {N_TESTS} pytest cases
    └── run_sql_check.py         # SQL views vs independent calculation"""
story += [P("Project layout used during development and testing:"), Preformatted(tree, code),
          Paragraph("Figure 9 — Project repository folder structure.", cap)]

doc = Doc(ROOT + "Cloud_Based_Examination_Result_Analytics_Report.pdf")
doc.multiBuild(story, canvasmaker=NumberedCanvas)
print("built")
