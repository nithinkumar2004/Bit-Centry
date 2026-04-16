"""
File handling utilities — save, hash, and detect uploaded files.
"""
import os
import hashlib
import uuid
from pathlib import Path
from typing import Tuple

from dotenv import load_dotenv

load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


def ensure_upload_dir():
    """Create upload directory if it doesn't exist."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_DIR, "tenders"), exist_ok=True)
    os.makedirs(os.path.join(UPLOAD_DIR, "bidders"), exist_ok=True)


def save_uploaded_file(file_content: bytes, original_filename: str, subdir: str = "") -> Tuple[str, str]:
    """
    Save an uploaded file with a unique name.
    
    Returns:
        Tuple of (file_path, file_hash)
    """
    ensure_upload_dir()
    
    ext = Path(original_filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    
    save_dir = os.path.join(UPLOAD_DIR, subdir) if subdir else UPLOAD_DIR
    os.makedirs(save_dir, exist_ok=True)
    
    file_path = os.path.join(save_dir, unique_name)
    
    with open(file_path, "wb") as f:
        f.write(file_content)

    file_hash = compute_file_hash(file_content)
    
    return file_path, file_hash


def compute_file_hash(content: bytes) -> str:
    """Compute SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


def detect_file_type(filename: str) -> str:
    """Detect if file is PDF or image based on extension."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    elif ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"):
        return "image"
    else:
        return "unknown"


def get_file_path(filename: str, subdir: str = "") -> str:
    """Get full path for a file in the upload directory."""
    if subdir:
        return os.path.join(UPLOAD_DIR, subdir, filename)
    return os.path.join(UPLOAD_DIR, filename)
