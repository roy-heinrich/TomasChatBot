# 🔐 SECURITY GUIDE - Tomas Chatbot API

## 🚨 URGENT: Your API is Currently Public!

Your chatbot API at [https://web-production-7609.up.railway.app/](https://web-production-7609.up.railway.app/) is **completely open** to anyone on the internet. This means:

- ❌ **Anyone can use your API** without permission
- ❌ **Unlimited requests** can be made
- ❌ **No rate limiting** or usage controls
- ❌ **Potential cost overruns** from AI provider usage
- ❌ **Resource abuse** possible

## 🛡️ IMMEDIATE SECURITY FIXES

### **Step 1: Add API Key Authentication**

I've created a secure version of your API (`app_secure.py`) with the following security features:

✅ **API Key Authentication** - All endpoints require valid API keys  
✅ **Admin Key Protection** - Admin endpoints have separate authentication  
✅ **Bearer Token Security** - Uses HTTP Bearer authentication  
✅ **Error Handling** - Proper error responses for unauthorized access  

### **Step 2: Set Up Environment Variables**

Add these to your Railway environment variables:

```env
# API Security Keys
API_KEY=your_secure_api_key_here
ADMIN_KEY=your_secure_admin_key_here

# Existing variables
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
GROQ_API_KEY=your_groq_key
COHERE_API_KEY=your_cohere_key
HUGGINGFACE_API_KEY=your_huggingface_key
```

### **Step 3: Generate Secure Keys**

Run this to generate secure keys:

```python
import secrets
print("API_KEY=" + secrets.token_urlsafe(32))
print("ADMIN_KEY=" + secrets.token_urlsafe(32))
```

### **Step 4: Deploy Secure Version**

1. **Replace `app.py` with `app_secure.py`**
2. **Update Railway environment variables**
3. **Redeploy your application**

## 🔒 Security Features Added

### **Authentication Levels**

1. **Public Endpoints** (No auth required):
   - `GET /` - Health check
   - `GET /health` - System status

2. **Protected Endpoints** (API key required):
   - `POST /chat` - Main chatbot endpoint
   - `POST /clear-context` - Clear conversation memory

3. **Admin Endpoints** (Admin key required):
   - `GET /admin/logs` - System logs
   - `GET /admin/metrics` - Performance metrics
   - `POST /admin/clear-cache` - Clear caches
   - `GET /admin/generate-keys` - Generate new keys

### **Usage Examples**

#### **With API Key (Regular Usage)**
```bash
curl -X POST "https://web-production-7609.up.railway.app/chat" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "Who is the principal?", "session_id": "user123"}'
```

#### **With Admin Key (Admin Functions)**
```bash
curl -X GET "https://web-production-7609.up.railway.app/admin/metrics" \
  -H "Authorization: Bearer YOUR_ADMIN_KEY"
```

## 🚀 Deployment Steps

### **Option 1: Quick Fix (Recommended)**

1. **Generate keys**:
```bash
python -c "import secrets; print('API_KEY=' + secrets.token_urlsafe(32)); print('ADMIN_KEY=' + secrets.token_urlsafe(32))"
```

2. **Update Railway environment variables** with the generated keys

3. **Replace app.py**:
```bash
cp app_secure.py app.py
```

4. **Redeploy**:
```bash
git add .
git commit -m "Add API key authentication"
git push
```

### **Option 2: Gradual Migration**

1. **Test secure version locally**:
```bash
python app_secure.py
```

2. **Verify authentication works**

3. **Deploy to Railway**

## 🔧 Configuration Options

### **CORS Settings**
Update the CORS middleware in `app_secure.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com", "https://anotherdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### **Rate Limiting** (Optional)
Add rate limiting middleware:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/chat")
@limiter.limit("10/minute")  # 10 requests per minute
async def chat_endpoint(request: Request, data: ChatRequest, api_key: str = Depends(verify_api_key)):
    # ... existing code
```

## 📊 Monitoring & Alerts

### **Set Up Monitoring**
1. **Railway Metrics** - Monitor CPU, memory, and request count
2. **API Usage Tracking** - Track requests per API key
3. **Cost Monitoring** - Monitor AI provider usage costs

### **Alert Thresholds**
- **High request volume** (>1000 requests/hour)
- **Unusual usage patterns** (requests from new IPs)
- **Cost spikes** (AI provider usage increases)

## 🆘 Emergency Procedures

### **If API is Being Abused**
1. **Immediately rotate API keys**:
```bash
curl -X GET "https://web-production-7609.up.railway.app/admin/generate-keys" \
  -H "Authorization: Bearer YOUR_ADMIN_KEY"
```

2. **Update environment variables** with new keys

3. **Restart the application**

### **If Keys are Compromised**
1. **Generate new keys immediately**
2. **Update all client applications**
3. **Monitor for suspicious activity**

## ✅ Security Checklist

- [ ] API key authentication implemented
- [ ] Admin key protection added
- [ ] Environment variables secured
- [ ] CORS configured for specific domains
- [ ] Rate limiting implemented (optional)
- [ ] Monitoring and alerts set up
- [ ] Emergency procedures documented
- [ ] Client applications updated with new keys

## 🔐 Best Practices

1. **Never commit API keys** to version control
2. **Rotate keys regularly** (monthly)
3. **Use different keys** for different environments
4. **Monitor usage patterns** for anomalies
5. **Implement rate limiting** for public APIs
6. **Use HTTPS only** in production
7. **Log all API access** for auditing

## 📞 Support

If you need help implementing these security measures:

1. **Test locally** with the secure version
2. **Verify authentication** works correctly
3. **Update client applications** with new API keys
4. **Monitor usage** after deployment

---

**⚠️ IMPORTANT: Implement these security measures immediately to protect your API from unauthorized access and potential abuse!**
