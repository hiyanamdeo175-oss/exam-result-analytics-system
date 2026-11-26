"""Runs the BigQuery view SQL in DuckDB over the evaluated sample data and
cross-checks the results against an independent pandas calculation."""
import json, os, re, sys, types, time
import duckdb, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [f"{ROOT}/cloud_function", f"{ROOT}/data_generator"]
stub = types.ModuleType("functions_framework"); stub.cloud_event = lambda f: f
sys.modules.setdefault("functions_framework", stub)
import main as cf, generate_results as gen

rows = gen.generate(42)
t0 = time.perf_counter()
evald = []
for r in rows:
    e = cf.evaluate(r); e["result_id"] = f"{r['exam_id']}__{r['student_id']}__{r['subject_code']}"
    evald.append(e)
eval_ms = (time.perf_counter() - t0) * 1000
df = pd.DataFrame(evald)
df["processed_at"] = pd.to_datetime(df["processed_at"])

# simulate a mark correction: S001 / ECE301 re-uploaded with a new value -> 2nd version appended
fix = df[(df.student_id == "S001") & (df.subject_code == "ECE301")].copy()
fix["marks"] = 91.0; fix["percentage"] = 91.0; fix["grade"] = "O"; fix["result_status"] = "PASS"
fix["processed_at"] = fix["processed_at"] + pd.Timedelta(seconds=5)
appended = pd.concat([df, fix], ignore_index=True)

con = duckdb.connect()
con.register("exam_results", appended)
sql = open(f"{ROOT}/bigquery/views.sql").read().replace("exam_analytics.", "")
sql = sql.replace("EXCEPT (rn)", "EXCLUDE (rn)")
for stmt in [s for s in sql.split(";") if s.strip()]:
    con.execute(stmt)

q = lambda v: con.execute(f"SELECT * FROM {v}").df()
latest = q("v_latest_results")
assert len(appended) == 601 and len(latest) == 600, (len(appended), len(latest))
assert latest[(latest.student_id=="S001")&(latest.subject_code=="ECE301")].marks.iloc[0] == 91.0

# use the ORIGINAL data (before correction) for the reported numbers
con.unregister("exam_results"); con.register("exam_results", df)
for stmt in [s for s in sql.split(";") if s.strip()]:
    con.execute(stmt)
subj = q("v_subject_performance").sort_values("subject_code")
cls = q("v_class_summary").sort_values("class_id")
sup = q("v_students_needing_support").sort_values(["subjects_failed","avg_percentage"], ascending=[False,True])
stu = q("v_student_summary")
grades = q("v_grade_distribution")

# independent pandas cross-check
pd_subj = df.groupby("subject_code").agg(avg=("marks","mean"), pas=("result_status", lambda s:(s=="PASS").mean()*100))
for _, r in subj.iterrows():
    assert abs(r.avg_marks - pd_subj.loc[r.subject_code,"avg"]) < 0.01
    assert abs(r.pass_percentage - pd_subj.loc[r.subject_code,"pas"]) < 0.01
pd_fail = df.assign(f=df.result_status=="FAIL").groupby("student_id").f.sum()
pd_avg = df.groupby("student_id").percentage.mean()
pd_support = set(pd_fail[(pd_fail>0)|(pd_avg<50)].index)
assert set(sup.student_id) == pd_support
print("SQL == pandas: OK")

out = dict(
  n_records=len(df), n_students=int(df.student_id.nunique()), eval_ms=round(eval_ms,1),
  overall_avg=round(df.percentage.mean(),2),
  overall_record_pass=round((df.result_status=="PASS").mean()*100,2),
  subj=subj.to_dict("records"), cls=cls.to_dict("records"),
  support=sup.to_dict("records"), grades=grades.to_dict("records"),
  fail_records=int((df.result_status=="FAIL").sum()),
  students_passed_all=int((stu.subjects_failed==0).sum()),
)
json.dump(out, open(f"{ROOT}/analytics_output.json","w"), indent=1, default=str)
df.to_csv(f"{ROOT}/evaluated_results.csv", index=False)
print(json.dumps({k:v for k,v in out.items() if k not in ("support","grades","subj","cls")}, indent=1))
print(subj[["subject_name","avg_marks","highest","lowest","pass_percentage"]].to_string())
print(cls.to_string()); print(len(sup), "need support"); print(sup.reason.value_counts().to_string())
