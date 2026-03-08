#!/bin/bash

echo "=========================================="
echo "   ClawLoom - 启动全部服务"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 检查 Python
echo "[检查] Python..."
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3"
    exit 1
fi
echo "[OK] Python 已安装"

# 检查 Node.js
echo "[检查] Node.js..."
if ! command -v node &> /dev/null; then
    echo "[错误] 未找到 Node.js"
    exit 1
fi
echo "[OK] Node.js 已安装"
echo ""

# 启动后端
echo "[启动] 后端服务器 (http://localhost:8000)..."
cd "$SCRIPT_DIR/engine" || exit 1
python3 -m uvicorn api.server_sqlite:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端
echo "[启动] 前端开发服务器 (http://localhost:3000)..."
cd "$SCRIPT_DIR/frontend" || exit 1
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "   服务已启动！"
echo "=========================================="
echo ""
echo "后端 API: http://localhost:8000"
echo "前端界面: http://localhost:3000"
echo "API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 捕获 Ctrl+C 信号
trap "echo '停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

# 保持脚本运行
wait
