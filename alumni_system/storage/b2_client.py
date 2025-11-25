"""
Backblaze B2 storage client for managing PDF files.
"""

import os
from datetime import datetime
from typing import Optional

from b2sdk.v2 import B2Api, InMemoryAccountInfo

from .config import (
    ALLOWED_FILE_TYPES,
    MAX_FILE_SIZE_MB,
    PDF_FOLDER_PREFIX,
    get_b2_credentials,
)


class B2StorageClient:
    """
    Client for interacting with Backblaze B2 storage.
    
    Provides methods for uploading, downloading, and managing PDF files.
    """

    def __init__(self):
        """Initialize the B2 storage client."""
        self._api: Optional[B2Api] = None
        self._bucket = None

    def _get_api(self) -> B2Api:
        """
        Get or create the B2 API instance.
        
        Returns:
            Authenticated B2Api instance.
        """
        if self._api is None:
            credentials = get_b2_credentials()
            info = InMemoryAccountInfo()
            self._api = B2Api(info)
            self._api.authorize_account(
                "production",
                credentials["application_key_id"],
                credentials["application_key"],
            )
        return self._api

    def _get_bucket(self):
        """
        Get or create the bucket instance.
        
        Returns:
            B2 Bucket instance.
        """
        if self._bucket is None:
            api = self._get_api()
            credentials = get_b2_credentials()
            self._bucket = api.get_bucket_by_name(credentials["bucket_name"])
        return self._bucket

    def upload_pdf(
        self,
        file_path: str,
        alumni_id: int,
        linkedin_id: str,
    ) -> dict:
        """
        Upload a PDF file to B2 storage.
        
        Args:
            file_path: Local path to the PDF file.
            alumni_id: ID of the alumni record.
            linkedin_id: LinkedIn ID for naming the file.
        
        Returns:
            Dictionary with upload details including file URL.
        
        Raises:
            ValueError: If file is not a PDF or exceeds size limit.
            FileNotFoundError: If file does not exist.
        """
        # Validate file
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in ALLOWED_FILE_TYPES:
            raise ValueError(f"Invalid file type: {file_ext}. Allowed: {ALLOWED_FILE_TYPES}")
        
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise ValueError(
                f"File size ({file_size_mb:.2f}MB) exceeds limit ({MAX_FILE_SIZE_MB}MB)"
            )
        
        # Generate B2 file name
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        b2_file_name = f"{PDF_FOLDER_PREFIX}{alumni_id}/{linkedin_id}_{timestamp}.pdf"
        
        # Upload file
        bucket = self._get_bucket()
        with open(file_path, "rb") as f:
            file_version = bucket.upload_bytes(
                f.read(),
                b2_file_name,
                content_type="application/pdf",
            )
        
        # Get download URL
        download_url = self._api.get_download_url_for_fileid(file_version.id_)
        
        return {
            "file_id": file_version.id_,
            "file_name": b2_file_name,
            "download_url": download_url,
            "size_bytes": file_version.size,
            "uploaded_at": datetime.utcnow().isoformat(),
        }

    def upload_pdf_bytes(
        self,
        pdf_bytes: bytes,
        alumni_id: int,
        linkedin_id: str,
    ) -> dict:
        """
        Upload PDF content from bytes to B2 storage.
        
        Args:
            pdf_bytes: PDF file content as bytes.
            alumni_id: ID of the alumni record.
            linkedin_id: LinkedIn ID for naming the file.
        
        Returns:
            Dictionary with upload details including file URL.
        
        Raises:
            ValueError: If content exceeds size limit.
        """
        # Validate size
        size_mb = len(pdf_bytes) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise ValueError(
                f"Content size ({size_mb:.2f}MB) exceeds limit ({MAX_FILE_SIZE_MB}MB)"
            )
        
        # Generate B2 file name
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        b2_file_name = f"{PDF_FOLDER_PREFIX}{alumni_id}/{linkedin_id}_{timestamp}.pdf"
        
        # Upload content
        bucket = self._get_bucket()
        file_version = bucket.upload_bytes(
            pdf_bytes,
            b2_file_name,
            content_type="application/pdf",
        )
        
        # Get download URL
        download_url = self._api.get_download_url_for_fileid(file_version.id_)
        
        return {
            "file_id": file_version.id_,
            "file_name": b2_file_name,
            "download_url": download_url,
            "size_bytes": file_version.size,
            "uploaded_at": datetime.utcnow().isoformat(),
        }

    def download_pdf(self, file_id: str, destination_path: str) -> str:
        """
        Download a PDF file from B2 storage.
        
        Args:
            file_id: B2 file ID.
            destination_path: Local path to save the file.
        
        Returns:
            Path to the downloaded file.
        """
        bucket = self._get_bucket()
        downloaded_file = bucket.download_file_by_id(file_id)
        downloaded_file.save_to(destination_path)
        return destination_path

    def delete_pdf(self, file_id: str, file_name: str) -> bool:
        """
        Delete a PDF file from B2 storage.
        
        Args:
            file_id: B2 file ID.
            file_name: B2 file name.
        
        Returns:
            True if deleted successfully.
        """
        api = self._get_api()
        api.delete_file_version(file_id, file_name)
        return True

    def list_alumni_pdfs(self, alumni_id: int) -> list[dict]:
        """
        List all PDFs for a specific alumni.
        
        Args:
            alumni_id: ID of the alumni.
        
        Returns:
            List of file info dictionaries.
        """
        bucket = self._get_bucket()
        prefix = f"{PDF_FOLDER_PREFIX}{alumni_id}/"
        
        files = []
        for file_version, _ in bucket.ls(folder_to_list=prefix):
            files.append({
                "file_id": file_version.id_,
                "file_name": file_version.file_name,
                "size_bytes": file_version.size,
                "upload_timestamp": file_version.upload_timestamp,
            })
        
        return files

    def get_download_url(self, file_id: str) -> str:
        """
        Get a download URL for a file.
        
        Args:
            file_id: B2 file ID.
        
        Returns:
            Download URL string.
        """
        api = self._get_api()
        return api.get_download_url_for_fileid(file_id)


# Global client instance
_storage_client: Optional[B2StorageClient] = None


def get_storage_client() -> B2StorageClient:
    """
    Get the global storage client instance.
    
    Returns:
        B2StorageClient instance.
    """
    global _storage_client
    if _storage_client is None:
        _storage_client = B2StorageClient()
    return _storage_client
