# RAG Chatbot with Google Drive Integration

## What This System Does

- This system enables natural language querying over large document collections stored in Google Drive. Documents are automatically ingested, chunked, embedded, and indexed in a **Qdrant vector database** to enable efficient semantic retrieval.

- At query time, the system retrieves the most relevant document segments using vector similarity and provides them as grounded context for response generation. When applied to large collections of legal documents, it significantly reduced search time compared to manual multi-document review.

**Key capabilities:**
- Semantic retrieval over heterogeneous document formats  
- Context-aware, multi-turn conversations with bounded memory  
- Source-grounded answers with metadata attribution  
- Incremental document updates without full reindexing

---

## 📖 Table of Contents

- [What This Does](#what-this-does)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

---

## What This Does

This chatbot allows you to have natural conversations about your documents stored in Google Drive. Instead of manually searching through files, simply ask questions and get accurate answers based on the content of your documents. The system automatically processes your files, understands their content, and retrieves relevant information when you ask questions.

**Example Use Cases:**
- Ask questions about company documentation
- Search through research papers conversationally
- Query customer support documents
- Analyze Nostr/Damus user profiles (default config)
- Create a personal knowledge base

---

## Key Features

###  Document Processing
- Automatically retrieves documents from Google Drive folders
- Supports PDF, DOCX, plain text, and Google Docs
- Processes documents in configurable batches
- Extracts structured metadata using AI
- Splits long documents into manageable chunks

###  Intelligent Conversation
- Powered by Google Gemini 2.0 Flash
- Maintains conversation context (40-message buffer)
- Retrieves most relevant document sections
- Provides source attribution
- Handles follow-up questions naturally

###  Vector Storage
- Fast similarity search with Qdrant
- Hybrid search (semantic + keyword filtering)
- Rich metadata for advanced filtering
- Handles thousands of documents efficiently
- Full CRUD operations support

###  Smart Features
- Telegram notifications (optional)
- Human-in-the-loop confirmations
- Automatic chat history to Google Docs
- Error handling with retries
- Progress tracking

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.9+ | Core application |
| **Framework** | LangChain | AI orchestration |
| **LLM** | Google Gemini 2.0 | Natural language understanding |
| **Embeddings** | OpenAI text-embedding-3-large | Document vectorization (3072 dims) |
| **Vector DB** | Qdrant | Similarity search |
| **Storage** | Google Drive | Document repository |
| **History** | Google Docs | Conversation logs |
| **Notifications** | Telegram Bot API | Alerts (optional) |

---

## Requirements

Before you begin, you'll need:

- ✅ Python 3.9 or newer
- ✅ Google Cloud Platform account (free tier works)
- ✅ OpenAI API account with billing enabled
- ✅ Qdrant instance (local Docker or cloud)
- ⚪ Telegram bot (advised)

---

## Installation

### Step 1: Get the Code

```bash
git clone https://github.com/yourusername/rag-chatbot.git
cd rag-chatbot
```

### Step 2: Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (choose your platform)
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Google Cloud Setup

**Enable APIs:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project
3. Enable **Google Drive API** and **Google Docs API**

**Create OAuth Credentials:**
1. Navigate to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Choose "Desktop app"
4. Download JSON file
5. Rename to `credentials.json`
6. Place in project root

> ⚠️ Never commit `credentials.json` to version control

### Step 5: Qdrant Setup

**Option A - Docker (Recommended):**
```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant
```

**Option B - Qdrant Cloud:**
1. Sign up at [cloud.qdrant.io](https://cloud.qdrant.io/)
2. Create a cluster
3. Note your URL and API key

### Step 6: Get API Keys

**OpenAI API Key:**
- Visit [platform.openai.com](https://platform.openai.com/)
- Create API key in your account settings

**Google Gemini API Key:**
- Visit [ai.google.dev](https://ai.google.dev/)
- Click "Get API key"

**Telegram Bot (Optional):**
- Message @BotFather on Telegram
- Send `/newbot` and follow prompts
- Get your chat ID from @userinfobot

### Step 7: Environment Configuration

Create `.env` file in project root:

```bash
# OpenAI
OPENAI_API_KEY=sk-your-key-here

# Google Gemini
GOOGLE_API_KEY=your-key-here

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION_NAME=my-documents

# Google Drive (get ID from folder URL)
GOOGLE_DRIVE_FOLDER_ID=your-folder-id

# Google Docs (get ID from document URL)
GOOGLE_DOCS_HISTORY_ID=your-doc-id

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your-token
TELEGRAM_CHAT_ID=your-chat-id
```

**Finding IDs:**
- **Folder ID:** From `https://drive.google.com/drive/folders/FOLDER_ID` 
- **Doc ID:** From `https://docs.google.com/document/d/DOC_ID/edit`

### Step 8: First Run

```bash
python main.py
```

A browser will open for Google authorization (one-time only).

---

## Configuration

### Adjusting Parameters

Edit `main.py` to customize:

```python
# Text processing
chunk_size = 3000          # Characters per chunk
chunk_overlap = 200        # Overlap between chunks

# Retrieval
retrieval_k = 20           # Documents to retrieve per query

# Memory
memory_window = 40         # Conversation turns to remember

# Batch processing
batch_size = 5             # Files to process at once
```

### Changing Models

```python
# Language model
self.llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",  # or "gemini-1.5-pro"
    max_output_tokens=8192,
    temperature=0.4
)

# Embeddings
self.embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large"  # or "text-embedding-3-small"
)
```

### Custom Metadata

Edit `document_processor.py` to extract custom fields:

```python
ResponseSchema(
    name="your_field",
    description="What to extract",
    type="string"  # or "list"
)
```

---

## Usage

### Processing Documents

To load documents from Google Drive, uncomment in `main.py`:

```python
await chatbot.process_documents()
```

Then run:
```bash
python main.py
```

The system will download, process, and store all documents from your configured folder.

### Interactive Chat

Run the chatbot:

```bash
python main.py
```

You'll see:

```
============================================================
RAG Chatbot - Document Assistant
============================================================
Type 'quit' or 'exit' to end conversation
Type 'clear' to reset memory
============================================================

You: 
```

**Commands:**
- Type any question about your documents
- `clear` - Reset conversation memory
- `quit` or `exit` - Close chatbot

**Example:**
```
You: What are the main topics in the documents?
Assistant: Based on the documents, the main topics are...

You: Tell me more about the first topic
Assistant: [Provides detailed context-aware response]
```

### Deleting Documents

To remove documents from the vector store:

```python
file_ids = ["file_id_1", "file_id_2"]
await chatbot.delete_documents_by_file_ids(file_ids)
```

If Telegram is configured, you'll receive a confirmation request.

---

## Project Structure

```
rag-chatbot/
├── main.py                      # Main application
├── google_drive_handler.py      # Drive operations
├── document_processor.py        # Processing & metadata
├── telegram_notifier.py         # Notifications
├── chat_history_manager.py      # History management
├── requirements.txt             # Dependencies
├── .env.example                 # Config template
├── .gitignore                   # Git exclusions
└── README.md                    # This file
```

**Not in repo (gitignored):**
- `credentials.json` - Google OAuth credentials
- `token.json` - Google OAuth token
- `.env` - Your configuration

---

## Troubleshooting

### Authentication

**Browser doesn't open:**
- Manually visit the URL shown in terminal
- Complete authorization and paste code back

**Invalid credentials:**
- Delete `token.json` and retry
- Verify `credentials.json` is correct
- Check APIs are enabled in Google Cloud

### API Issues

**OpenAI key not working:**
- Verify key in `.env`
- Check billing is set up
- Ensure sufficient credits

**Rate limits:**
- Reduce `batch_size`
- Add delays between calls
- Upgrade API plan

### Qdrant

**Cannot connect:**
- Check Docker is running: `docker ps`
- Verify URL in `.env`
- For cloud, check API key

**Collection errors:**
- Collection is auto-created
- Delete and recreate if needed

### Processing

**Documents not processing:**
- Verify Google Drive folder ID
- Check folder access permissions
- Ensure supported formats (PDF, DOCX, TXT, Google Docs)

**Metadata extraction fails:**
- Check Gemini API key and quota
- Reduce `chunk_size` for long documents
- Review console error messages

**Memory issues:**
- Reduce `batch_size`
- Reduce `chunk_size`
- Process in multiple sessions

---

## Security

### Critical Files (Never Commit)

- `credentials.json` - Google OAuth credentials
- `token.json` - Google OAuth token
- `.env` - API keys and configuration
- Any files with secrets

All these are in `.gitignore` by default.

### API Key Safety

- Store only in `.env` file
- Don't share in messages/screenshots
- Rotate keys regularly
- Use environment variables in production

### Google Permissions

- App requests read-only Drive access
- Review/revoke at [myaccount.google.com/permissions](https://myaccount.google.com/permissions)

### Data Flow

| Service | Data Sent | Purpose |
|---------|-----------|---------|
| OpenAI | Document text | Create embeddings |
| Google Gemini | Documents & questions | Metadata extraction & chat |
| Google Drive/Docs | Read/write operations | Documents & history |
| Telegram | Notifications | Alerts (optional) |
| Qdrant | Embeddings & metadata | Vector storage |

---

## Contributing

Contributions welcome! Here's how:

### Reporting Bugs

Open an issue with:
- Clear description
- Steps to reproduce
- Python version & OS
- Error messages/logs

### Suggesting Features

Open an issue describing:
- Problem it solves
- How it would work
- Why it's useful

### Code Contributions

1. Fork repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

---

## License

MIT License - see LICENSE file for details.

---

## Acknowledgments

Built with:
- [LangChain](https://langchain.com/) - LLM framework
- [Qdrant](https://qdrant.tech/) - Vector search
- [Google Gemini](https://ai.google.dev/) - AI model
- [OpenAI](https://openai.com/) - Embeddings

Inspired by my first RAG Agent in a low code tool called n8n.

---

## Support

Need help?
- Check Troubleshooting section
- Search GitHub Issues
- Open new Issue with details

---
