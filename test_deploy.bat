@echo off
echo Testing Railway deployment locally...

echo.
echo Checking requirements_micro.txt...
if not exist requirements_micro.txt (
    echo ERROR: requirements_micro.txt not found!
    exit /b 1
)

echo.
echo Building Docker image with micro requirements...
docker build -f Dockerfile -t tomas-chatbot:latest .

if %errorlevel% equ 0 (
    echo.
    echo ✅ Docker build successful!
    echo 🚀 Ready for Railway deployment!
    echo.
    echo Next steps:
    echo 1. git add .
    echo 2. git commit -m "Micro requirements for Railway deployment"
    echo 3. git push origin main
) else (
    echo.
    echo ❌ Docker build failed!
    exit /b 1
)
