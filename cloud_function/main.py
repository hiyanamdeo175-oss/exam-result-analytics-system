"""Cloud Function (2nd gen) - Firestore trigger.

Fires whenever a document in the `results` collection is created or updated.
It evaluates the raw marks (percentage, grade, PASS/FAIL) and appends the
enriched record to BigQuery. The table is append-only: if a mark is corrected,
a new version is appended and the BigQuery views keep only the latest one.
"""
import os
from datetime import datetime, timezone

import functions_framework

PASS_PERCENTAGE = float(os.environ.get("PASS_PERCENTAGE", 40))

# (minimum percentage, grade) - checked from the top down
GRADE_BANDS = [
    (90, "O"), (80, "A+"), (70, "A"), (60, "B+"), (50, "B"), (40, "C"),
]

REQUIRED = ("exam_id", "class_id", "student_id", "subject_code",
            "subject_name", "marks", "max_marks")


def grade_for(percentage: float) -> str:
    for floor, grade in GRADE_BANDS:
        if percentage >= floor:
            return grade
    return "F"


def evaluate(record: dict) -> dict:
    """Pure function: raw Firestore record in, analytics-ready row out."""
    missing = [f for f in REQUIRED if record.get(f) in (None, "")]
    if missing:
        raise ValueError(f"missing fields: {', '.join(missing)}")

    marks = float(record["marks"])
    max_marks = float(record["max_marks"])
    if max_marks <= 0 or not 0 <= marks <= max_marks:
        raise ValueError(f"marks {marks} out of range 0..{max_marks}")

    percentage = round(100.0 * marks / max_marks, 2)
    return {
        "exam_id": record["exam_id"],
        "class_id": record["class_id"],
        "student_id": record["student_id"],
        "subject_code": record["subject_code"],
        "subject_name": record["subject_name"],
        "marks": marks,
        "max_marks": max_marks,
        "percentage": percentage,
        "grade": grade_for(percentage),
        "result_status": "PASS" if percentage >= PASS_PERCENTAGE else "FAIL",
        "submitted_at": record.get("submitted_at"),
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }


def _decode_fields(fields) -> dict:
    """Convert Firestore protobuf Value objects into plain, JSON-serialisable Python values."""
    out = {}
    for name, value in fields.items():
        kind = value._pb.WhichOneof("value_type")
        raw = getattr(value._pb, kind)
        if kind == "timestamp_value":              # protobuf Timestamp -> ISO-8601 string (UTC)
            raw = raw.ToDatetime().isoformat() + "Z"
        elif kind == "null_value":
            raw = None
        out[name] = raw
    return out


@functions_framework.cloud_event
def process_result(cloud_event):
    from google.cloud import bigquery
    from google.events.cloud import firestore as firestoredata

    payload = firestoredata.DocumentEventData()
    payload._pb.ParseFromString(cloud_event.data)

    if not payload.value.fields:          # document was deleted - nothing to do
        return

    record = _decode_fields(payload.value.fields)
    row = evaluate(record)
    row["result_id"] = cloud_event["subject"].split("/")[-1]

    table = os.environ["BQ_TABLE"]        # e.g. project.exam_analytics.exam_results
    errors = bigquery.Client().insert_rows_json(
        table, [row], row_ids=[cloud_event["id"]])   # event id -> de-duplicates retries
    if errors:
        raise RuntimeError(f"BigQuery insert failed: {errors}")
    print(f"processed {row['result_id']} -> {row['grade']} ({row['result_status']})")
