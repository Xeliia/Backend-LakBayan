"""
Supabase Storage Backup Utility

This module provides functionality to backup transportation data to Supabase Storage.
Used by both GitHub Actions (scheduled) and Django Admin (manual trigger).
"""

import json
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SupabaseBackupError(Exception):
    """Custom exception for Supabase backup errors"""
    pass


class SupabaseBackup:
    """
    Handles backup of transportation data to Supabase Storage.
    
    Environment variables required:
        - SUPABASE_URL: Your Supabase project URL
        - SUPABASE_SERVICE_KEY: Supabase service role key (for storage access)
        - SUPABASE_BUCKET_NAME: Name of the storage bucket (default: 'transport-backups')
    """
    
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        bucket_name: Optional[str] = None
    ):
        """
        Initialize the Supabase backup client.
        
        Args:
            supabase_url: Supabase project URL (or from env SUPABASE_URL)
            supabase_key: Supabase service role key (or from env SUPABASE_SERVICE_KEY)
            bucket_name: Storage bucket name (or from env SUPABASE_BUCKET_NAME)
        """
        self.supabase_url = supabase_url or os.environ.get('SUPABASE_URL')
        self.supabase_key = supabase_key or os.environ.get('SUPABASE_SERVICE_KEY')
        self.bucket_name = bucket_name or os.environ.get('SUPABASE_BUCKET_NAME', 'transport-backups')
        
        if not self.supabase_url:
            raise SupabaseBackupError("SUPABASE_URL is required")
        if not self.supabase_key:
            raise SupabaseBackupError("SUPABASE_SERVICE_KEY is required")
        
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of Supabase client"""
        if self._client is None:
            try:
                from supabase import create_client, Client
                self._client: Client = create_client(self.supabase_url, self.supabase_key)
            except ImportError:
                raise SupabaseBackupError(
                    "supabase package not installed. Run: pip install supabase"
                )
            except Exception as e:
                raise SupabaseBackupError(f"Failed to create Supabase client: {str(e)}")
        return self._client
    
    def get_default_filename(self) -> str:
        """
        Get the default filename for the backup.
        
        Returns:
            Default filename 'transport_data.json'
        """
        return "transport_data.json"
    
    def upload_json(
        self,
        data: dict,
        filename: str = "transport_data.json",
        folder: str = ""
    ) -> dict:
        """
        Upload JSON data to Supabase Storage.
        
        Args:
            data: Dictionary to upload as JSON
            filename: Filename to use (default: transport_data.json)
            folder: Optional folder path within the bucket
            
        Returns:
            dict with 'success', 'filename', 'path', and 'message' keys
        """
        
        # Construct the full path
        file_path = f"{folder}/{filename}" if folder else filename
        file_path = file_path.lstrip('/')
        
        try:
            # Convert data to JSON bytes - compact format with proper Unicode support
            json_bytes = json.dumps(data, separators=(',', ':'), default=str, ensure_ascii=False).encode('utf-8')
            
            # Upload to Supabase Storage (upsert to overwrite existing file)
            response = self.client.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=json_bytes,
                file_options={"content-type": "application/json", "upsert": "true"}
            )
            
            logger.info(f"Successfully uploaded backup to {self.bucket_name}/{file_path}")
            
            return {
                'success': True,
                'filename': filename,
                'path': file_path,
                'bucket': self.bucket_name,
                'message': f"Backup uploaded successfully: {file_path}"
            }
            
        except Exception as e:
            error_msg = f"Failed to upload backup: {str(e)}"
            logger.error(error_msg)
            raise SupabaseBackupError(error_msg)
    
    def list_backups(self, folder: str = "", limit: int = 100) -> list:
        """
        List existing backups in the storage bucket.
        
        Args:
            folder: Folder path to list
            limit: Maximum number of files to return
            
        Returns:
            List of file objects
        """
        try:
            response = self.client.storage.from_(self.bucket_name).list(
                path=folder,
                options={"limit": limit, "sortBy": {"column": "created_at", "order": "desc"}}
            )
            return response
        except Exception as e:
            raise SupabaseBackupError(f"Failed to list backups: {str(e)}")
    
    def get_public_url(self, file_path: str) -> str:
        """
        Get the public URL for a backup file.
        
        Args:
            file_path: Path to the file in the bucket
            
        Returns:
            Public URL string
        """
        try:
            response = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
            return response
        except Exception as e:
            raise SupabaseBackupError(f"Failed to get public URL: {str(e)}")


def backup_transport_data(
    data: dict,
    supabase_url: Optional[str] = None,
    supabase_key: Optional[str] = None,
    bucket_name: Optional[str] = None,
    filename: str = "transport_data.json"
) -> dict:
    """
    Convenience function to backup transport data to Supabase.
    
    Args:
        data: The transport data dictionary to backup
        supabase_url: Supabase project URL (optional, uses env)
        supabase_key: Supabase service key (optional, uses env)
        bucket_name: Storage bucket name (optional, uses env)
        filename: Filename to use (default: transport_data.json)
        
    Returns:
        dict with backup result details
    """
    backup = SupabaseBackup(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        bucket_name=bucket_name
    )
    return backup.upload_json(data=data, filename=filename)
