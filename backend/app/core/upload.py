import os
import magic
from fastapi import HTTPException

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
UPLOAD_DIR = "/app/uploads"
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_image_bytes(data: bytes) -> None:
    """Raises 400 if data is not a real JPEG, PNG or WebP (checked via magic bytes)."""
    mime = magic.from_buffer(data[:2048], mime=True)
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="File must be a real JPEG, PNG or WebP image")


def delete_upload(url: str | None) -> None:
    """Delete a previously stored upload file, ignoring errors."""
    if url and url.startswith("/uploads/"):
        path = os.path.join(UPLOAD_DIR, url.split("/")[-1])
        try:
            os.remove(path)
        except OSError:
            pass
