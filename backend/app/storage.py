from fastapi import HTTPException
from google.cloud import storage

from app.core.config import settings


def get_bucket():
    if not settings.GCS_PROJECT_ID or not settings.GCS_BUCKET_NAME:
        raise HTTPException(
            status_code=503,
            detail="Google Cloud Storage is not configured for this service.",
        )

    client = storage.Client(project=settings.GCS_PROJECT_ID)
    return client.bucket(settings.GCS_BUCKET_NAME)
