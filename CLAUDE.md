# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LeafKnow is a knowledge management and learning platform that combines AI-powered chat capabilities with document management and vector search. The application features a desktop frontend built with Tauri + React and a Python FastAPI backend that handles AI model integration, document processing, and knowledge retrieval.

## Architecture

LeafKnow uses a hybrid architecture with separate backend and frontend processes:

### Backend (Python FastAPI)
- **Location**: `core/` directory
- **Port**: 60000 (default)
- **Main Technologies**: FastAPI, SQLModel, LanceDB, Pydantic-AI
- **Key Components**:
  - `main.py` - FastAPI application entry point
  - `models_mgr.py` - AI model management (supports multiple AI providers)
  - `chatsession_mgr.py` - Chat session management
  - `db_mgr.py` - SQLite database operations
  - `lancedb_mgr.py` - Vector database for embeddings
  - `multivector_mgr.py` - Multi-vector search capabilities
  - `task_mgr.py` - Asynchronous task management

### Frontend (Tauri + React)
- **Location**: `leaf-know/` directory
- **Technology Stack**:
  - Tauri 2.x (Rust backend for desktop app)
  - React 19.1.0 with TypeScript
  - Vite for development and building
  - Tailwind CSS for styling
  - Radix UI components
- **Key Features**:
  - AI chat interface with streaming responses
  - Document management and upload
  - Vector search and retrieval
  - Knowledge graph visualization (@xyflow/react)

### Data Storage
- **SQLite**: Primary database at `~/Library/Application Support/com.leafmove.leaf-know/sqlite.db`
- **LanceDB**: Vector database for embeddings and semantic search

## Development Commands

### Starting the Full Application

**Method 1: Using Scripts (Recommended)**
```bash
# Terminal 1: Start API backend
cd core
./core_standalone.sh  # Automatically reads Tauri config and sets up DB path

# Terminal 2: Start frontend application
cd leaf-know
./dev.sh
```

**Method 2: Manual Commands**
```bash
# Terminal 1: Start API backend
cd core
uv sync
uv run main.py --port 60000 --host 127.0.0.1 --db-path "sqlite.db"

# Terminal 2: Start frontend application
cd leaf-know
bun install  # or npm install
bun tauri dev  # or npm run tauri dev
```

### Development-Only Commands

**Frontend Web Development (No Tauri)**
```bash
cd leaf-know
bun install
bun run dev
# Access at http://localhost:1420
```

**API Development Only**
```bash
cd core
uv sync
uv run main.py --port 60000 --host 127.0.0.1
# API docs at http://127.0.0.1:60000/docs
# Health check at http://127.0.0.1:60000/health
```

### Building and Testing

**Build Frontend for Production**
```bash
cd leaf-know
bun run build
```

**Build Tauri Application**
```bash
cd leaf-know
bun run tauri build
```

**Run Compatibility Tests**
```bash
cd core
python test_compatibility.py  # Test Python version and dependencies
```

**Run Single Test**
```bash
cd core
uv run python test_agno.py  # Test agno library imports (if exists)
```

## Key Technologies

### Backend Dependencies
- **Python**: >= 3.10 (required)
- **FastAPI**: Web framework for API
- **SQLModel**: Database ORM with Pydantic integration
- **LanceDB**: Vector database for embeddings
- **Pydantic-AI**: AI agent framework
- **UV**: Python package manager
- **Docling**: Document processing (PDF, DOCX, PPTX, etc.)
- **MarkItDown**: Markdown conversion for various formats
- **Tiktoken**: Token counting for AI models

### Frontend Dependencies
- **Node.js**: >= 18.0.0
- **Bun**: Package manager (can use npm as alternative)
- **Rust**: >= 1.70.0 (required for Tauri)
- **React 19.1.0**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Tauri 2.x**: Desktop application framework
- **Vite**: Build tool and dev server
- **Tailwind CSS 4.x**: Utility-first CSS framework
- **AI SDK React**: AI model integration
- **Radix UI**: Component library
- **Zustand**: State management
- **React Flow**: Knowledge graph visualization

