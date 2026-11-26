"""Generate a reproducible synthetic exam-result dataset and (optionally)
upload it to the Cloud Run API.

    python generate_results.py                       # writes results.csv
    python generate_results.py --url https://<run-url>   # also POSTs in batches
"""
import argparse
import csv
import json
import random
import urllib.request

EXAM_ID = "MID-SEM-2026"
CLASSES = {"ECE-A": 60, "ECE-B": 60}
SUBJECTS = [                       # code, name, difficulty offset (marks)
    ("ECE301", "Digital Signal Processing", -6),
    ("ECE302", "Microprocessors", 0),
    ("ECE303", "Control Systems", -3),
    ("ECE304", "Data Structures", 4),
    ("ECE305", "Engineering Mathematics", -2),
]
MAX_MARKS = 100


def generate(seed: int = 42):
    rng = random.Random(seed)
    rows, n = [], 0
    for class_id, size in CLASSES.items():
        class_shift = 2 if class_id == "ECE-A" else -2
        for _ in range(size):
            n += 1
            student_id = f"S{n:03d}"
            ability = rng.gauss(66, 12) + class_shift          # student's overall level
            for code, name, offset in SUBJECTS:
                marks = round(min(100, max(0, rng.gauss(ability + offset, 8))))
                rows.append(dict(exam_id=EXAM_ID, class_id=class_id, student_id=student_id,
                                 subject_code=code, subject_name=name,
                                 marks=marks, max_marks=MAX_MARKS))
    return rows


def post_batches(rows, url, size=200):
    for i in range(0, len(rows), size):
        req = urllib.request.Request(f"{url}/results", method="POST",
                                     data=json.dumps(rows[i:i + size]).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            print(resp.status, resp.read().decode())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="Cloud Run service URL")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    data = generate(args.seed)
    with open("results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0]))
        w.writeheader()
        w.writerows(data)
    print(f"wrote {len(data)} records to results.csv")
    if args.url:
        post_batches(data, args.url.rstrip("/"))
