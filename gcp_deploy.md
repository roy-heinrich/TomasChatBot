# 🚀 Google Cloud Run Deployment Guide

## Why Google Cloud Run is Perfect

- ✅ **2 million requests/month FREE**
- ✅ **No credit card required**
- ✅ **No sleep mode**
- ✅ **Supports heavy ML dependencies**
- ✅ **Global deployment**
- ✅ **Pay-per-use** (very cheap)

## 🚀 Quick Deployment Steps

### 1. Set up Google Cloud (Free)
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Sign up with your Google account
3. Create a new project (or use existing)
4. Enable Cloud Run API
5. **No credit card required!**

### 2. Install Google Cloud CLI
```bash
# Windows (PowerShell)
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& "$env:Temp\GoogleCloudSDKInstaller.exe"
```

### 3. Deploy Your Chatbot
```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Deploy to Cloud Run
gcloud run deploy tomas-chatbot --source . --region asia-southeast1 --allow-unauthenticated
```

### 4. Set Environment Variables
In Google Cloud Console:
- Go to Cloud Run → tomas-chatbot → Edit
- Add environment variables:
  - `GROQ_API_KEY=your_key`
  - `SUPABASE_URL=your_url`
  - `SUPABASE_KEY=your_key`
  - `COHERE_API_KEY=your_key`

## 📊 Free Tier Limits

- **Requests**: 2 million/month
- **CPU**: 1 vCPU per request
- **Memory**: 1GB per request
- **Timeout**: 300 seconds
- **Concurrent**: 10 requests

## 💰 Cost After Free Tier

- **CPU**: $0.00002400 per vCPU-second
- **Memory**: $0.00000250 per GB-second
- **Requests**: $0.40 per million requests

**Your chatbot will likely stay within free tier!**

## 🎯 Benefits

- ✅ **Completely free** for your use case
- ✅ **No timeout issues** with ML dependencies
- ✅ **No sleep mode** - always responsive
- ✅ **Global deployment** - fast worldwide
- ✅ **Auto-scaling** - handles traffic spikes
- ✅ **No credit card required**

## 🚀 Deploy Now!

1. **Sign up**: [console.cloud.google.com](https://console.cloud.google.com)
2. **Create project**: Choose a name
3. **Enable APIs**: Cloud Run API
4. **Deploy**: Use the commands above
5. **Done!** 🎉

Your chatbot will be live with full ML capabilities!
