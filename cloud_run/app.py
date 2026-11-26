"""Cloud Run service - ingestion + analytics REST API.

POST /results               store one result or a batch of results in Firestore
GET  /analytics/subjects    subject-wise performance      (from BigQuery view)
GET  /analytics/classes     class averages / pass %       (from BigQuery view)
GET  /analytics/support     students requiring support    (from BigQuery view)
GET  /health                liveness probe
"""
import os
from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__)

DATASET = os.environ.get("BQ_DATASET", "exam_analytics")
REQUIRED = ("exam_id", "class_id", "student_id", "subject_code",
            "subject_name", "marks", "max_marks")


def validate(record: dict):
    """Return (clean_record, error_message). Exactly one of them is None."""
    if not isinstance(record, dict):
        return None, "each result must be a JSON object"
    missing = [f for f in REQUIRED if record.get(f) in (None, "")]
    if missing:
        return None, f"missing fields: {', '.join(missing)}"
    try:
        marks, max_marks = float(record["marks"]), float(record["max_marks"])
    except (TypeError, ValueError):
        return None, "marks and max_marks must be numbers"
    if max_marks <= 0 or not 0 <= marks <= max_marks:
        return None, f"marks must be between 0 and {max_marks:g}"
    clean = {k: str(record[k]).strip() for k in REQUIRED if k not in ("marks", "max_marks")}
    clean.update(marks=marks, max_marks=max_marks,
                 submitted_at=datetime.now(timezone.utc))
    return clean, None


def doc_id(rec: dict) -> str:
    # deterministic id -> re-uploading the same student/subject updates, not duplicates
    return f"{rec['exam_id']}__{rec['student_id']}__{rec['subject_code']}"


@app.get("/")
def dashboard():
    return send_from_directory(os.path.dirname(__file__), "dashboard.html")


@app.get("/dashboard-data")
def dashboard_data():
    import json
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "analytics_output.json")
    with open(path, encoding="utf-8") as f:
        return jsonify(json.load(f))


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.post("/results")
def add_results():
    body = request.get_json(silent=True)
    if body is None:
        return jsonify(error="body must be JSON"), 400
    records = body if isinstance(body, list) else [body]
    if not 0 < len(records) <= 500:
        return jsonify(error="send between 1 and 500 results per request"), 400

    cleaned = []
    for i, rec in enumerate(records):
        clean, err = validate(rec)
        if err:
            return jsonify(error=f"record {i}: {err}"), 422
        cleaned.append(clean)

    from google.cloud import firestore      # imported only once the payload is valid

    db = firestore.Client()
    batch = db.batch()
    for clean in cleaned:
        batch.set(db.collection("results").document(doc_id(clean)), clean)
    batch.commit()
    return jsonify(stored=len(cleaned)), 201


def _query_view(view: str, exam_id: str | None):
    from google.cloud import bigquery

    client = bigquery.Client()
    sql = f"SELECT * FROM `{client.project}.{DATASET}.{view}`"
    params = []
    if exam_id:
        sql += " WHERE exam_id = @exam_id"
        params.append(bigquery.ScalarQueryParameter("exam_id", "STRING", exam_id))
    job = client.query(sql, job_config=bigquery.QueryJobConfig(query_parameters=params))
    return [dict(row) for row in job.result()]


@app.get("/analytics/<name>")
def analytics(name):
    views = {"subjects": "v_subject_performance",
             "classes": "v_class_summary",
             "support": "v_students_needing_support"}
    if name not in views:
        return jsonify(error="unknown analytics report"), 404
    return jsonify(_query_view(views[name], request.args.get("exam_id")))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
