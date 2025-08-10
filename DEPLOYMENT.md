# 🚀 Deployment Guide for Quest & Rewards MCP Server

This guide will help you deploy your Quest & Rewards MCP server to various cloud platforms.

## 📋 Prerequisites

1. **Python 3.11+** installed
2. **Git** for version control
3. **Environment variables** configured
4. **Domain/URL** for Puch AI to access your server

## 🌐 Deployment Options

### Option 1: Railway (Recommended for Beginners)

Railway is one of the easiest platforms to deploy Python applications.

#### Steps:
1. **Sign up** at [railway.app](https://railway.app)
2. **Connect your GitHub** repository
3. **Create new project** from GitHub repo
4. **Set environment variables:**
   ```
   AUTH_TOKEN=your_secret_token_here
   MY_NUMBER=919876543210
   ```
5. **Deploy** - Railway will automatically detect Python and deploy
6. **Get your URL** from the deployment dashboard

#### Railway Configuration
Create a `railway.json` file in your project root:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "cd mcp-bearer-token && python quest_rewards_mcp.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Option 2: Render

Render provides free hosting for Python applications.

#### Steps:
1. **Sign up** at [render.com](https://render.com)
2. **Create new Web Service**
3. **Connect your GitHub** repository
4. **Configure the service:**
   - **Name:** quest-rewards-mcp
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `cd mcp-bearer-token && python quest_rewards_mcp.py`
5. **Set environment variables** in the dashboard
6. **Deploy**

### Option 3: Heroku

Heroku is a popular platform for Python applications.

#### Steps:
1. **Install Heroku CLI** and sign up
2. **Create `requirements.txt`:**
   ```
   fastmcp>=2.11.2
   python-dotenv>=1.1.1
   pydantic>=2.0.0
   ```
3. **Create `Procfile`:**
   ```
   web: cd mcp-bearer-token && python quest_rewards_mcp.py
   ```
4. **Deploy:**
   ```bash
   heroku create your-quest-app
   heroku config:set AUTH_TOKEN=your_secret_token_here
   heroku config:set MY_NUMBER=919876543210
   git push heroku main
   ```

### Option 4: DigitalOcean App Platform

DigitalOcean provides reliable hosting with good performance.

#### Steps:
1. **Sign up** at [digitalocean.com](https://digitalocean.com)
2. **Create new App**
3. **Connect your GitHub** repository
4. **Configure:**
   - **Source Directory:** `/`
   - **Build Command:** `pip install -r requirements.txt`
   - **Run Command:** `cd mcp-bearer-token && python quest_rewards_mcp.py`
5. **Set environment variables**
6. **Deploy**

## 🔧 Local Development with ngrok

For testing and development, use ngrok to expose your local server:

### Setup ngrok:
1. **Download ngrok** from [ngrok.com](https://ngrok.com)
2. **Sign up** for free account
3. **Get your authtoken** from dashboard
4. **Configure ngrok:**
   ```bash
   ngrok config add-authtoken YOUR_AUTHTOKEN
   ```

### Run with ngrok:
1. **Start your server:**
   ```bash
   cd mcp-bearer-token
   python quest_rewards_mcp.py
   ```
2. **In another terminal, start ngrok:**
   ```bash
   ngrok http 8086
   ```
3. **Use the ngrok URL** (e.g., `https://abc123.ngrok.io`) with Puch AI

## 🔐 Security Considerations

### Environment Variables
- **Never commit** your `.env` file to version control
- **Use strong, unique tokens** for `AUTH_TOKEN`
- **Rotate tokens** periodically

### HTTPS Requirements
- **Puch AI requires HTTPS** - all cloud platforms provide this
- **ngrok provides HTTPS** automatically
- **Local development** must use ngrok or similar

### Rate Limiting
Consider implementing rate limiting for production:
```python
# Add to your server
from fastapi import HTTPException
import time

# Simple rate limiting
RATE_LIMIT = {}  # user_id -> last_request_time

def check_rate_limit(user_id: str):
    now = time.time()
    if user_id in RATE_LIMIT:
        if now - RATE_LIMIT[user_id] < 1:  # 1 second between requests
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
    RATE_LIMIT[user_id] = now
```

## 📊 Monitoring and Logs

### Add Logging
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add to your tools
logger.info(f"User {puch_user_id} completed quest {quest_id}")
```

### Health Check Endpoint
Add a health check for monitoring:
```python
@mcp.tool
async def health_check() -> str:
    return "Quest server is running! 🎮"
```

## 🐛 Troubleshooting

### Common Issues:

1. **Port Issues:**
   - Ensure port 8086 is available
   - Check firewall settings
   - Use `PORT` environment variable if needed

2. **Import Errors:**
   - Verify all dependencies are installed
   - Check Python version (3.11+)
   - Run `pip install -r requirements.txt`

3. **Authentication Errors:**
   - Verify `AUTH_TOKEN` is set correctly
   - Check token format and length
   - Ensure no extra spaces or characters

4. **Connection Issues:**
   - Verify HTTPS URL is accessible
   - Check ngrok tunnel status
   - Test with curl: `curl https://your-url/mcp`

### Debug Commands:
```bash
# Test server locally
python test_quest_server.py

# Check server logs
tail -f logs/app.log

# Test MCP connection
curl -X POST https://your-url/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
```

## 🎯 Production Checklist

Before going live:
- [ ] **Environment variables** configured
- [ ] **HTTPS enabled** and working
- [ ] **Logging** implemented
- [ ] **Error handling** tested
- [ ] **Rate limiting** considered
- [ ] **Monitoring** set up
- [ ] **Backup strategy** planned
- [ ] **Documentation** updated

## 🚀 Next Steps

After deployment:
1. **Test with Puch AI** using your new URL
2. **Monitor logs** for any issues
3. **Gather user feedback** and iterate
4. **Consider database** for persistent storage
5. **Add more quests** and rewards
6. **Implement analytics** to track usage

---

**Happy Deploying! 🚀**

Your quest server is now ready to help users embark on epic adventures! 🌟
