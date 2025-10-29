# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LeafKnow is a knowledge management application that combines AI-powered chat with document processing and retrieval capabilities. The project consists of:

- **Backend API**: Python FastAPI server with SQLite database
- **Frontend**: Tauri desktop application with React UI
- **AI Framework**: Custom Agno-based AI agent system
- **Document Processing**: Multi-modal vectorization and RAG system

## Architecture

### Core Components

1. **API Server** ([`core/main.py`](core/main.py))
   - FastAPI application with SQLite WAL mode optimization
   - Multi-threaded task processing (normal and high priority)
   - RESTful APIs for models, chat sessions, and documents
   - CORS enabled for Tauri frontend

2. **Database Management** ([`core/db_mgr.py`](core/db_mgr.py))
   - SQLite with WAL mode for concurrent access
   - Comprehensive schema for tasks, documents, chat sessions, models
   - Built-in initialization and migration support
   - Optimized for file monitoring and document processing

3. **AI Model Management** ([`core/models_mgr.py`](core/models_mgr.py))
   - Multi-provider model support (OpenAI, Ollama, local models)
   - Built-in MLX-optimized models for vision and embedding
   - Streaming chat with Vercel AI SDK v5 compatibility
   - RAG integration with context-aware responses

4. **Memory Management** ([`core/memory_mgr.py`](core/memory_mgr.py))
   - Token counting and message trimming
   - Context window optimization
   - Tool token calculation

5. **Chat Applications**
   - Enhanced chat app ([`chat_app_enhanced.py`](chat_app_enhanced.py)) with multi-user support
   - Basic chat app ([`chat_app.py`](chat_app.py))
   - Session and agent management with SQLite persistence

### Key Features

- **Multi-modal AI**: Vision + text processing with local Qwen3-VL model
- **Document Vectorization**: Automatic embedding and chunking
- **RAG System**: Pin files to sessions for context-aware responses
- **Task Queue**: Asynchronous processing with priority handling
- **Model Discovery**: Automatic detection of Ollama and other local models

## Development Commands

### Backend Development

```bash
# Start the API server
python core/main.py --port 60000 --host 127.0.0.1 --db-path autobox_id.db

# Run enhanced chat application
python chat_app_enhanced.py

# Test database initialization
python core/db_mgr.py

# Test model management
python core/models_mgr.py
```

### Frontend Development

```bash
cd leaf-know

# Install dependencies
bun install

# Start development server
bun run dev

# Build for production
bun run build

# Run Tauri development
bun run tauri dev
```

### Testing

```bash
# Run unit tests
python -m pytest tests/unit/

# Run specific test
python tests/unit/test_session_features.py

# Run modular tests
python tests/agno_modular/tests.py

# Run MCP tests
python tests/mcp/test_mcp_py38.py
```

## Database Schema

The application uses SQLite with the following key tables:

- **`t_tasks`**: Asynchronous task processing
- **`t_documents`**: Document metadata and processing status
- **`t_parent_chunks`**: Document content chunks (text, images, tables)
- **`t_child_chunks`**: Vectorized content for retrieval
- **`t_chat_sessions`**: Chat session management
- **`t_chat_messages`**: Message history with structured content
- **`t_chat_session_pin_files`**: File pinning for RAG context
- **`t_model_configurations`**: AI model configurations
- **`t_capability_assignments`**: Model capability mapping

### Important Database Features

- **WAL Mode**: Enabled for concurrent read/write access
- **Connection Pooling**: Optimized for multi-threaded access
- **FTS5 Search**: Full-text search for file metadata
- **JSON Columns**: Flexible metadata storage
- **Foreign Keys**: Referential integrity with cascade deletes

## Model Configuration

### Built-in Models

The application includes MLX-optimized models for Apple Silicon:

- **Vision Model**: `mlx-community/Qwen3-VL-4B-Instruct-3bit`
- **Embedding Model**: `mlx-community/embeddinggemma-300m-4bit`

