Write-Host "Testing Railway deployment locally..." -ForegroundColor Green

Write-Host ""
Write-Host "Checking requirements_micro.txt..." -ForegroundColor Yellow
if (-not (Test-Path "requirements_micro.txt")) {
    Write-Host "ERROR: requirements_micro.txt not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Building Docker image with micro requirements..." -ForegroundColor Yellow
docker build -f Dockerfile -t tomas-chatbot:latest .

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Docker build successful!" -ForegroundColor Green
    Write-Host "🚀 Ready for Railway deployment!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. git add ." -ForegroundColor White
    Write-Host "2. git commit -m 'Micro requirements for Railway deployment'" -ForegroundColor White
    Write-Host "3. git push origin main" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ Docker build failed!" -ForegroundColor Red
    exit 1
}
