"""
RAG Chatbot with Google Drive Integration
Main application file
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import asyncio
from datetime import datetime

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Qdrant
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.memory import ConversationBufferWindowMemory
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from google_drive_handler import GoogleDriveHandler
from document_processor import DocumentProcessor
from telegram_notifier import TelegramNotifier
from chat_history_manager import ChatHistoryManager

# Load environment variables
load_dotenv()


class RAGChatbot:
    """Main RAG Chatbot class integrating all components"""
    
    def __init__(self):
        # API Keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        # Qdrant Configuration
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY", "")
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "nostr-damus-user-profiles")
        
        # Google Drive Configuration
        self.drive_folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        self.chat_history_doc_id = os.getenv("GOOGLE_DOCS_HISTORY_ID")
        
        # Initialize components
        self.qdrant_client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)
        self.drive_handler = GoogleDriveHandler()
        self.doc_processor = DocumentProcessor()
        self.telegram = TelegramNotifier(self.telegram_token, self.telegram_chat_id)
        self.chat_history = ChatHistoryManager(self.chat_history_doc_id)
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",
            openai_api_key=self.openai_api_key
        )
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=self.google_api_key,
            max_output_tokens=8192
        )
        
        # Initialize vector store
        self.vector_store = None
        self._init_vector_store()
        
        # Initialize memory
        self.memory = ConversationBufferWindowMemory(
            k=40,
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize agent
        self.agent_executor = None
        self._init_agent()
    
    def _init_vector_store(self):
        """Initialize or connect to Qdrant vector store"""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections().collections
            collection_exists = any(c.name == self.collection_name for c in collections)
            
            if not collection_exists:
                # Create collection
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
                )
                print(f"Created collection: {self.collection_name}")
            
            # Connect to vector store
            self.vector_store = Qdrant(
                client=self.qdrant_client,
                collection_name=self.collection_name,
                embeddings=self.embeddings
            )
            print(f"Connected to vector store: {self.collection_name}")
            
        except Exception as e:
            print(f"Error initializing vector store: {e}")
            raise
    
    def _init_agent(self):
        """Initialize the AI agent with tools"""
        # Create retrieval tool
        retriever = self.vector_store.as_retriever(
            search_kwargs={"k": 20}
        )
        
        retrieval_tool = Tool(
            name="nostr_damus_user_profiles",
            description="Retrieve information about Nostr or Damus users",
            func=lambda query: self._retrieve_documents(query)
        )
        
        # Define system prompt
        system_prompt = """You are an intelligent assistant specialized in answering user questions using Nostr user profiles. Your primary goal is to provide precise, contextually relevant, and concise answers based on the tools and resources available.

### TOOL
Use the "nostr_damus_user_profiles" tool to:
- perform semantic similarity searches and retrieve information from Nostr user profiles relevant to the user's query.
- access detailed information about Nostr and/or Damus users when additional context or specifics are required.

### Key Instructions
1. **Response Guidelines**:
   - Clearly explain how the retrieved information addresses the user's query, if applicable.
   - If no relevant information is found, respond with: "I cannot find the answer in the available resources."

2. **Focus and Relevance**:
   - Ensure all responses are directly aligned with the user's question.
   - Avoid including extraneous details or relying solely on internal knowledge.
