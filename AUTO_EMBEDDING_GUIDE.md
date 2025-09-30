# 🤖 Auto Embedding Generation Guide

## Overview
This guide shows you how to automatically generate embeddings whenever new data is added to your Supabase database.

## 🚀 Setup Options

### Option 1: Background Monitor (Recommended for Development)
Runs a background process that checks for new records every 30 seconds.

```bash
# Start the background monitor
python auto_embedding_system.py --mode monitor

# Or with custom check interval
python auto_embedding_system.py --mode monitor --check-interval 60
```

### Option 2: Webhook Server (Recommended for Production)
Runs a webhook server that Supabase can call when new records are added.

```bash
# Start the webhook server
python auto_embedding_system.py --mode webhook
```

### Option 3: One-time Processing
Process all existing records without embeddings.

```bash
# Process existing records
python auto_embedding_system.py --mode process
```

## 🔧 Supabase Setup

### 1. Run SQL Triggers
Copy and paste the contents of `auto_embedding_triggers.sql` into your Supabase SQL Editor and execute it.

### 2. Set Up Webhook (Optional)
If using the webhook server, configure Supabase to call your webhook URL:

1. Go to Supabase Dashboard → Database → Webhooks
2. Create a new webhook
3. Set the URL to your webhook endpoint (e.g., `https://your-app.com/webhook/embedding`)
4. Select the `chatbot_prompts` table
5. Choose `INSERT` and `UPDATE` events

## 🚀 Integration with Main Chatbot

### Automatic Integration
```bash
# Integrate auto embeddings into your chatbot
python integrate_auto_embeddings.py
```

### Manual Integration
Add this to your `chatbot_refactored.py`:

```python
# Add import
from core.auto_embedding_generator import AutoEmbeddingGenerator

# In __init__ method
self.auto_embedding = AutoEmbeddingGenerator()

# Use in your code
await self.auto_embedding.process_new_record(record_id, keywords, response)
```

## 📊 Monitoring

### Check Embedding Status
```sql
-- Run this in Supabase SQL Editor
SELECT * FROM check_embedding_status();
```

### Process Missing Embeddings
```sql
-- Run this in Supabase SQL Editor
SELECT * FROM generate_missing_embeddings();
```

## 🔄 How It Works

### Background Monitor
1. Checks for records without embeddings every 30 seconds
2. Generates embeddings for new records
3. Updates the database with embeddings
4. Continues monitoring

### Webhook Server
1. Receives webhook from Supabase when new records are added
2. Generates embedding for the new record
3. Updates the record with the embedding
4. Returns success/failure status

### SQL Triggers
1. Automatically triggered when records are inserted/updated
2. Calls webhook or logs the action
3. Ensures all new records get embeddings

## 🚀 Deployment

### For Development
```bash
# Start background monitor
python auto_embedding_system.py --mode monitor
```

### For Production
```bash
# Start webhook server
python auto_embedding_system.py --mode webhook
```

### For Render Deployment
Add this to your `render.yaml`:

```yaml
services:
  - type: web
    name: tomas-chatbot-embeddings
    env: python
    plan: free
    buildCommand: |
      pip install --upgrade pip
      pip install -r requirements.txt
    startCommand: python auto_embedding_system.py --mode webhook
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
```

## 🧪 Testing

### Test Auto Embeddings
```bash
# Test the functionality
python integrate_auto_embeddings.py
```

### Test Webhook
```bash
# Start webhook server
python auto_embedding_system.py --mode webhook

# Test with curl
curl -X POST http://localhost:8001/webhook/embedding \
  -H "Content-Type: application/json" \
  -d '{"type": "INSERT", "record": {"id": 1, "keywords": "test", "response": "test response"}}'
```

## 📈 Performance

### Memory Usage
- Model is loaded only when needed
- Automatically unloaded after use
- Garbage collection runs after each operation

### Speed
- Embedding generation: ~100-200ms per record
- Database update: ~50-100ms per record
- Total processing: ~150-300ms per record

### Scalability
- Background monitor: Handles 100+ records per minute
- Webhook server: Handles real-time processing
- SQL triggers: Instant processing

## 🔧 Troubleshooting

### Common Issues

**1. "Model not loaded" error**
```bash
# Check if sentence-transformers is installed
pip install sentence-transformers
```

**2. "Supabase connection failed"**
```bash
# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_KEY
```

**3. "Webhook not receiving calls"**
- Check Supabase webhook configuration
- Verify webhook URL is accessible
- Check webhook server logs

### Debug Mode
```bash
# Run with debug logging
PYTHONPATH=. python auto_embedding_system.py --mode monitor
```

## 🎯 Best Practices

### 1. Use Background Monitor for Development
- Easy to start/stop
- Good for testing
- Handles batch processing

### 2. Use Webhook Server for Production
- Real-time processing
- More efficient
- Better for high-volume systems

### 3. Monitor Performance
- Check embedding status regularly
- Monitor memory usage
- Watch for errors in logs

### 4. Backup Strategy
- Keep original data safe
- Test embedding generation
- Have fallback plans

## 🚀 Next Steps

1. **Choose your setup method** (background monitor or webhook)
2. **Run the SQL triggers** in Supabase
3. **Start the auto embedding system**
4. **Test with new records**
5. **Monitor performance**

Your chatbot will now automatically generate embeddings for all new data! 🎉
