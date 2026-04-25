import uuid
from datetime import timedelta

from fastapi import APIRouter, HTTPException

from app.db.database import SessionDep
from app.models import Question
from app.storage import get_bucket, get_signing_credentials


router = APIRouter(prefix="/media", tags=["media"])


@router.post("/upload-url")
def generate_upload_url(question_id: uuid.UUID, content_type: str, session: SessionDep):
    """Uploads a file to the bucket."""
    # Verify question exists
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    filename = f"questions/{question_id}"
    blob = get_bucket().blob(filename)

    upload_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=15),
        method="PUT",
        content_type=content_type,
        credentials=get_signing_credentials(),
    )

    # Persist the content type so we know media exists
    question.media_content_type = content_type
    session.add(question)
    session.commit()

    return {"upload_url": upload_url, "gcs_path": filename}


@router.get("/download-url")
def generate_download_url(question_id: uuid.UUID, session: SessionDep):
    """Generate a signed download URL for a question's media."""
    # Verify question exists
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Check if question has media
    if not question.media_content_type:
        return {
            "download_url": None,
            "gcs_path": None,
            "content_type": None,
        }

    # Derive path from question ID
    gcs_path = f"questions/{question_id}"

    # Get the blob from storage
    blob = get_bucket().blob(gcs_path)

    # Check if blob exists
    if not blob.exists():
        # Clear stale metadata when object no longer exists in storage.
        question.media_content_type = None
        session.add(question)
        session.commit()
        return {
            "download_url": None,
            "gcs_path": None,
            "content_type": None,
        }

    # Generate signed download URL
    download_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=15),
        method="GET",
        credentials=get_signing_credentials(),
    )

    return {
        "download_url": download_url,
        "gcs_path": gcs_path,
        "content_type": question.media_content_type,
    }


# curl - X PUT \
#     - H "Content-Type: image/png" \
#     - H "Authorization: Bearer $(gcloud auth print-access-token)" \
#     --upload-file <IMAGE PATH> \
#     "<SIGNED_UPLOAD_URL>"
