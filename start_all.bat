@echo off
chcp 65001 >nul
echo ==========================================
echo    ClawLoom - 启动全部服务
echo ==========================================
echo.

:: 检查 Python
echo [检查] Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请安装 Python 3.9+
    pause
    exit /b 1
)

:: 检查 Node.js
echo [检查] Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js，请安装 Node.js 18+
    pause
    exit /b 1
)

echo [OK] 环境检查通过
echo.

:: 启动后端 (使用新的完整版服务器)
echo [启动] 后端服务器 v2 (http://localhost:8000)...
start "ClawLoom Backend" cmd /k "cd /d %~dp0engine && python -m uvicorn api.server_full:app --host 0.0.0.0 --port 8000"

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: 启动前端
echo [启动] 前端开发服务器 (http://localhost:3000)...
start "ClawLoom Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ==========================================
echo    服务已启动！
echo ==========================================
echo.
echo 后端 API:   http://localhost:8000
echo 前端界面:   http://localhost:3000
echo API 文档:   http://localhost:8000/docs
echo.
echo 可用功能:
echo   - 织主注册/登录
echo   - API Key 管理
echo   - AI 认领绑定
echo   - 世界创造与管理
echo.
echo 按任意键打开浏览器...
pause >nul

start http://localhost:3000
