# Cloud-Based Examination Result Analytics System

Serverless result storage, analytics and dashboarding on Google Cloud Platform.

    Result upload -> Cloud Run API -> Firestore -> Cloud Function -> BigQuery -> Looker Studio

| Folder / file          | Purpose                                                                 |
|------------------------|-------------------------------------------------------------------------|
| `cloud_run/`           | Flask API (ingestion `POST /results`, analytics `GET /analytics/*`) + Dockerfile |
| `cloud_function/`      | Firestore-triggered function: grades each result and appends it to BigQuery |
| `bigquery/`            | `schema.json` (table) and `views.sql` (analytics views)                 |
| `data_generator/`      | Seeded synthetic dataset generator / batch uploader                      |
| `tests/`               | 24 pytest cases + SQL cross-check (`run_sql_check.py`)                   |
| `deploy.sh`, `setup_bigquery.sh` | One-shot deployment scripts                                    |

## Run locally (no GCP needed)
    pip install pytest flask duckdb pandas
    python -m pytest tests -v
    python tests/run_sql_check.py

## Deploy
    export PROJECT_ID=<your-project>
    ./deploy.sh
    python data_generator/generate_results.py --url <cloud-run-url>

Then connect Looker Studio to the BigQuery views (see `looker_studio_guide.md`).
