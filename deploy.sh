#!/usr/bin/env bash
# One-shot deployment of the Cloud Run API and the Firestore-triggered Cloud Function.
set -euo pipefail
PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
REGION="asia-south1"

gcloud config set project "$PROJECT_ID"
gcloud services enable run.googleapis.com cloudfunctions.googleapis.com firestore.googleapis.com \
    bigquery.googleapis.com eventarc.googleapis.com cloudbuild.googleapis.com

# Firestore (native mode) - skip if it already exists
gcloud firestore databases create --location="$REGION" --type=firestore-native || true

# BigQuery dataset, table and views
./setup_bigquery.sh

# Cloud Run - ingestion + analytics API
gcloud run deploy exam-results-api --source cloud_run --region "$REGION" \
    --allow-unauthenticated --set-env-vars BQ_DATASET=exam_analytics

# Cloud Function - fires on every write to results/{docId}
gcloud functions deploy process-exam-result --gen2 --runtime python312 --region "$REGION" \
    --source cloud_function --entry-point process_result \
    --trigger-location "$REGION" \
    --trigger-event-filters="type=google.cloud.firestore.document.v1.written" \
    --trigger-event-filters="database=(default)" \
    --trigger-event-filters-path-pattern="document=results/{docId}" \
    --set-env-vars BQ_TABLE="$PROJECT_ID.exam_analytics.exam_results"