### Model Providers

Support for multiple model providers:

- **OpenAI**: GPT-4o, GPT-3.5-turbo
- **Anthropic**: Claude models
- **Ollama**: Local models via Ollama server
- **LM Studio**: Local models via LM Studio
- **OpenRouter**: Various model access

### Configuration

Models are configured via the database `t_model_configurations` table and assigned to capabilities in `t_capability_assignments`. The system supports:

- Text generation
- Vision processing
- Structured output
- Tool use
- Embedding generation

## File Processing Pipeline

1. **File Discovery**: Rust-based file monitoring with configurable rules
2. **Screening**: Apply filter rules (extension, filename, folder patterns)
3. **Document Processing**: Parse with Docling for multi-modal content
4. **Chunking**: Split content into parent/child chunks
5. **Vectorization**: Generate embeddings with local models
6. **Storage**: Store in SQLite + LanceDB for vector search

## API Endpoints

### Models API
- `GET /models` - List available models
- `POST /models/{model_id}/test` - Test model configuration
- `PUT /models/{model_id}/enable` - Enable/disable model

### Chat Sessions API
- `GET /chat-sessions` - List sessions
- `POST /chat-sessions` - Create session
- `PUT /chat-sessions/{session_id}` - Update session
- `DELETE /chat-sessions/{session_id}` - Delete session

### Chat API
- `POST /chat-sessions/{session_id}/chat` - Send message (streaming)
- `GET /chat-sessions/{session_id}/messages` - Get message history

### Documents API
- `POST /pin-file` - Pin file for RAG context
- `GET /documents` - List processed documents
- `GET /documents/{document_id}/chunks` - Get document chunks

## Task Processing

The system uses a priority-based task queue:

- **HIGH**: User-initiated operations (file pinning)
- **MEDIUM**: Background processing (document vectorization)
- **LOW**: Maintenance tasks

Tasks are processed by dedicated worker threads with SQLite connection pooling.

## Development Notes

### Database Optimization
- Uses WAL mode for concurrent access
- Connection pooling with 5 base connections
- 30-minute connection recycling
- Optimized pragmas for performance

### AI Integration
- Agno framework for agent-based AI
- Vercel AI SDK v5 compatible streaming
- Multi-modal support (text + images)
- Tool integration for external capabilities

### Error Handling
- Comprehensive logging with structured output
- Graceful degradation for missing models
- Database transaction rollback on errors
- User-friendly error messages

### Performance Considerations
- Streaming responses for real-time chat
- Background task processing
- Token counting for context management
- Vector search optimization with LanceDB

## Configuration Files

- **Model Configs**: [`model_configs.json`](model_configs.json) - Legacy model configurations
- **Tauri Config**: [`leaf-know/src-tauri/tauri.conf.json`](leaf-know/src-tauri/tauri.conf.json) - Desktop app configuration
- **Package Config**: [`leaf-know/package.json`](leaf-know/package.json) - Frontend dependencies
- **Python Project**: [`core/pyproject.toml`](core/pyproject.toml) - Backend dependencies

## Security Notes

- API keys stored in database (encrypted in production)
- Local file system access restrictions
- SQL injection protection via SQLModel
- CORS configuration for frontend access
- No remote code execution in AI responses

## Troubleshooting

### Database Issues
- Check WAL file permissions if database is locked
- Use `python core/db_mgr.py` to reinitialize schema
- Monitor connection pool usage in logs

### Model Issues
- Verify MLX installation for Apple Silicon models
- Check Ollama server status for local models
- Test API keys for cloud providers
- Monitor model download progress in logs

### Performance Issues
- Monitor task queue backlog via `/task/{task_id}`
- Check vector database size and indexing
- Review memory usage for large document sets
- Adjust connection pool size if needed

## 文件存放规则

- 文档存到docs文件夹中

- 测试文件存放到tests文件夹中
- sqlite本地数据库文件使用autobox_id.db