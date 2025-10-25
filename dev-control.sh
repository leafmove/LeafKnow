#!/bin/bash

# LeafKnow 开发环境控制脚本
# 用于手动启动和停止开发环境

PROJECT_DIR="/Users/wample/coding/me/LeafKnow"
FRONTEND_DIR="$PROJECT_DIR/leaf-know"
API_DIR="$PROJECT_DIR/api"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo -e "${BLUE}LeafKnow 开发环境控制脚本${NC}"
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  start     启动完整开发环境"
    echo "  stop      停止所有相关进程"
    echo "  status    显示当前进程状态"
    echo "  frontend  仅启动前端开发服务器"
    echo "  api       仅启动后端 API 服务"
    echo "  tauri     启动 Tauri 应用"
    echo "  logs      显示实时日志"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start    # 启动完整环境"
    echo "  $0 stop     # 停止所有服务"
    echo "  $0 status   # 查看状态"
}

# 检查进程状态
check_status() {
    echo -e "${BLUE}=== LeafKnow 进程状态 ===${NC}"
    echo ""

    # 检查 Tauri 进程
    TAURI_PROCESS=$(ps aux | grep -E "leaf-know" | grep -v grep)
    if [ -n "$TAURI_PROCESS" ]; then
        echo -e "${GREEN}✓ Tauri 应用正在运行${NC}"
        echo "$TAURI_PROCESS" | awk '{print "  PID: " $2 " | 命令: " $11 " " $12}'
    else
        echo -e "${RED}✗ Tauri 应用未运行${NC}"
    fi

    # 检查 Vite 进程
    VITE_PROCESS=$(ps aux | grep -E "vite.*1420" | grep -v grep)
    if [ -n "$VITE_PROCESS" ]; then
        echo -e "${GREEN}✓ Vite 前端服务器正在运行 (http://localhost:1420)${NC}"
        echo "$VITE_PROCESS" | awk '{print "  PID: " $2}'
    else
        echo -e "${RED}✗ Vite 前端服务器未运行${NC}"
    fi

    # 检查 API 进程
    API_PROCESS=$(ps aux | grep -E "python.*60000" | grep -v grep)
    if [ -n "$API_PROCESS" ]; then
        echo -e "${GREEN}✓ Python API 服务正在运行 (http://127.0.0.1:60000)${NC}"
        echo "$API_PROCESS" | awk '{print "  PID: " $2}'
    else
        echo -e "${RED}✗ Python API 服务未运行${NC}"
    fi

    echo ""
}

# 停止所有进程
stop_all() {
    echo -e "${YELLOW}正在停止所有 LeafKnow 进程...${NC}"

    # 停止 Tauri
    pkill -f "leaf-know" 2>/dev/null && echo -e "${GREEN}✓ 已停止 Tauri 应用${NC}"

    # 停止 Vite
    pkill -f "vite.*1420" 2>/dev/null && echo -e "${GREEN}✓ 已停止 Vite 服务器${NC}"

    # 停止 API
    pkill -f "python.*60000" 2>/dev/null && echo -e "${GREEN}✓ 已停止 Python API${NC}"

    # 停止可能的 bun 进程
    pkill -f "bun.*run.*dev" 2>/dev/null && echo -e "${GREEN}✓ 已停止 bun dev${NC}"

    echo -e "${GREEN}所有进程已停止${NC}"
}

# 启动 API 服务
start_api() {
    echo -e "${YELLOW}启动 Python API 服务...${NC}"
    cd "$API_DIR"
    if [ -f "main.py" ]; then
        # 使用 nohup 在后台启动 API
        nohup uv run main.py --host 127.0.0.1 --port 60000 --db-path "/Users/wample/Library/Application Support/com.leafmove.leaf-know/sqlite.db" > api.log 2>&1 &
        sleep 2
        echo -e "${GREEN}✓ API 服务已启动 (日志: api.log)${NC}"
    else
        echo -e "${RED}✗ 未找到 main.py 文件${NC}"
    fi
}

# 启动前端服务器
start_frontend() {
    echo -e "${YELLOW}启动 Vite 前端服务器...${NC}"
    cd "$FRONTEND_DIR"
    if [ -f "package.json" ]; then
        # 使用 nohup 在后台启动前端
        nohup bun run dev > frontend.log 2>&1 &
        sleep 2
        echo -e "${GREEN}✓ 前端服务器已启动 (http://localhost:1420, 日志: frontend.log)${NC}"
    else
        echo -e "${RED}✗ 未找到 package.json 文件${NC}"
    fi
}

# 启动 Tauri 应用
start_tauri() {
    echo -e "${YELLOW}启动 Tauri 应用...${NC}"
    cd "$FRONTEND_DIR/src-tauri"

    # 检查是否需要加载 Rust 环境
    if [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    fi

    # 启动 Tauri（保持在前台运行）
    echo -e "${BLUE}启动 Tauri 开发服务器...${NC}"
    echo -e "${YELLOW}提示: 使用 Ctrl+C 停止应用${NC}"
    cargo run
}

# 启动完整开发环境
start_full() {
    echo -e "${BLUE}启动 LeafKnow 完整开发环境...${NC}"
    echo ""

    # 1. 启动 API
    start_api
    sleep 3

    # 2. 启动前端
    start_frontend
    sleep 3

    # 3. 启动 Tauri
    echo -e "${YELLOW}现在启动 Tauri 桌面应用...${NC}"
    start_tauri
}

# 显示日志
show_logs() {
    echo -e "${BLUE}=== 实时日志 ===${NC}"
    echo -e "${YELLOW}API 日志 (api.log):${NC}"
    if [ -f "$API_DIR/api.log" ]; then
        tail -f "$API_DIR/api.log" &
    fi

    echo -e "${YELLOW}前端日志 (frontend.log):${NC}"
    if [ -f "$FRONTEND_DIR/frontend.log" ]; then
        tail -f "$FRONTEND_DIR/frontend.log" &
    fi

    # 等待用户中断
    trap 'killall tail 2>/dev/null; exit' INT
    wait
}

# 主逻辑
case "$1" in
    start)
        start_full
        ;;
    stop)
        stop_all
        ;;
    status)
        check_status
        ;;
    frontend)
        start_frontend
        ;;
    api)
        start_api
        ;;
    tauri)
        start_tauri
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}未知选项: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac