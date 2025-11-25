"""
Backblaze B2 storage configuration.
Uses environment variables for credentials.
"""

import os


def get_b2_credentials() -> dict:
    """
    Get Backblaze B2 credentials from environment variables.
    
    Required environment variables:
        - B2_APPLICATION_KEY_ID: Application key ID
        - B2_APPLICATION_KEY: Application key (secret)
        - B2_BUCKET_NAME: Name of the bucket to use
        - B2_BUCKET_ID: ID of the bucket (optional, for some operations)
    
    Returns:
        Dictionary containing B2 credentials.
    """
    return {
        "application_key_id": os.environ.get("B2_APPLICATION_KEY_ID", ""),
        "application_key": os.environ.get("B2_APPLICATION_KEY", ""),
        "bucket_name": os.environ.get("B2_BUCKET_NAME", "alumni-pdfs"),
        "bucket_id": os.environ.get("B2_BUCKET_ID", ""),
    }


# File storage settings
PDF_FOLDER_PREFIX = "linkedin_pdfs/"
MAX_FILE_SIZE_MB = 10
ALLOWED_FILE_TYPES = [".pdf"]
