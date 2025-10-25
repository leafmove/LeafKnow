# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LeafKnow appears to be a new project in an empty directory. This is likely a knowledge management or learning platform based on the project name.

## Development Setup

Since this is a new project, the development setup will depend on what technology stack is chosen. Common next steps might include:

- Initializing a git repository: `git init`
- Setting up a package.json for Node.js projects: `npm init`
- Creating initial project structure based on chosen framework

## Architecture

The project architecture will be determined as development begins. Consider the following when making architectural decisions:

- Whether this will be a web application, mobile app, or desktop application
- Frontend framework choice (React, Vue, Angular, etc.)
- Backend requirements (API, database, authentication)
- Deployment strategy

## Common Commands

Commands will be added as the project develops and build tools are configured.

## Development Setup

### Python Environment

- **Python Version**: 3.12.9 (configured via uv)
- **Package Manager**: uv (modern Python package manager)
- **Virtual Environment**: .venv (auto-created by uv)
- **Project Configuration**: pyproject.toml

### Installation Commands

```bash
# Sync dependencies (installs all required packages)
uv sync

# Run Python commands in the project environment
uv run python --version
uv run python main.py

# Install new dependencies
uv add package_name

# Install development dependencies
uv add --dev package_name
```

### Core Dependencies

The project includes the following key dependencies:
- **FastAPI**: Web framework for API development
- **LanceDB**: Vector database for embeddings
- **Docling**: Document parsing and processing
- **Pydantic AI**: AI framework for structured outputs
- **SQLModel**: Database ORM
- **Tiktoken**: Token counting for text processing
- **Uvicorn**: ASGI server for FastAPI

## Task Execution Records

### 2025-10-25
- **任务**: Python版本管理和依赖安装
- **问题描述**: 项目配置要求Python >=3.13，但系统环境兼容性问题导致依赖安装失败
- **执行过程**:
  1. 检查当前系统Python版本和uv管理的Python版本
  2. 卸载不需要的Python 3.14.0版本
  3. 安装并设置Python 3.12.9为项目默认版本
  4. 修改pyproject.toml中的Python版本要求从>=3.13改为>=3.12
  5. 使用uv sync成功安装所有项目依赖（194个包）
- **结果**:
  - Python环境配置完成，使用Python 3.12.9
  - 虚拟环境创建成功(.venv)
  - 所有核心依赖包安装完成并可正常导入
  - 项目ready for development

### Notes

- 项目使用uv作为现代Python包管理工具，提供快速的依赖解析和安装
- 配置了.python-version文件锁定Python 3.12.9版本
- 依赖安装成功，包含194个包，总大小约400MB+
- 核心功能模块验证可正常导入