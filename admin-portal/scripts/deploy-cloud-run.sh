#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-ultrasound-guidance}"
REGION="${REGION:-us-east1}"
SERVICE_NAME="${SERVICE_NAME:-admin-portal}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${SOURCE_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"

if [[ -z "${VITE_API_URL:-}" ]]; then
  echo "Error: VITE_API_URL is required."
  echo "Example: VITE_API_URL=https://backend-abc123-ue.a.run.app $0"
  exit 1
fi

if [[ -z "${VITE_GCS_CLIENT_ID:-}" ]]; then
  echo "Error: VITE_GCS_CLIENT_ID is required."
  echo "Example: VITE_GCS_CLIENT_ID=<google-oauth-web-client-id> $0"
  exit 1
fi

if [[ "${ALLOW_UNAUTHENTICATED:-true}" == "true" ]]; then
  AUTH_FLAG="--allow-unauthenticated"
else
  AUTH_FLAG="--no-allow-unauthenticated"
fi

echo "Deploying ${SERVICE_NAME} to Cloud Run"
echo "  Project: ${PROJECT_ID}"
echo "  Region: ${REGION}"
echo "  Source: ${SOURCE_DIR}"
echo "  VITE_API_URL: ${VITE_API_URL}"
echo "  VITE_GCS_CLIENT_ID: ${VITE_GCS_CLIENT_ID}"

gcloud run deploy "$SERVICE_NAME" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --source "$SOURCE_DIR" \
  --set-build-env-vars "VITE_API_URL=${VITE_API_URL},VITE_GCS_CLIENT_ID=${VITE_GCS_CLIENT_ID}" \
  --set-env-vars "NODE_ENV=production" \
  $AUTH_FLAG
