# 🚀 Railway Deployment Guide for Tomas Chatbot

## Why Railway is Perfect for Your Chatbot

- ✅ **No timeout issues** with heavy ML dependencies
- ✅ **$5 monthly credit** (generous free tier)
- ✅ **No sleep mode** - always running
- ✅ **Built-in database** support
- ✅ **Easy GitHub integration**

## 🚀 Quick Deployment Steps

### 1. Sign up for Railway
- Go to [railway.app](https://railway.app)
- Sign up with your GitHub account
- Get $5 monthly credit (no credit card required initially)

### 2. Deploy from GitHub
```bash
# Railway will automatically detect your Python app
# Just connect your GitHub repository
```

### 3. Environment Variables
Set these in Railway dashboard:
```
GROQ_API_KEY=your_groq_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
COHERE_API_KEY=your_cohere_key
HUGGINGFACE_API_KEY=your_hf_key
```

### 4. Deploy!
- Railway will automatically build and deploy
- No timeout issues with `sentence-transformers`
- Full ML capabilities enabled

## 📊 Resource Usage

Your chatbot will use approximately:
- **CPU**: 0.5-1.0 vCPU (well within free tier)
- **RAM**: 512MB-1GB (within limits)
- **Storage**: <100MB (well within 3GB limit)
- **Bandwidth**: Minimal for API calls

## 🎯 Benefits Over Render

| Feature | Railway | Render |
|---------|---------|--------|
| **ML Dependencies** | ✅ No timeouts | ❌ 300s timeout |
| **Sleep Mode** | ❌ Always running | ✅ Sleeps after 15min |
| **Free Tier** | $5/month credit | Limited |
| **Build Time** | No limits | 300s timeout |
| **Database** | Built-in support | External only |

## 🔧 Railway-Specific Optimizations

The `railway.json` file includes:
- **Health check**: `/health` endpoint
- **Timeout**: 300s for health checks
- **Restart policy**: Auto-restart on failure
- **Start command**: `python start.py`

## 📈 Scaling Options

If you need more resources later:
- **Hobby Plan**: $5/month (1GB RAM, 1 vCPU)
- **Pro Plan**: $20/month (8GB RAM, 4 vCPU)
- **Team Plan**: $99/month (unlimited)

## 🚀 Deploy Now!

1. Go to [railway.app](https://railway.app)
2. Click "Deploy from GitHub"
3. Select your TomasChatBot repository
4. Add environment variables
5. Deploy! 🎉

Your chatbot will be live with full ML capabilities in minutes!
