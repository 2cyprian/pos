"""Security utilities for file sanitization and validation"""
import os
import re
from pathlib import Path


ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path separators
    filename = os.path.basename(filename)
    
    # Remove special characters except dots and hyphens
    filename = re.sub(r'[^\w\s.-]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Limit length
    name, ext = os.path.splitext(filename)
    name = name[:200]
    return name + ext


def validate_file_extension(filename: str) -> bool:
    """
    Validate if file extension is allowed.
    
    Args:
        filename: Filename to validate
        
    Returns:
        True if valid, False otherwise
    """
    file_ext = Path(filename).suffix.lower()
    return file_ext in ALLOWED_EXTENSIONS


def validate_file_size(file_size: int) -> bool:
    """
    Validate if file size is within limits.
    
    Args:
        file_size: File size in bytes
        
    Returns:
        True if valid, False otherwise
    """
    return 0 < file_size <= MAX_FILE_SIZE


def get_safe_upload_path(filename: str, upload_dir: str = "static/uploads") -> Path:
    """
    Get a safe path for file upload.
    
    Args:
        filename: Original filename
        upload_dir: Upload directory
        
    Returns:
        Safe path for file
    """
    safe_filename = sanitize_filename(filename)
    return Path(upload_dir) / safe_filename
