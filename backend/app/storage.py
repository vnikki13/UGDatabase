from google.cloud import storage
from app.core.config import settings

client = storage.Client(project=settings.GCS_PROJECT_ID)
bucket = client.bucket(settings.GCS_BUCKET_NAME)
