# Railway Deployment Guide - Optimized for Timeouts

## Problem
Railway builds are timing out during the Docker build process, specifically during the "importing to docker" phase.

## Solutions Applied

### 1. Micro Requirements (`requirements_micro.txt`)
- Absolute minimum dependencies
- No heavy packages like `cohere`, `gunicorn`
- Only essential packages for core functionality

### 2. Micro Dockerfile (`Dockerfile.micro`)
- Minimal system dependencies
- Aggressive caching strategy
- Only copies essential files
- Increased timeouts: `--timeout=3000 --retries=15`

### 3. Optimized .dockerignore
- Excludes all development files
- Reduces build context size
- Faster Docker build

## Deployment Steps

### Option 1: Use Micro Dockerfile (Recommended)
```bash
# Update railway.toml to use micro Dockerfile
# Already configured in railway.toml

git add .
git commit -m "Micro requirements for Railway deployment"
git push origin main
```

### Option 2: Manual Docker Build (Testing)
```bash
# Test locally first
docker build -f Dockerfile.micro -t tomas-chatbot:latest .

# If successful, deploy to Railway
git add .
git commit -m "Micro requirements for Railway deployment"
git push origin main
```

### Option 3: Alternative Requirements
If still timing out, try these in order:
1. `requirements_micro.txt` (current)
2. `requirements_ultra_minimal.txt`
3. `requirements_minimal.txt`

## Railway Configuration
- **Builder**: dockerfile
- **Dockerfile**: Dockerfile.micro
- **Timeout**: 3000 seconds
- **Retries**: 15
- **Health Check**: 300 seconds

## Monitoring
- Check Railway logs for build progress
- Look for "pip install" completion time
- Monitor "importing to docker" phase

## Fallback Options
If micro requirements don't work:
1. Try removing `sentence-transformers` temporarily
2. Use `requirements_fallback.txt`
3. Consider Railway's build timeout limits
4. Contact Railway support for timeout issues

## Success Indicators
- ✅ `pip install` completes in < 2 minutes
- ✅ "importing to docker" completes in < 1 minute
- ✅ Total build time < 5 minutes
- ✅ No timeout errors
