# Railway Deployment Guide

## Quick Deploy to Railway

1. **Commit all changes to GitHub:**
   ```bash
   git add .
   git commit -m "Optimize for Railway deployment"
   git push origin main
   ```

2. **Connect to Railway:**
   - Go to [Railway.app](https://railway.app)
   - Connect your GitHub repository
   - Railway will automatically detect the Dockerfile

3. **Set Environment Variables in Railway:**
   ```
   GROQ_API_KEY=your_groq_key
   COHERE_API_KEY=your_cohere_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

4. **Deploy:**
   - Railway will automatically build and deploy
   - Monitor the build logs for any issues

## Files Created for Railway:

- ✅ `Dockerfile` - Updated with optimized requirements
- ✅ `requirements_minimal.txt` - Minimal dependencies for faster build
- ✅ `railway.toml` - Railway configuration
- ✅ `.dockerignore` - Optimized Docker build
- ✅ `start.py` - Application startup script

## Build Optimizations:

- **CPU-only PyTorch** - Reduces download size
- **Retry logic** - Handles network timeouts
- **Minimal dependencies** - Faster builds
- **Health checks** - Ensures deployment success

## Troubleshooting:

If build fails:
1. Check Railway build logs
2. Verify all environment variables are set
3. Ensure GitHub repository is public or Railway has access
4. Check if all dependencies are in `requirements_minimal.txt`
