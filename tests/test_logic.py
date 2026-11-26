import os
import sys
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path[:0] = [os.path.join(ROOT, "cloud_function"), os.path.join(ROOT, "cloud_run"),
                os.path.join(ROOT, "data_generator")]

# functions_framework is only needed on GCP; stub it so the pure logic can be tested locally
try:
    import functions_framework  # noqa: F401
except ImportError:
    stub = types.ModuleType("functions_framework")
    stub.cloud_event = lambda f: f
    sys.modules["functions_framework"] = stub

import main as cf                      # cloud function
import app as api                      # cloud run
import generate_results as gen

BASE = dict(exam_id="E1", class_id="ECE-A", student_id="S001", subject_code="ECE301",
            subject_name="DSP", marks=72, max_marks=100)


# ---------- Cloud Function: evaluate() ----------
@pytest.mark.parametrize("marks,grade,status", [
    (100, "O", "PASS"), (90, "O", "PASS"), (89, "A+", "PASS"), (80, "A+", "PASS"),
    (70, "A", "PASS"), (60, "B+", "PASS"), (50, "B", "PASS"),
    (40, "C", "PASS"), (39, "F", "FAIL"), (0, "F", "FAIL"),
])
def test_grade_and_status_boundaries(marks, grade, status):
    row = cf.evaluate({**BASE, "marks": marks})
    assert row["grade"] == grade and row["result_status"] == status


def test_percentage_uses_max_marks():
    assert cf.evaluate({**BASE, "marks": 21, "max_marks": 50})["percentage"] == 42.0


@pytest.mark.parametrize("bad", [
    {"marks": 101}, {"marks": -1}, {"max_marks": 0}, {"student_id": ""}, {"subject_code": None},
])
def test_evaluate_rejects_bad_records(bad):
    with pytest.raises(ValueError):
        cf.evaluate({**BASE, **bad})


# ---------- Cloud Run: validate() ----------
def test_validate_accepts_and_cleans():
    clean, err = api.validate({**BASE, "student_id": " S001 ", "marks": "72"})
    assert err is None and clean["student_id"] == "S001" and clean["marks"] == 72.0


@pytest.mark.parametrize("bad", [{"marks": "abc"}, {"marks": 150}, {"exam_id": ""}])
def test_validate_rejects(bad):
    clean, err = api.validate({**BASE, **bad})
    assert clean is None and err


def test_doc_id_is_deterministic():
    assert api.doc_id(BASE) == "E1__S001__ECE301"


def test_api_endpoints_without_gcp():
    client = api.app.test_client()
    assert client.get("/health").get_json() == {"status": "ok"}
    assert client.post("/results", data="not json").status_code == 400
    assert client.post("/results", json=[{**BASE, "marks": 500}]).status_code == 422
    assert client.get("/analytics/unknown").status_code == 404


# ---------- Generator ----------
def test_generator_is_reproducible_and_valid():
    a, b = gen.generate(7), gen.generate(7)
    assert a == b and len(a) == 120 * 5
    assert all(0 <= r["marks"] <= r["max_marks"] for r in a)


# ---------- Cloud Function: Firestore event decoding ----------
def test_decode_fields_handles_strings_numbers_and_timestamps():
    from types import SimpleNamespace
    from google.protobuf.timestamp_pb2 import Timestamp

    def val(kind, raw):
        return SimpleNamespace(_pb=SimpleNamespace(WhichOneof=lambda _: kind, **{kind: raw}))

    ts = Timestamp(); ts.FromJsonString("2026-09-19T10:30:00Z")
    fields = {"student_id": val("string_value", "S001"), "marks": val("double_value", 72.0),
              "max_marks": val("integer_value", 100), "submitted_at": val("timestamp_value", ts)}
    out = cf._decode_fields(fields)
    assert out == {"student_id": "S001", "marks": 72.0, "max_marks": 100,
                   "submitted_at": "2026-09-19T10:30:00Z"}
    import json; json.dumps(out)          # must be JSON-serialisable for insert_rows_json
