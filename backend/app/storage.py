from google.cloud import storage
from .core.config import settings

client = storage.Client()
bucket = client.bucket(settings.GCS_BUCKET_NAME)
