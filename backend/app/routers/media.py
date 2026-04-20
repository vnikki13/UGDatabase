import uuid
from datetime import timedelta

from fastapi import APIRouter, HTTPException

from app.db.database import SessionDep
from app.models import Question
from app.storage import get_bucket


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
    )

    # Save media information to question
    question.media_storage_path = filename
    question.media_content_type = content_type
    session.add(question)
    session.commit()
    session.refresh(question)

    return {"upload_url": upload_url, "gcs_path": filename}


@router.get("/download-url")
def generate_download_url(question_id: uuid.UUID, session: SessionDep):
    """Generate a signed download URL for a question's media."""
    # Verify question exists
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Check if question has media
    if not question.media_storage_path:
        raise HTTPException(status_code=404, detail="Question has no media")

    # Get the blob from storage
    blob = get_bucket().blob(f"{question.media_storage_path}")

    # Check if blob exists
    if not blob.exists():
        raise HTTPException(status_code=404, detail="Media file not found in storage")

    # Generate signed download URL
    download_url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=15),
        method="GET",
    )

    return {
        "download_url": download_url,
        "gcs_path": question.media_storage_path,
        "content_type": question.media_content_type,
    }


# curl - X PUT \
#     - H "Content-Type: image/png" \
#     - H "Authorization: Bearer $(gcloud auth print-access-token)" \
#     --upload-file <IMAGE PATH> \
#     "<SIGNED_UPLOAD_URL>"
