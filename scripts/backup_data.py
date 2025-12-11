#!/usr/bin/env python3
"""
Standalone Backup Script for GitHub Actions

This script fetches transportation data from the API and uploads it to Supabase Storage.
Designed to run independently via GitHub Actions on a weekly schedule.

Environment variables required:
    - SUPABASE_URL: Your Supabase project URL
    - SUPABASE_SERVICE_KEY: Supabase service role key
    - SUPABASE_BUCKET_NAME: Storage bucket name (default: 'transport-backups')
    - API_ENDPOINT: API endpoint URL (default: 'https://api-lakbayan.onrender.com/api/complete/')
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Optional

import requests
from supabase import create_client, Client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BackupError(Exception):
    """Custom exception for backup errors"""
    pass


def fetch_transport_data(api_url: str, timeout: int = 60) -> dict:
    """
    Fetch transportation data from the API endpoint.
    
    Args:
        api_url: The API endpoint URL
        timeout: Request timeout in seconds
        
    Returns:
        dict: The JSON response data
        
    Raises:
        BackupError: If the request fails
    """
    logger.info(f"Fetching data from {api_url}")
    
    try:
        response = requests.get(api_url, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        
        # Log some stats
        regions_count = len(data.get('regions', []))
        terminals_count = data.get('total_terminals', 'N/A')
        routes_count = data.get('total_routes', 'N/A')
        
        logger.info(f"Fetched data: {regions_count} regions, {terminals_count} terminals, {routes_count} routes")
        
        return data
        
    except requests.exceptions.Timeout:
        raise BackupError(f"Request timed out after {timeout} seconds")
    except requests.exceptions.RequestException as e:
        raise BackupError(f"Failed to fetch data: {str(e)}")
    except json.JSONDecodeError as e:
        raise BackupError(f"Invalid JSON response: {str(e)}")


def upload_to_supabase(
    data: dict,
    supabase_url: str,
    supabase_key: str,
    bucket_name: str,
    filename: str = "transport_data.json"
) -> dict:
    """
    Upload JSON data to Supabase Storage.
    
    Args:
        data: Dictionary to upload
        supabase_url: Supabase project URL
        supabase_key: Supabase service role key
        bucket_name: Storage bucket name
        filename: Filename to use (default: transport_data.json)
        
    Returns:
        dict with upload result
        
    Raises:
        BackupError: If upload fails
    """
    
    logger.info(f"Uploading to Supabase bucket '{bucket_name}' as '{filename}'")
    
    try:
        # Initialize Supabase client
        client: Client = create_client(supabase_url, supabase_key)
        
        # Convert to JSON bytes - compact format with proper Unicode support
        json_bytes = json.dumps(data, separators=(',', ':'), default=str, ensure_ascii=False).encode('utf-8')
        
        # Upload to storage (upsert to overwrite existing file)
        response = client.storage.from_(bucket_name).upload(
            path=filename,
            file=json_bytes,
            file_options={"content-type": "application/json", "upsert": "true"}
        )
        
        logger.info(f"Successfully uploaded: {filename}")
        
        # Get public URL
        public_url = client.storage.from_(bucket_name).get_public_url(filename)
        
        return {
            'success': True,
            'filename': filename,
            'bucket': bucket_name,
            'public_url': public_url,
            'size_bytes': len(json_bytes)
        }
        
    except Exception as e:
        raise BackupError(f"Failed to upload to Supabase: {str(e)}")


def main() -> int:
    """
    Main entry point for the backup script.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    logger.info("=" * 50)
    logger.info("Starting LakBayan Transport Data Backup")
    logger.info("=" * 50)
    
    # Get configuration from environment
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')
    bucket_name = os.environ.get('SUPABASE_BUCKET_NAME', 'transport-backups')
    api_endpoint = os.environ.get(
        'API_ENDPOINT',
        'https://api-lakbayan.onrender.com/api/complete/'
    )
    
    # Validate required environment variables
    missing_vars = []
    if not supabase_url:
        missing_vars.append('SUPABASE_URL')
    if not supabase_key:
        missing_vars.append('SUPABASE_SERVICE_KEY')
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return 1
    
    try:
        # Step 1: Fetch data from API
        data = fetch_transport_data(api_endpoint)
        
        # Step 2: Upload to Supabase
        result = upload_to_supabase(
            data=data,
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            bucket_name=bucket_name
        )
        
        # Success!
        logger.info("=" * 50)
        logger.info("Backup completed successfully!")
        logger.info(f"  Filename: {result['filename']}")
        logger.info(f"  Bucket: {result['bucket']}")
        logger.info(f"  Size: {result['size_bytes']:,} bytes")
        logger.info(f"  URL: {result['public_url']}")
        logger.info("=" * 50)
        
        return 0
        
    except BackupError as e:
        logger.error(f"Backup failed: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
