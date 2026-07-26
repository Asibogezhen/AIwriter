@echo off
echo ============================================
echo   SVG AI 动画生成器 - 启动所有服务
echo ============================================
echo.

echo [1/3] 启动 FastAPI 后端 (端口 8000)...
start "Backend" cmd /c "cd /d %~dp0backend && uvicorn backend.main:app --reload --port 8000 --host 0.0.0.0"

echo [2/3] 启动 Vue 前端 (端口 5173)...
start "Frontend" cmd /c "cd /d %~dp0frontend && npm run dev"

echo [3/3] 启动渲染服务 (端口 3001)...
start "RenderService" cmd /c "cd /d %~dp0render-service && npm start"

echo.
echo 所有服务已启动:
echo   后端:  http://localhost:8000
echo   前端:  http://localhost:5173
echo   渲染:  http://localhost:3001
echo.
echo 按任意键停止所有服务...
pause >nul
taskkill /f /fi "WINDOWTITLE eq Backend*" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq Frontend*" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq RenderService*" >nul 2>&1
echo 已停止。
