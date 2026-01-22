@echo off
setlocal EnableDelayedExpansion
echo ============================================
echo Starting PromptEnhance Services
echo ============================================
echo.

REM Ensure Redis is running (Docker)
echo [1/2] Checking Redis...
netstat -an | findstr ":6379" >nul 2>&1
if !errorlevel! neq 0 (
    echo   X Redis is not running. Starting with Docker...
    
    REM Check if Docker is running
    docker info >nul 2>&1
    if !errorlevel! neq 0 (
        echo   X Docker is not running. Please start Docker Desktop first.
        pause
        exit /b 1
    )
    
    REM Check if container exists using docker container inspect
    docker container inspect promptenhance-redis >nul 2>&1
    if !errorlevel! neq 0 (
        echo   - Creating new Redis container...
        docker run -d --name promptenhance-redis -p 6379:6379 redis:latest
        if !errorlevel! neq 0 (
            echo   X Failed to create Redis container.
            pause
            exit /b 1
        )
    ) else (
        echo   - Starting existing Redis container...
        docker start promptenhance-redis >nul 2>&1
        if !errorlevel! neq 0 (
            echo   X Failed to start existing Redis container.
            pause
            exit /b 1
        )
    )
    echo   - Waiting for Redis to start...
    timeout /t 3 /nobreak >nul
) else (
    echo   - Redis is running
)

echo.
echo [2/2] Starting Django with Daphne...
start "Django Server" cmd /k "cd backend && ..\venv\Scripts\activate && daphne -b 0.0.0.0 -p 8000 backend.asgi:application"

echo.
echo ============================================
echo Services Started!
echo ============================================
echo.
echo Django Server: Running on http://localhost:8000
echo.
timeout /t 2
start "" http://localhost:8000
echo Press any key to close this window...
pause >nul