"""
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        agent = create_structured_chat_agent(
            llm=self.llm,
            tools=[retrieval_tool],
            prompt=prompt
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=[retrieval_tool],
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True
        )
    
    def _retrieve_documents(self, query: str) -> str:
        """Retrieve relevant documents from vector store"""
        try:
            docs = self.vector_store.similarity_search(query, k=20)
            
            if not docs:
                return "No relevant information found."
            
            # Format results
            results = []
            for i, doc in enumerate(docs, 1):
                content = doc.page_content
                metadata = doc.metadata
                results.append(f"Document {i}:\n{content}\n")
            
            return "\n".join(results)
        except Exception as e:
            return f"Error retrieving documents: {str(e)}"
    
    async def process_documents(self, batch_size: int = 5):
        """Process documents from Google Drive and store in Qdrant"""
        try:
            print(f"Fetching files from Google Drive folder: {self.drive_folder_id}")
            
            # Get files from Google Drive
            files = self.drive_handler.list_files_in_folder(self.drive_folder_id)
            
            if not files:
                print("No files found in the folder")
                return
            
            print(f"Found {len(files)} files to process")
            
            # Process files in batches
            for i in range(0, len(files), batch_size):
                batch = files[i:i + batch_size]
                
                for file in batch:
                    try:
                        file_id = file['id']
                        file_name = file['name']
                        
                        print(f"Processing: {file_name}")
                        
                        # Download file
                        content = self.drive_handler.download_file(file_id)
                        
                        if not content:
                            print(f"Skipping {file_name} - no content")
                            continue
                        
                        # Extract metadata using Gemini
                        metadata = await self.doc_processor.extract_metadata(content)
                        
                        # Add file metadata
                        metadata['file_id'] = file_id
                        metadata['pubkey'] = file_name
                        
                        # Split document into chunks
                        chunks = self.doc_processor.split_text(content)
                        
                        # Add to vector store
                        texts = [chunk for chunk in chunks]
                        metadatas = [metadata.copy() for _ in chunks]
                        
                        self.vector_store.add_texts(
                            texts=texts,
                            metadatas=metadatas
                        )
                        
                        print(f"✓ Stored {len(chunks)} chunks for {file_name}")
                        
                        # Small delay to avoid rate limits
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        print(f"Error processing {file.get('name', 'unknown')}: {e}")
                        continue
            
            # Send completion notification
            await self.telegram.send_message("Qdrant vector store upsert completed")
            print("Document processing completed!")
            
        except Exception as e:
            print(f"Error in process_documents: {e}")
            raise
    
    async def delete_documents_by_file_ids(self, file_ids: List[str]) -> bool:
        """Delete documents from Qdrant by file IDs with confirmation"""
        try:
            # Request confirmation via Telegram
            confirmed = await self.telegram.request_confirmation(
                f"WARNING - {len(file_ids)} Records in the Qdrant vector store collection "
                f'"{self.collection_name}" will be deleted. Are you sure you want to continue? '
                f"This action cannot be undone!",
                timeout_minutes=15
            )
            
            if not confirmed:
                await self.telegram.send_message("Qdrant vector store deletion declined")
                return False
            
            # Delete points for each file ID
            for file_id in file_ids:
                self.qdrant_client.delete(
                    collection_name=self.collection_name,
                    points_selector=Filter(
                        must=[
                            FieldCondition(
                                key="metadata.file_id",
                                match=MatchValue(value=file_id)
                            )
                        ]
                    )
                )
                print(f"Deleted documents for file_id: {file_id}")
            
            print(f"Successfully deleted {len(file_ids)} document sets")
            return True
            
        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False
    
    async def chat(self, message: str) -> str:
        """Process a chat message and return response"""
        try:
            # Get response from agent
            response = await asyncio.to_thread(
                self.agent_executor.invoke,
                {"input": message}
            )
            
            output = response.get("output", "I couldn't generate a response.")
            
            # Save to chat history
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            history_entry = f"\n-------------------------------\n\n{timestamp}\n\n{message}\n\n{output}"
            
            await self.chat_history.append_to_history(history_entry)
            
            return output
            
        except Exception as e:
            error_msg = f"Error processing chat: {str(e)}"
            print(error_msg)
            return error_msg
    
    async def run_chat_interface(self):
        """Run an interactive chat interface"""
        print("\n" + "="*60)
        print("RAG Chatbot - Nostr User Profiles")
        print("="*60)
        print("Type 'quit' or 'exit' to end the conversation")
        print("Type 'clear' to clear conversation memory")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit']:
                    print("Goodbye!")
                    break
                
                if user_input.lower() == 'clear':
                    self.memory.clear()
                    print("Conversation memory cleared.")
                    continue
                
                print("\nAssistant: ", end="", flush=True)
                response = await self.chat(user_input)
                print(response + "\n")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}\n")


async def main():
    """Main entry point"""
    chatbot = RAGChatbot()
    
    # Uncomment to process documents from Google Drive
    # await chatbot.process_documents()
    
    # Run chat interface
    await chatbot.run_chat_interface()


if __name__ == "__main__":
    asyncio.run(main())
