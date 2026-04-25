import os

from fastapi import HTTPException
from google.auth import default, iam
from google.auth.credentials import Signing
from google.auth.transport.requests import Request
from google.cloud import storage
from google.oauth2 import service_account
import requests


from app.core.config import settings


def _is_email_in_project(service_account_email: str) -> bool:
    if not settings.GCS_PROJECT_ID:
        return True

    project_domain = f"@{settings.GCS_PROJECT_ID}.iam.gserviceaccount.com"
    return service_account_email.endswith(project_domain)


def get_storage_client() -> storage.Client:
    if not settings.GCS_PROJECT_ID:
        raise HTTPException(
            status_code=503,
            detail="Google Cloud Storage project is not configured.",
        )

    return storage.Client(project=settings.GCS_PROJECT_ID)


def get_service_account_email(credentials) -> str:
    service_account_email = getattr(credentials, "service_account_email", None)
    if (
        service_account_email
        and service_account_email != "default"
        and _is_email_in_project(service_account_email)
    ):
        return service_account_email

    configured_email = (
        settings.GOOGLE_SERVICE_ACCOUNT_EMAIL
        or os.getenv("GOOGLE_SERVICE_ACCOUNT_EMAIL")
        or os.getenv("SERVICE_ACCOUNT_EMAIL")
    )
    if configured_email:
        return configured_email

    try:
        response = requests.get(
            "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email",
            headers={"Metadata-Flavor": "Google"},
            timeout=3,
        )
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Unable to determine the runtime service account email for signed URLs. "
                "Set GOOGLE_SERVICE_ACCOUNT_EMAIL or run on Cloud Run with metadata access enabled."
            ),
        ) from exc


def get_signing_credentials() -> Signing:
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])

    if isinstance(credentials, Signing):
        return credentials

    service_account_email = get_service_account_email(credentials)
    if not service_account_email:
        raise HTTPException(
            status_code=503,
            detail=(
                "Cloud Storage signed URLs require signing credentials. "
                "On Cloud Run, use a service account with signBlob support. "
                "For local development, authenticate via Application Default Credentials "
                "and set GOOGLE_SERVICE_ACCOUNT_EMAIL when needed."
            ),
        )

    signer = iam.Signer(Request(), credentials, service_account_email)
    return service_account.Credentials(
        signer=signer,
        service_account_email=service_account_email,
        token_uri="https://oauth2.googleapis.com/token",
    )


def get_bucket():
    if not settings.GCS_PROJECT_ID or not settings.GCS_BUCKET_NAME:
        raise HTTPException(
            status_code=503,
            detail="Google Cloud Storage is not configured.",
        )

    client = get_storage_client()
    return client.bucket(settings.GCS_BUCKET_NAME)


def delete_media(media_storage_path: str) -> None:
    if not media_storage_path:
        return

    try:
        bucket = get_bucket()
        blob = bucket.blob(media_storage_path)
        blob.delete()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete media from storage: {str(exc)}",
        ) from exc
