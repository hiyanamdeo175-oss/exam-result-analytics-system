import json, subprocess, textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon
import pandas as pd

for f in ("Regular", "Bold", "Italic", "BoldItalic"):
    fm.fontManager.addfont(f"/usr/share/fonts/truetype/crosextra/Carlito-{f}.ttf")
plt.rcParams["font.family"] = "Carlito"

BLUE, GREEN, YELLOW, RED, PURPLE, DARK, GREY = "#1a73e8", "#34a853", "#fbbc04", "#ea4335", "#7b1fa2", "#2b2f36", "#5f6368"
OUT = "report_build/"
D = json.load(open("analytics_output.json"))
df = pd.read_csv("evaluated_results.csv")
subj = pd.DataFrame(D["subj"]); cls = pd.DataFrame(D["cls"]); sup = pd.DataFrame(D["support"])
short = {"Digital Signal Processing": "DSP", "Microprocessors": "Microproc.", "Control Systems": "Control Sys.",
         "Data Structures": "Data Struct.", "Engineering Mathematics": "Eng. Maths"}

def box(ax, x, y, w, h, color, title, sub=None, tc="white", fs=9.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06", fc=color, ec="none"))
    ax.text(x + w/2, y + h/2 + (0.09 if sub else 0), title, ha="center", va="center", color=tc, fontsize=fs, fontweight="bold")
    if sub:
        ax.text(x + w/2, y + h/2 - 0.12, sub, ha="center", va="center", color=tc, fontsize=fs-2.6)

def arrow(ax, p1, p2, color=GREY, ls="-", rad=0.0, lw=1.4):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=11, color=color, lw=lw, ls=ls,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))

# ---------------- Fig 1: concept ----------------
fig, ax = plt.subplots(figsize=(7.2, 2.7)); ax.set_xlim(0, 12); ax.set_ylim(0, 4.5); ax.axis("off")
ax.add_patch(FancyBboxPatch((0.05, 0.05), 11.9, 4.4, boxstyle="round,pad=0.02,rounding_size=0.15", fc="#f4f8fe", ec="#d2e3fc", lw=1.2))
ax.text(0.4, 4.0, "EXAMINATION RESULTS  →  ACTIONABLE INSIGHT", fontsize=10, fontweight="bold", color=BLUE)
top_subj = subj.sort_values("avg_percentage")
cards = [
 ("Subject-wise performance", f"{subj.avg_percentage.min():.1f}% – {subj.avg_percentage.max():.1f}%", "subject average range", BLUE),
 ("Class averages", f"{cls.class_avg_percentage.max():.1f}% / {cls.class_avg_percentage.min():.1f}%", "ECE-A vs ECE-B", GREEN),
 ("Pass percentage", f"{D['students_passed_all']/D['n_students']*100:.1f}%", "passed every subject", YELLOW),
 ("Needs additional support", f"{len(sup)} students", "flagged automatically", RED),
]
for i, (t, v, s, c) in enumerate(cards):
    x = 0.35 + i * 2.9
    ax.add_patch(FancyBboxPatch((x, 0.5), 2.7, 3.0, boxstyle="round,pad=0.02,rounding_size=0.1", fc="white", ec=c, lw=1.8))
    ax.add_patch(FancyBboxPatch((x, 3.05), 2.7, 0.45, boxstyle="round,pad=0.0,rounding_size=0.1", fc=c, ec="none"))
    ax.text(x + 1.35, 3.28, t, ha="center", va="center", fontsize=7.4, fontweight="bold", color="white" if c != YELLOW else DARK)
    ax.text(x + 1.35, 2.0, v, ha="center", va="center", fontsize=12.5, fontweight="bold", color=DARK)
    ax.text(x + 1.35, 1.15, s, ha="center", va="center", fontsize=7, color=GREY)