### AI Integration
- **Multiple AI Providers**: Supports various AI models through `models_mgr.py`
- **Built-in Models**: Pre-configured embedding and VLM models in `config.py`
- **Document Processing**: Multi-format document parsing and extraction
- **Vector Search**: Semantic search with LanceDB integration
- **Multi-vector Search**: Advanced search capabilities via `multivector_mgr.py`
- **Tool Integration**: External AI tool integration via `tool_provider.py`

## Architecture Overview

LeafKnow implements a sophisticated RAG (Retrieval-Augmented Generation) system with the following key architectural components:

### AI Model Management System
- **`models_mgr.py`**: Central AI model manager supporting multiple providers (OpenAI, Anthropic, local models)
- **`model_config_mgr.py`**: Model configuration and capability management
- **`model_capability_confirm.py`**: Model capability validation
- **`models_builtin.py`**: Built-in model configurations

### Chat and Memory System
- **`chatsession_mgr.py`**: Chat session lifecycle management
- **`chatsession_api.py`**: RESTful API for chat operations
- **`memory_mgr.py`**: Conversation memory and context management

### Document and Vector Search System
- **`documents_api.py`**: Document upload and processing API
- **`lancedb_mgr.py`**: Vector database operations with LanceDB
- **`multivector_mgr.py`**: Advanced multi-vector search capabilities
- **`search_mgr.py`**: Unified search interface

### Task and Tool Integration
- **`task_mgr.py`**: Asynchronous task management
- **`tool_provider.py`**: External AI tool integration

### Data Layer
- **`db_mgr.py`**: SQLite database operations for persistent storage
- **`utils.py`**: Shared utilities and helper functions

## Project Structure

```
LeafKnow/
├── core/                   # Python FastAPI backend
│   ├── main.py            # FastAPI application entry point
│   ├── models_mgr.py      # AI model management (multi-provider support)
│   ├── model_config_mgr.py # Model configuration and validation
│   ├── chatsession_*.py   # Chat session management and API
│   ├── db_mgr.py          # SQLite database operations
│   ├── lancedb_mgr.py     # Vector database (LanceDB) operations
│   ├── multivector_mgr.py # Multi-vector search capabilities
│   ├── search_mgr.py      # Unified search interface
│   ├── task_mgr.py        # Asynchronous task management
│   ├── tool_provider.py   # External AI tool integration
│   ├── documents_api.py   # Document processing and upload API
│   ├── models_api.py      # AI model API endpoints
│   ├── memory_mgr.py      # Conversation memory management
│   ├── config.py          # Built-in model configurations
│   ├── utils.py           # Shared utilities
│   ├── core_standalone.sh  # Core startup script (reads Tauri config)
│   ├── test_compatibility.py # Environment compatibility tests
│   └── pyproject.toml     # Python dependencies
├── leaf-know/             # Tauri + React frontend
│   ├── src/               # React source code
│   │   ├── App.tsx        # Main application component
│   │   ├── ai-sdk-chat.tsx # AI chat interface
│   │   ├── rag-local.tsx  # RAG functionality
│   │   └── components/    # React components
│   ├── src-tauri/         # Tauri backend (Rust)
│   │   ├── src/
│   │   │   ├── main.rs    # Tauri entry point
│   │   │   ├── lib.rs     # Main library
│   │   │   └── api_startup.rs # API startup management
│   │   └── tauri.conf.json # Tauri configuration
│   ├── package.json       # Node.js dependencies
│   ├── vite.config.ts     # Vite configuration
│   ├── tailwind.config.js # Tailwind CSS configuration
│   ├── dev.sh             # Frontend startup script
│   └── build.sh           # Production build script
├── docs/                  # Project documentation
├── CLAUDE.md             # This file
├── README.md             # Project overview
└── .gitignore            # Git ignore rules
```

