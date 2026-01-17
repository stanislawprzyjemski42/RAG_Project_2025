"""
Google Drive Handler
Handles file operations with Google Drive
"""

import os
import io
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

# Scopes required for Google Drive and Docs access
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/documents'
]


class GoogleDriveHandler:
    """Handler for Google Drive operations"""
    
    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = None
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive API"""
        # Load existing credentials
        if os.path.exists(self.token_file):
            self.creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        
        # Refresh or create new credentials
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_file}\n"
                        "Please download OAuth credentials from Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(self.creds.to_json())
        
        # Build service
        self.service = build('drive', 'v3', credentials=self.creds)
    
    def list_files_in_folder(self, folder_id: str) -> List[Dict]:
        """
        List all files in a Google Drive folder
        
        Args:
            folder_id: Google Drive folder ID
            
        Returns:
            List of file metadata dictionaries
        """
        try:
            files = []
            page_token = None
            
            while True:
                response = self.service.files().list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType, size, modifiedTime)',
                    pageToken=page_token
                ).execute()
                
                files.extend(response.get('files', []))
                page_token = response.get('nextPageToken', None)
                
                if page_token is None:
                    break
            
            return files
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def download_file(self, file_id: str) -> Optional[str]:
        """
        Download a file from Google Drive and return its content as text
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            File content as string, or None if error
        """
        try:
            # Get file metadata
            file_metadata = self.service.files().get(fileId=file_id, fields='mimeType,name').execute()
            mime_type = file_metadata.get('mimeType', '')
            file_name = file_metadata.get('name', '')
            
            # Handle Google Docs files
            if mime_type == 'application/vnd.google-apps.document':
                # Export as plain text
                request = self.service.files().export_media(
                    fileId=file_id,
                    mimeType='text/plain'
                )
            else:
                # Download regular files
                request = self.service.files().get_media(fileId=file_id)
            
            # Download content
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            # Decode content
            file_content.seek(0)
            content = file_content.read().decode('utf-8', errors='ignore')
            
            return content
            
        except HttpError as error:
            print(f'Error downloading file {file_id}: {error}')
            return None
        except Exception as e:
            print(f'Unexpected error downloading file {file_id}: {e}')
            return None
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict]:
        """
        Get metadata for a file
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            File metadata dictionary
        """
        try:
            return self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, modifiedTime, createdTime'
            ).execute()
        except HttpError as error:
            print(f'Error getting file metadata: {error}')
            return None