fig.savefig(OUT + "fig1_concept.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ---------------- Fig 2: architecture ----------------
fig, ax = plt.subplots(figsize=(7.2, 2.9)); ax.set_xlim(0, 17); ax.set_ylim(0, 6); ax.axis("off")
ax.add_patch(FancyBboxPatch((0.1, 0.15), 3.0, 5.5, boxstyle="round,pad=0.02,rounding_size=0.12", fc="white", ec="#c4c7c5"))
ax.text(1.6, 5.2, "Result Sources", ha="center", fontsize=9.5, fontweight="bold", color=DARK)
for i, t in enumerate(["Exam-cell CSV", "Marks entry form", "Upload script"]):
    ax.add_patch(FancyBboxPatch((0.35, 3.65 - i*1.3), 2.5, 0.9, boxstyle="round,pad=0.02,rounding_size=0.08", fc="#eef3fd", ec=BLUE, lw=1))
    ax.text(1.6, 4.1 - i*1.3, t, ha="center", va="center", fontsize=7.8, color=DARK)
ax.add_patch(FancyBboxPatch((3.45, 0.15), 13.45, 5.5, boxstyle="round,pad=0.02,rounding_size=0.12", fc="#fafafa", ec="#c4c7c5"))
ax.text(10.2, 5.2, "Google Cloud Platform", ha="center", fontsize=11, fontweight="bold", color=DARK)
nodes = [("Cloud Run", "REST API", BLUE), ("Firestore", "results store", YELLOW), ("Cloud Functions", "grade + status", GREEN),
         ("BigQuery", "analytics views", "#4285f4"), ("Looker Studio", "dashboard", PURPLE)]
xs = [3.75 + i*2.65 for i in range(5)]
for (t, s_, c), x in zip(nodes, xs):
    box(ax, x, 2.6, 2.15, 1.35, c, t, s_, tc=DARK if c == YELLOW else "white", fs=7.5)
arrow(ax, (3.1, 3.3), (3.75, 3.3), BLUE)
for i in range(4):
    arrow(ax, (xs[i] + 2.15, 3.275), (xs[i+1], 3.275))
arrow(ax, (xs[3] + 1.07, 2.6), (xs[0] + 1.07, 2.6), GREY, ls=(0, (4, 3)), rad=-0.3)
ax.text((xs[0] + xs[3]) / 2 + 1.07, 0.75, "GET /analytics/*  (Cloud Run reads the BigQuery views)", ha="center", fontsize=8, color=GREY, style="italic")
for i, l in enumerate(["store", "on write", "append", "SQL views"]):
    ax.text(xs[i] + 2.4, 4.15, l, ha="center", fontsize=7, color=GREY)
fig.savefig(OUT + "fig2_arch.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ---------------- Fig 3: data flow ----------------
fig, ax = plt.subplots(figsize=(7.2, 3.6)); ax.set_xlim(0, 14); ax.set_ylim(0, 7); ax.axis("off")
ax.text(0.1, 6.7, "End-to-End Data Flow", fontsize=13, fontweight="bold", color=DARK)
ax.text(0.1, 6.3, "Cloud-Based Examination Result Analytics System — GCP Pipeline", fontsize=8, color=GREY)
box(ax, 0.1, 3.9, 2.0, 1.1, DARK, "Result Upload", "CSV / JSON batch", fs=7.6)
def diamond(cx, cy, w, h, label, fc="white"):
    ax.add_patch(Polygon([(cx-w/2, cy), (cx, cy+h/2), (cx+w/2, cy), (cx, cy-h/2)], fc=fc, ec=DARK, lw=1.2))
    ax.text(cx, cy, label, ha="center", va="center", fontsize=8, fontweight="bold", color=DARK)
box(ax, 2.7, 3.9, 2.0, 1.1, BLUE, "Cloud Run API", "validate payload", fs=7.6)
diamond(6.05, 4.45, 1.9, 1.5, "Valid?")
box(ax, 7.6, 3.9, 1.9, 1.1, YELLOW, "Firestore", "results/{docId}", tc=DARK, fs=7.6)
box(ax, 10.0, 3.9, 2.0, 1.1, GREEN, "Cloud Function", "trigger: doc written", fs=7.6)
diamond(13.0, 4.45, 1.9, 1.5, "% ≥ 40 ?")
box(ax, 4.6, 1.0, 1.9, 1.0, RED, "HTTP 422", "record rejected", fs=7.6)
box(ax, 10.0, 1.0, 2.0, 1.0, "#4285f4", "BigQuery", "append graded row", fs=7.6)
box(ax, 6.9, 1.0, 1.9, 1.0, PURPLE, "Looker Studio", "dashboard", fs=7.6)
arrow(ax, (2.1, 4.45), (2.7, 4.45)); arrow(ax, (4.7, 4.45), (5.1, 4.45)); arrow(ax, (7.0, 4.45), (7.6, 4.45))
arrow(ax, (9.5, 4.45), (10.0, 4.45)); arrow(ax, (12.0, 4.45), (12.05, 4.45))
arrow(ax, (6.05, 3.7), (5.7, 2.0), rad=0.0); ax.text(6.05, 2.8, "No", fontsize=7.5, color=GREY, style="italic")
ax.text(7.05, 4.6, "Yes", fontsize=7.5, color=GREY, style="italic")
arrow(ax, (13.0, 3.7), (12.0, 1.7), rad=-0.15); ax.text(12.15, 2.85, "PASS / FAIL\n+ grade", fontsize=7.5, color=GREY, style="italic", ha="right")
arrow(ax, (10.0, 1.5), (8.8, 1.5)); ax.text(9.4, 1.72, "views", fontsize=7, color=GREY, ha="center", style="italic")
ax.text(0.1, 0.25, "Every accepted result is graded and stored; the BigQuery views then derive subject-wise performance, class averages,\n"
                   "pass percentages and the list of students requiring additional support, which Looker Studio renders.",
        fontsize=7.6, color=GREY, va="bottom")
fig.savefig(OUT + "fig3_flow.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ---------------- Fig 5: grading rules ----------------
fig, ax = plt.subplots(figsize=(7.2, 1.9)); ax.set_xlim(0, 14); ax.set_ylim(0, 3.7); ax.axis("off")
ax.text(0.1, 3.4, "Grading & Support Rules Applied", fontsize=11, fontweight="bold", color=DARK)
ax.text(0.1, 3.0, "As implemented in the Cloud Function (grade / status) and BigQuery views (support flag)", fontsize=7.5, color=GREY)
bands = [("O", "≥ 90", GREEN), ("A+", "80–89", "#57bb8a"), ("A", "70–79", "#8ecf9c"), ("B+", "60–69", "#c5e1a5"),
         ("B", "50–59", "#fff2b3"), ("C", "40–49", "#ffd580"), ("F", "< 40", RED)]
for i, (g, r, c) in enumerate(bands):
    x = 0.1 + i * 1.32
    ax.add_patch(FancyBboxPatch((x, 1.55), 1.2, 1.05, boxstyle="round,pad=0.02,rounding_size=0.06", fc=c, ec="none"))
    ax.text(x + 0.6, 2.2, g, ha="center", va="center", fontsize=12, fontweight="bold", color="white" if g in ("O", "F") else DARK)
    ax.text(x + 0.6, 1.8, r + " %", ha="center", va="center", fontsize=7.5, color="white" if g in ("O", "F") else DARK)
ax.add_patch(FancyBboxPatch((9.55, 1.55), 4.3, 1.05, boxstyle="round,pad=0.02,rounding_size=0.06", fc="white", ec=RED, lw=1.6))
ax.text(11.7, 2.32, "Needs additional support if", ha="center", fontsize=8, fontweight="bold", color=RED)
ax.text(11.7, 2.0, "any subject is below 40 %", ha="center", fontsize=7.6, color=DARK)
ax.text(11.7, 1.72, "or overall average is below 50 %", ha="center", fontsize=7.6, color=DARK)
ax.text(0.1, 0.9, "PASS mark: 40 % per subject.  A student “passes overall” only when every subject is passed.", fontsize=8, color=GREY)
ax.text(0.1, 0.4, "The pass mark is an environment variable (PASS_PERCENTAGE); the grade bands live in one GRADE_BANDS table in the Cloud Function.", fontsize=8, color=GREY)
fig.savefig(OUT + "fig5_rules.png", dpi=200, bbox_inches="tight"); plt.close(fig)

# ---------------- Fig 6: dashboard mock ----------------
fig = plt.figure(figsize=(7.2, 5.0)); fig.patch.set_facecolor("#f1f3f4")
fig.text(0.04, 0.955, "Examination Result Analytics Dashboard", fontsize=13, fontweight="bold", color=BLUE)
fig.text(0.70, 0.955, "Exam: MID-SEM-2026  v", fontsize=8.5, color=GREY, bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#dadce0"))
kpis = [("Students", f"{D['n_students']}", BLUE), ("Result records", f"{D['n_records']}", BLUE),
        ("Overall average", f"{D['overall_avg']:.1f}%", GREEN), ("Passed all subjects", f"{D['students_passed_all']/D['n_students']*100:.1f}%", GREEN),
        ("Need support", f"{len(sup)}", RED)]
for i, (t, v, c) in enumerate(kpis):
    a = fig.add_axes([0.04 + i*0.187, 0.79, 0.17, 0.11]); a.axis("off")
    a.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.0,rounding_size=0.08", fc="white", ec="#dadce0", transform=a.transAxes))
    a.text(0.08, 0.72, t, fontsize=7.5, color=GREY, transform=a.transAxes)
    a.text(0.08, 0.22, v, fontsize=15, fontweight="bold", color=c, transform=a.transAxes)
def panel(rect, title):
    a = fig.add_axes(rect); a.set_facecolor("white")
    for s in a.spines.values(): s.set_color("#dadce0")
    a.set_title(title, fontsize=8.5, fontweight="bold", loc="left", color=DARK, pad=6)
    a.tick_params(labelsize=7, colors=GREY); return a
a = panel([0.07, 0.42, 0.40, 0.29], "Subject-wise average (%)")
s2 = subj.sort_values("subject_code"); a.bar([short[n] for n in s2.subject_name], s2.avg_percentage, color=BLUE, width=0.6)
for i, v in enumerate(s2.avg_percentage): a.text(i, v + 1, f"{v:.0f}", ha="center", fontsize=7, color=DARK)
a.set_ylim(0, 100)
a = panel([0.57, 0.42, 0.40, 0.29], "Pass percentage by subject (%)")
a.bar([short[n] for n in s2.subject_name], s2.pass_percentage, color=GREEN, width=0.6); a.set_ylim(0, 115); a.set_yticks([0,20,40,60,80,100])
for i, v in enumerate(s2.pass_percentage): a.text(i, v + 1.5, f"{v:.0f}", ha="center", fontsize=7, color=DARK)
a = panel([0.07, 0.06, 0.28, 0.27], "Class average (%)")
a.bar(cls.class_id, cls.class_avg_percentage, color=[BLUE, "#8ab4f8"], width=0.5); a.set_ylim(0, 100)
for i, v in enumerate(cls.class_avg_percentage): a.text(i, v + 1.5, f"{v:.1f}", ha="center", fontsize=8, color=DARK)
a = fig.add_axes([0.42, 0.06, 0.55, 0.27]); a.axis("off"); a.set_title("Students requiring additional support", fontsize=8.5, fontweight="bold", loc="left", color=DARK, pad=6)
hdr = ["Student", "Class", "Average", "Failed", "Reason"]; cx = [0.0, 0.16, 0.30, 0.46, 0.58]
for x, h in zip(cx, hdr): a.text(x, 0.93, h, fontsize=7.2, fontweight="bold", color=GREY, transform=a.transAxes)
for r, (_, row) in enumerate(sup.head(6).iterrows()):
    y = 0.78 - r * 0.145
    a.add_patch(plt.Rectangle((-0.02, y - 0.05), 1.04, 0.13, fc="#fce8e6" if row.subjects_failed > 1 else "#fef7e0", ec="none", transform=a.transAxes))
    vals = [row.student_id, row.class_id, f"{row.avg_percentage:.1f}%", str(int(row.subjects_failed)), row.reason.replace("Failed subject(s)", "Failed subj.")]
    for x, v in zip(cx, vals): a.text(x, y, v, fontsize=7, color=DARK, transform=a.transAxes)
fig.savefig(OUT + "fig6_dashboard.png", dpi=200); plt.close(fig)

# ---------------- Fig 7: terminal ----------------
res = subprocess.run(["python3", "-m", "pytest", "tests", "-q", "--no-header", "-p", "no:cacheprovider"], capture_output=True, text=True)
lines = ["$ python -m pytest tests -v"]
v = subprocess.run(["python3", "-m", "pytest", "tests", "-v", "--no-header", "-p", "no:cacheprovider"], capture_output=True, text=True).stdout.splitlines()
keep = [l for l in v if "PASSED" in l]
pick = keep[::2][:11]
lines += [l.replace("tests/test_logic.py::", "") for l in pick]
lines += [f"... ({len(keep) - len(pick)} more)", v[-1].replace("=", "").strip()]
lines = ["$ python -m pytest tests -v"] + [l[:100] for l in lines[1:]]
open(OUT + "pytest_output.txt", "w").write("\n".join(lines))
fig, ax = plt.subplots(figsize=(7.2, 0.2 + 0.19 * len(lines))); ax.axis("off"); fig.patch.set_facecolor("#0c0c0c")
for i, l in enumerate(lines):
    col = "#e5e5e5" if l.startswith("$") else ("#16c60c" if "PASSED" in l or "passed" in l else "#cccccc")
    ax.text(0.01, 1 - (i + 0.8) / len(lines), l, family="DejaVu Sans Mono", fontsize=6.4, color=col, transform=ax.transAxes, va="center")
fig.savefig(OUT + "fig7_tests.png", dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor(), pad_inches=0.12); plt.close(fig)

# ---------------- Fig 8: results charts ----------------
fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.6)); fig.subplots_adjust(wspace=0.38, bottom=0.27, top=0.88, left=0.06, right=0.99)
ax = axs[0]; s2 = subj.sort_values("subject_code"); x = range(len(s2))
ax.bar(x, s2.avg_percentage, color=BLUE, width=0.62); ax.set_xticks(list(x)); ax.set_xticklabels([short[n] for n in s2.subject_name], rotation=35, ha="right", fontsize=7.5)
for i, v in enumerate(s2.avg_percentage): ax.text(i, v + 1, f"{v:.1f}", ha="center", fontsize=7)
ax.set_ylim(0, 100); ax.set_title("Average marks by subject (%)", fontsize=9, fontweight="bold", loc="left")
ax = axs[1]
cols = {"ECE-A": BLUE, "ECE-B": "#f28b82"}
w = 0.38
for j, c in enumerate(["ECE-A", "ECE-B"]):
    sub = df[df.class_id == c].groupby("subject_code").percentage.mean().reindex(s2.subject_code)
    ax.bar([i + (j - 0.5) * w for i in x], sub.values, width=w, color=cols[c], label=c)
ax.set_xticks(list(x)); ax.set_xticklabels([short[n] for n in s2.subject_name], rotation=35, ha="right", fontsize=7.5)
ax.set_ylim(0, 100); ax.legend(fontsize=7, frameon=False, loc="upper right", ncol=2); ax.set_title("Class average by subject (%)", fontsize=9, fontweight="bold", loc="left")
ax = axs[2]
order = ["O", "A+", "A", "B+", "B", "C", "F"]; gc = df.grade.value_counts().reindex(order).fillna(0)
ax.bar(order, gc.values, color=[GREEN, "#57bb8a", "#8ecf9c", "#c5e1a5", "#ffe082", "#ffb74d", RED], width=0.65)
for i, v in enumerate(gc.values): ax.text(i, v + 3, str(int(v)), ha="center", fontsize=7)
ax.set_title("Grade distribution (600 results)", fontsize=9, fontweight="bold", loc="left"); ax.set_ylim(0, gc.max() * 1.15)
for a in axs:
    a.spines[["top", "right"]].set_visible(False); a.tick_params(labelsize=7.5)
fig.savefig(OUT + "fig8_results.png", dpi=200); plt.close(fig)
print("figs done"); print(open(OUT + "pytest_output.txt").read())
