#!/bin/bash

# 简化的 Tauri 开发启动脚本
# 保持在前台运行，方便调试

PROJECT_DIR="/Users/wample/coding/me/LeafKnow/leaf-know"

echo "🚀 启动 LeafKnow 开发环境..."

# 进入项目目录
cd "$PROJECT_DIR"

# 加载 Rust 环境
if [ -f "$HOME/.cargo/env" ]; then
    source "$HOME/.cargo/env"
fi

# 设置环境变量保持前台运行
export TAURI_DEV_KEEP_TERMINAL=true

echo "📝 提示："
echo "   - 使用 Ctrl+C 停止应用"
echo "   - 所有日志将显示在终端中"
echo "   - 应用窗口将在几秒后弹出"
echo ""

# 启动 Tauri 开发服务器（保持在前台）
bun tauri dev