## Important Configuration

### Database Configuration
- **SQLite Database**: Automatically created at `~/Library/Application Support/com.leafmove.leaf-know/sqlite.db`
- **LanceDB**: Used for vector embeddings and semantic search
- **WAL Mode**: SQLite uses WAL mode for better concurrency

### Built-in Model Configuration
The project includes built-in model configurations in `core/config.py`:
- **Embedding Models**: Support for LLAMACPPPYTHON and MLXCOMMUNITY backends
- **VLM (Vision Language Models)**: Qwen3-VL-4B-Instruct with configurable context length
- **Vector Dimensions**: 768 dimensions for embeddings
- **Max Output Tokens**: 2048 tokens for VLM responses

### Port Configuration
- **API Backend**: Port 60000 (configurable via `--port` argument)
- **Frontend Dev Server**: Port 1420 (Vite default, fixed in Tauri config)
- **HMR Port**: 1421 for hot module replacement

### Environment Setup Requirements
1. **Python 3.10+** - Critical requirement, project requires Python 3.10+
2. **Rust toolchain** - Required for Tauri compilation
3. **Node.js 18+** - For frontend development
4. **UV package manager** - For Python dependency management
5. **Bun (recommended)** - For Node.js dependency management
6. **jq** - Required for API startup script (reads Tauri config)

### Key Configuration Files
- `core/pyproject.toml` - Python dependencies and project metadata
- `leaf-know/package.json` - Node.js dependencies and scripts
- `leaf-know/src-tauri/tauri.conf.json` - Tauri application configuration
- `leaf-know/vite.config.ts` - Vite build configuration
- `core/config.py` - Backend configuration and built-in model settings

## Development Workflow

### Daily Development
1. Start API backend in one terminal
2. Start Tauri frontend in another terminal
3. Make changes to code
4. Frontend hot-reloads automatically
5. API changes require restart

### API Development
- Access interactive API docs at `http://127.0.0.1:60000/docs`
- Check API health at `http://127.0.0.1:60000/health`
- API supports CORS for frontend development
- Model configurations and capabilities can be tested via the API

### Frontend Development
- React components hot-reload on save
- Tauri native APIs available through `@tauri-apps/api`
- Use `@/` alias for imports from src directory
- AI chat interface uses streaming responses via AI SDK

### Debugging and Troubleshooting
- **API**: Check terminal output for logs and errors
- **Frontend**: Use browser DevTools (F12) in Tauri app
- **Database**: SQLite database location in config above
- **Model Issues**: Check model configurations in `config.py` and verify with `test_compatibility.py`

## Key Integration Points

### Model Integration
When adding new AI models:
1. Update `models_builtin.py` with built-in configurations
2. Modify `models_mgr.py` for provider integration
3. Update `model_config_mgr.py` for capability validation
4. Test with `test_compatibility.py`

### Document Processing
Documents are processed through:
1. **Upload**: Via `documents_api.py`
2. **Extraction**: Using Docling and MarkItDown libraries
3. **Embedding**: Through configurable embedding models
4. **Vector Storage**: In LanceDB via `lancedb_mgr.py`

### Chat System Flow
1. **Session Creation**: `chatsession_mgr.py` creates session
2. **Context Retrieval**: Vector search via `search_mgr.py`
3. **Model Inference**: Through `models_mgr.py`
4. **Response Generation**: With memory from `memory_mgr.py`

## Notes

- The project requires Python 3.10+ - upgrade required for Python 3.8 systems
- API startup script automatically reads Tauri configuration for database path
- Built-in models support both local (LLAMACPPPYTHON, MLXCOMMUNITY) and cloud providers
- Multi-vector search enables advanced semantic search capabilities
- The application is designed for desktop deployment with local data storage
- All AI model configurations are centralized in `config.py` for easy modification
