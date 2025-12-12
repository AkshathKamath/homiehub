import uuid
from typing import List
from fastapi import UploadFile, HTTPException, status
from google.cloud import storage

from app.config import settings, GCS_BUCKET_NAME

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_PHOTOS = 10
MAX_FILE_SIZE_MB = 5

_storage_client = storage.Client(project=settings.google_cloud_project)

def get_bucket():
    return _storage_client.bucket(GCS_BUCKET_NAME)

async def upload_room_photos(room_id: str, files: List[UploadFile]) -> List[str]:
    if not files:
        return []

    if len(files) > MAX_PHOTOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 photos allowed"
        )

    bucket = get_bucket()
    urls: List[str] = []

    for file in files:
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}"
            )

        content = await file.read()
        if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="File exceeds 5MB limit"
            )

        ext = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp"
        }[file.content_type]

        object_name = f"rooms/{room_id}/{uuid.uuid4().hex}.{ext}"
        blob = bucket.blob(object_name)

        blob.upload_from_string(content, content_type=file.content_type)

        # For buckets with uniform bucket-level access, public_url should work
        # if the bucket is configured for public access
        urls.append(blob.public_url)

    return urls
