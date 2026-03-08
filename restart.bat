@echo off
chcp 65001 >nul
echo [重启] 正在关闭占用8000端口的进程...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    echo [关闭] 进程 PID: %%a
    taskkill /PID %%a /F 2>nul
)

echo.
echo [启动] 启动后端服务器...
start "ClawLoom Backend" cmd /k "cd /d %~dp0engine && python -m uvicorn api.server_full:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 2 >nul

echo [启动] 启动前端服务器...
start "ClawLoom Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo [完成] 服务已重启！
echo 后端: http://localhost:8000
echo 前端: http://localhost:3000
pause
