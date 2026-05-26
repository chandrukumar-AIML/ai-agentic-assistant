"""
Safe file upload reading with size limit.
Prevents DoS via unbounded file.read() on large uploads.
"""
from fastapi import UploadFile, HTTPException


async def read_upload_limited(file: UploadFile, max_bytes: int) -> bytes:
    """
    Read an uploaded file up to max_bytes.
    Raises HTTP 413 if the file exceeds the limit.
    """
    chunks: list[bytes] = []
    total = 0
    chunk_size = 64 * 1024  # 64 KB chunks

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum allowed size is {max_bytes // (1024*1024)} MB.",
            )
        chunks.append(chunk)

    return b"".join(chunks)
