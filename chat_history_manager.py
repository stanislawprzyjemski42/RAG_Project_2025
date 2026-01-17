"""
Chat History Manager
Manages chat history storage in Google Docs
"""

import os
from typing import Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


class ChatHistoryManager:
    """Manages chat history in Google Docs"""
    
    def __init__(self, document_id: str, credentials_file: str = 'credentials.json', token_file: str = 'token.json'):
        self.document_id = document_id
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = None
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Docs API"""
        scopes = ['https://www.googleapis.com/auth/documents']
        
        # Load existing credentials
        if os.path.exists(self.token_file):
            self.creds = Credentials.from_authorized_user_file(self.token_file, scopes)
        
        # Refresh or create new credentials
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    print(f"Warning: Credentials file not found: {self.credentials_file}")
                    print("Chat history will not be saved to Google Docs")
                    return
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, scopes
                )
                self.creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open(self.token_file, 'w') as token:
                token.write(self.creds.to_json())
        
        # Build service
        self.service = build('docs', 'v1', credentials=self.creds)
    
    async def append_to_history(self, content: str) -> bool:
        """
        Append content to the chat history document
        
        Args:
            content: Content to append
            
        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            print("Google Docs service not initialized - skipping history save")
            return False
        
        try:
            # Get document to find the end position
            document = self.service.documents().get(documentId=self.document_id).execute()
            
            # The end of the document is typically at index 1 for a new doc
            # For existing docs, we get the content length
            end_index = document.get('body', {}).get('content', [{}])[-1].get('endIndex', 1)
            
            # Insert text at the end
            requests = [
                {
                    'insertText': {
                        'location': {
                            'index': end_index - 1  # Insert before the last character
                        },
                        'text': content
                    }
                }
            ]
            
            # Execute the batch update
            self.service.documents().batchUpdate(
                documentId=self.document_id,
                body={'requests': requests}
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error appending to chat history: {e}")
            return False
    
    async def clear_history(self) -> bool:
        """
        Clear all content from the chat history document
        
        Returns:
            True if successful, False otherwise
        """
        if not self.service:
            return False
        
        try:
            # Get document
            document = self.service.documents().get(documentId=self.document_id).execute()
            
            # Get the content length
            content = document.get('body', {}).get('content', [])
            if not content:
                return True
            
            # Delete all content except the last newline
            end_index = content[-1].get('endIndex', 1)
            
            requests = [
                {
                    'deleteContentRange': {
                        'range': {
                            'startIndex': 1,
                            'endIndex': end_index - 1
                        }
                    }
                }
            ]
            
            # Execute the batch update
            self.service.documents().batchUpdate(
                documentId=self.document_id,
                body={'requests': requests}
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error clearing chat history: {e}")
            return False
    
    async def get_history(self) -> Optional[str]:
        """
        Get the full chat history content
        
        Returns:
            Chat history as string, or None if error
        """
        if not self.service:
            return None
        
        try:
            # Get document
            document = self.service.documents().get(documentId=self.document_id).execute()
            
            # Extract text from document
            content = document.get('body', {}).get('content', [])
            text = ""
            
            for element in content:
                if 'paragraph' in element:
                    paragraph = element['paragraph']
                    for text_run in paragraph.get('elements', []):
                        if 'textRun' in text_run:
                            text += text_run['textRun'].get('content', '')
            
            return text
            
        except Exception as e:
            print(f"Error getting chat history: {e}")
            return None
    
    async def create_new_document(self, title: str) -> Optional[str]:
        """
        Create a new Google Doc for chat history
        
        Args:
            title: Title for the new document
            
        Returns:
            Document ID if successful, None otherwise
        """
        if not self.service:
            return None
        
        try:
            document = self.service.documents().create(
                body={'title': title}
            ).execute()
            
            new_doc_id = document.get('documentId')
            print(f"Created new document: {title} (ID: {new_doc_id})")
            
            return new_doc_id
            
        except Exception as e:
            print(f"Error creating new document: {e}")
            return None
