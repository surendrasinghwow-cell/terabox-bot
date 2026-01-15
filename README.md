# TeraBox Video Downloader Bot

A Telegram bot that extracts direct download links from TeraBox.

## Deploy to Render

### Step 1: Create GitHub Repository
1. Create a new GitHub repo
2. Upload these files:
   - `app.py`
   - `requirements.txt`
   - `Procfile`

### Step 2: Deploy on Render
1. Go to https://render.com
2. Click **New** → **Web Service**
3. Connect your GitHub repo
4. Configure:
   - **Name**: terabox-bot
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

### Step 3: Set Environment Variables (Optional)
- `BOT_TOKEN`: Your Telegram bot token
- `NDUS_COOKIE`: Your TeraBox ndus cookie

### Step 4: Setup Webhook
After deployment, visit:
```
https://your-app.onrender.com/setwebhook
```

### Step 5: Test
Open Telegram and send a TeraBox link to your bot!
