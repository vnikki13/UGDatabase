#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-ultrasound-guidance}"
REGION="${REGION:-us-east1}"
SERVICE_NAME="${SERVICE_NAME:-admin-portal}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${SOURCE_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
ENV_FILE="${ENV_FILE:-$SOURCE_DIR/.env}"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

if [[ "${ALLOW_UNAUTHENTICATED:-true}" == "true" ]]; then
  AUTH_FLAG="--allow-unauthenticated"
else
  AUTH_FLAG="--no-allow-unauthenticated"
fi

VITE_GCS_CLIENT_ID="${VITE_GCS_CLIENT_ID:-947728965057-a48qnufhbpcr3vovmk0d4r1unhd3lepk.apps.googleusercontent.com}"
VITE_API_URL="${VITE_API_URL:-https://backend-947728965057.us-east1.run.app/api/v1}"

if [[ -z "$VITE_API_URL" || -z "$VITE_GCS_CLIENT_ID" ]]; then
  echo "Error: VITE_API_URL and VITE_GCS_CLIENT_ID must be set (via $ENV_FILE or environment variables)."
  exit 1
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
