# 🤖 RAG Chatbot with Google Drive Integration

A powerful RAG (Retrieval-Augmented Generation) chatbot that processes, stores, and interacts with documents from Google Drive using Qdrant vector storage and Google's Gemini AI.

## Features

### Document Processing & Storage
- ✅ Retrieves documents from Google Drive folders
- ✅ Processes and splits documents into manageable chunks
- ✅ Extracts metadata using AI for enhanced search capabilities
- ✅ Stores document vectors in Qdrant for efficient retrieval
- ✅ Supports batch processing with configurable chunk sizes

### Intelligent Chat Interface
- ✅ Conversational interface powered by Google Gemini
- ✅ RAG-based retrieval for context-aware responses
- ✅ Maintains chat history in Google Docs
- ✅ Memory management with configurable window buffer
- ✅ Specialized agent for Nostr/Damus user profiles

### Vector Store Management
- ✅ Secure delete operations with human verification via Telegram
- ✅ Telegram notifications for important operations
- ✅ Metadata-based hybrid search capabilities
- ✅ Batch processing and progress tracking

## Quick Start

### Prerequisites

- Python 3.9+
- Qdrant vector database (local or cloud)
- Google Cloud Platform account with APIs enabled
- OpenAI API account
- Telegram bot (optional, for notifications)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd rag-chatbot
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up Google Cloud credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the following APIs:
     - Google Drive API
     - Google Docs API
   - Create OAuth 2.0 credentials
   - Download credentials as `credentials.json` and place in project root

5. **Set up Qdrant**
   
   **Option A: Local Docker**
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```
   
   **Option B: Qdrant Cloud**
   - Sign up at [cloud.qdrant.io](https://cloud.qdrant.io/)
   - Create a cluster and get your API key

6. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

7. **Set up Telegram bot (optional)**
   - Chat with [@BotFather](https://t.me/botfather) on Telegram
   - Create a new bot and get the token
   - Get your chat ID by messaging [@userinfobot](https://t.me/userinfobot)
   - Add to `.env` file

## 📖 Usage

### Process Documents from Google Drive

```python
import asyncio
from main import RAGChatbot

async def main():
    chatbot = RAGChatbot()
    
    # Process all documents in the configured folder
    await chatbot.process_documents(batch_size=5)

asyncio.run(main())
```

### Run Interactive Chat

```bash
python main.py
```

The chat interface will start and you can:
- Ask questions about the documents
- Type `clear` to reset conversation memory
- Type `quit` or `exit` to end the session

### Delete Documents from Vector Store

```python
import asyncio
from main import RAGChatbot

async def main():
    chatbot = RAGChatbot()
    
    # Delete specific documents by file IDs
    file_ids = ["file_id_1", "file_id_2"]
    await chatbot.delete_documents_by_file_ids(file_ids)

asyncio.run(main())
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings | Yes |
| `GOOGLE_API_KEY` | Google API key for Gemini | Yes |
| `QDRANT_URL` | Qdrant instance URL | Yes |
| `QDRANT_API_KEY` | Qdrant API key (if cloud) | No |
| `QDRANT_COLLECTION_NAME` | Vector store collection name | Yes |
| `GOOGLE_DRIVE_FOLDER_ID` | Google Drive folder ID | Yes |
| `GOOGLE_DOCS_HISTORY_ID` | Google Docs ID for chat history | Yes |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | No |
| `TELEGRAM_CHAT_ID` | Telegram chat ID | No |

### Document Processing Configuration

In `main.py`, adjust these parameters:

```python
# Chunk size for text splitting
chunk_size = 3000
chunk_overlap = 200

# Batch processing size
batch_size = 5

# Memory window size (number of messages)
memory_window = 40

# Number of documents to retrieve
retrieval_k = 20
```

## 📁 Project Structure

```
rag-chatbot/
├── main.py                    # Main application
├── google_drive_handler.py    # Google Drive operations
├── document_processor.py      # Document processing and metadata extraction
├── telegram_notifier.py       # Telegram notifications
├── chat_history_manager.py    # Google Docs chat history
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── credentials.json          # Google OAuth credentials (not in repo)
├── token.json               # Generated OAuth token (not in repo)
└── README.md                # This file
```

## 🔒 Security Notes

- Never commit `credentials.json`, `token.json`, or `.env` files
- Store API keys securely using environment variables
- Use service accounts for production deployments
- Implement proper access controls for Google Drive folders
- Enable Telegram bot security features if using notifications

## 🛠️ Metadata Extraction

The system automatically extracts structured metadata from documents:

- **Overarching Theme**: Main topics discussed
- **Recurring Topics**: Common threads across content
- **Pain Points**: User frustrations or challenges
- **Analytical Insights**: Key observations and patterns
- **Conclusion**: Summary of findings
- **Keywords**: 10 key terms for hybrid search

This metadata enables powerful hybrid search combining semantic similarity and keyword filtering.

##  Advanced Features

### Hybrid Search

The Qdrant vector store supports hybrid search combining:
- Semantic similarity (vector search)
- Keyword filtering (metadata search)

### Conversation Memory

Uses a window buffer memory to maintain context:
- Stores last 40 messages by default
- Can be cleared with `clear` command
- Persists across chat session

### Error Handling

- Automatic retry logic for API calls
- Graceful degradation when services unavailable
- Detailed error logging for debugging

##  Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

##  Acknowledgments

- Built with [LangChain](https://langchain.com/)
- Vector storage by [Qdrant](https://qdrant.tech/)
- AI powered by [Google Gemini](https://deepmind.google/technologies/gemini/) and [OpenAI](https://openai.com/)
- Based on my first RAG Agent made in n8n.

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review error logs

## 🔄 Workflow Comparison

This Python implementation replicates the n8n workflow with the following mappings:

| n8n Node | Python Component |
|----------|------------------|
| Google Drive nodes | `GoogleDriveHandler` |
| Document processing | `DocumentProcessor` |
| Qdrant Vector Store | `QdrantClient` + LangChain |
| Gemini Chat Model | `ChatGoogleGenerativeAI` |
| OpenAI Embeddings | `OpenAIEmbeddings` |
| Telegram nodes | `TelegramNotifier` |
| Google Docs | `ChatHistoryManager` |
| AI Agent | LangChain Agent + Memory |
| Loop Over Items | Python async batch processing |
| Human Verification | Telegram confirmation flow |
