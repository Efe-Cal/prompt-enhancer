@echo off
echo ============================================
echo Starting PromptEnhance Services
echo ============================================
echo.

REM Ensure Redis is running (Docker)
echo [1/3] Checking Redis...
redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo   X Redis is not running. Starting with Docker...
    docker ps --filter "name=promptenhance-redis" --format "{{.ID}}" | findstr /r "." >nul 2>&1
    if %errorlevel% neq 0 (
        docker run -d --name promptenhance-redis -p 6379:6379 redis >nul 2>&1
    ) else (
        docker start promptenhance-redis >nul 2>&1
        if %errorlevel% neq 0 (
            echo   X Failed to start existing Redis container.
            echo   Please ensure Docker Desktop is running.
            echo.
            pause
            exit /b 1
        )
    )

) else (
    echo   - Redis is running
)

echo.
echo [2/3] Starting Celery worker...
start "Celery Worker" cmd /k "cd backend && ..\venv\Scripts\activate && celery -A backend worker --loglevel=info --pool=solo"

echo.
echo [3/3] Starting Django with Daphne...
timeout /t 3 /nobreak >nul
start "Django Server" cmd /k "cd backend && ..\venv\Scripts\activate && daphne -b 0.0.0.0 -p 8000 backend.asgi:application"

echo.
echo ============================================
echo Services Started!
echo ============================================
echo.
echo Celery Worker: Running in separate window
echo Django Server: Running on http://localhost:8000
echo.
echo Press any key to close this window...
pause >nul
