#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-ultrasound-guidance}"
REGION="${REGION:-us-east1}"
SERVICE_NAME="${SERVICE_NAME:-backend}"
VPC_CONNECTOR="${VPC_CONNECTOR:-backend-connector}"
DB_HOST="${DB_HOST:-172.16.0.3}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-postgres}"
DB_USER="${DB_USER:-ug_app}"
DB_PASSWORD_SECRET="${DB_PASSWORD_SECRET:-backend-postgres-password}"
GCS_BUCKET_NAME="${GCS_BUCKET_NAME:-question-bank-media}"
GCS_PROJECT_ID="${GCS_PROJECT_ID:-ultrasound-guidance}"
GHOST_URL="${GHOST_URL:-https://ultrasoundguidance.ghost.io}"
GHOST_ADMIN_KEY_SECRET="${GHOST_ADMIN_KEY_SECRET:-backend-ghost-admin-key}"
ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-http://localhost:5173,https://localhost,https://localhost:5173,http://localhost:2368,http://localhost:3000,https://ug-admin.nikkivaughandev.com,https://ultrasoundguidance.com}"
ADMIN_PORTAL_ORIGIN="${ADMIN_PORTAL_ORIGIN:-}"
DEBUG="${DEBUG:-false}"

if [[ -n "$ADMIN_PORTAL_ORIGIN" ]]; then
  case ",$ALLOWED_ORIGINS," in
    *",$ADMIN_PORTAL_ORIGIN,"*) ;;
    *) ALLOWED_ORIGINS="$ALLOWED_ORIGINS,$ADMIN_PORTAL_ORIGIN" ;;
  esac
fi

env_vars="^#^ALLOWED_ORIGINS=$ALLOWED_ORIGINS#DEBUG=$DEBUG#POSTGRES_SERVER=$DB_HOST#POSTGRES_PORT=$DB_PORT#POSTGRES_DB=$DB_NAME#POSTGRES_USER=$DB_USER#CLOUD_SQL_CONNECTION_NAME=#GCS_BUCKET_NAME=$GCS_BUCKET_NAME#GCS_PROJECT_ID=$GCS_PROJECT_ID#GHOST_URL=$GHOST_URL"

gcloud run deploy "$SERVICE_NAME" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --source . \
  --vpc-connector "$VPC_CONNECTOR" \
  --vpc-egress private-ranges-only \
  --clear-cloudsql-instances \
  --update-env-vars "$env_vars" \
  --update-secrets "POSTGRES_PASSWORD=${DB_PASSWORD_SECRET}:latest,GHOST_ADMIN_KEY=${GHOST_ADMIN_KEY_SECRET}:latest"
