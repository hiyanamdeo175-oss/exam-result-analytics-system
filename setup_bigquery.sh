#!/usr/bin/env bash
# Creates the dataset, table and analytics views.
set -euo pipefail
PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
bq --project_id="$PROJECT_ID" mk --dataset --location=asia-south1 exam_analytics || true
bq --project_id="$PROJECT_ID" mk --table exam_analytics.exam_results bigquery/schema.json || true
bq --project_id="$PROJECT_ID" query --use_legacy_sql=false < bigquery/views.sql
