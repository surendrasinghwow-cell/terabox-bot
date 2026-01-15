# TeraBox Video Downloader Telegram Bot
# Using PlayTerabox API for extraction

from flask import Flask, request, jsonify
import requests
import json
import re
from urllib.parse import urlparse, parse_qs
import os

app = Flask(__name__)

# Bot Token
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8481194301:AAHPoP38OxzK1mXpXjnNzmK8J_6DflgVurs")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Webhook URL
WEBHOOK_BASE = os.environ.get("RENDER_EXTERNAL_URL", "https://terabox-bot-ynxr.onrender.com")

TERABOX_DOMAINS = ['terabox.com', 'teraboxapp.com', '1024terabox.com', '1024tera.com', '4funbox.com', 'mirrobox.com']


def send_message(chat_id, text, reply_markup=None):
    url = f"{TELEGRAM_API}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    requests.post(url, data=data)


def send_photo(chat_id, photo_url, caption, reply_markup=None):
    url = f"{TELEGRAM_API}/sendPhoto"
    data = {"chat_id": chat_id, "photo": photo_url, "caption": caption, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(url, data=data, timeout=10)
    except:
        send_message(chat_id, caption, reply_markup)


def is_terabox_url(url):
    try:
        domain = urlparse(url).netloc.lower().replace('www.', '')
        return any(d in domain for d in TERABOX_DOMAINS)
    except:
        return False


def get_surl(url):
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if 'surl' in params:
            return params['surl'][0]
        if '/s/' in url:
            return url.split('/s/')[-1].split('/')[0].split('?')[0]
        return None
    except:
        return None


def format_size(size_bytes):
    if not size_bytes:
        return None
    size_bytes = int(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def try_playterabox_api(url):
    """Try using playterabox.com API."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Origin': 'https://playterabox.com',
            'Referer': 'https://playterabox.com/',
        }
        
        # Try their API endpoint
        api_url = "https://playterabox.com/api/fetch"
        resp = requests.post(api_url, json={"url": url}, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success') or data.get('download_url') or data.get('link'):
                return {
                    'success': True,
                    'download_link': data.get('download_url') or data.get('link') or data.get('url'),
                    'file_name': data.get('filename') or data.get('name') or 'Video',
                    'size': data.get('size'),
                    'thumbnail': data.get('thumbnail') or data.get('thumb'),
                    'source': 'playterabox'
                }
    except Exception as e:
        pass
    return None


def try_terabox_player_api(url):
    """Try terabox player API."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
        }
        
        api_url = f"https://teraboxplayer.com/api/download?url={url}"
        resp = requests.get(api_url, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success') and data.get('data'):
                file_data = data['data']
                return {
                    'success': True,
                    'download_link': file_data.get('download_url') or file_data.get('link'),
                    'file_name': file_data.get('filename') or file_data.get('name') or 'Video',
                    'size': file_data.get('size'),
                    'thumbnail': file_data.get('thumbnail'),
                    'source': 'teraboxplayer'
                }
    except:
        pass
    return None


def try_terabox_dl_api(url):
    """Try terabox-dl API."""
    try:
        surl = get_surl(url)
        if not surl:
            return None
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        api_url = f"https://terabox-dl.vercel.app/api?url={url}"
        resp = requests.get(api_url, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('ok') or data.get('success'):
                return {
                    'success': True,
                    'download_link': data.get('download_link') or data.get('dlink') or data.get('url'),
                    'file_name': data.get('filename') or data.get('name') or 'Video',
                    'size': data.get('size'),
                    'thumbnail': data.get('thumb'),
                    'source': 'terabox-dl'
                }
    except:
        pass
    return None


def try_savefrom_api(url):
    """Try savefrom-style API."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        api_url = "https://getvideo.wiki/api/terabox"
        resp = requests.post(api_url, data={"url": url}, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success') or data.get('download'):
                return {
                    'success': True,
                    'download_link': data.get('download') or data.get('link'),
                    'file_name': data.get('title') or data.get('filename') or 'Video',
                    'thumbnail': data.get('thumbnail'),
                    'source': 'getvideo'
                }
    except:
        pass
    return None


def extract_terabox(url):
    """Try all extraction methods."""
    
    apis = [
        try_playterabox_api,
        try_terabox_player_api,
        try_terabox_dl_api,
        try_savefrom_api,
    ]
    
    for api_func in apis:
        try:
            result = api_func(url)
            if result and result.get('success') and result.get('download_link'):
                return result
        except:
            continue
    
    return {
        'success': False,
        'error': 'Could not extract download link. Try again later or check if the link is valid.',
    }


@app.route('/')
def home():
    return '''
    <html>
    <head><title>TeraBox Bot</title></head>
    <body style="font-family:Arial;padding:50px;text-align:center;background:#1a1a2e;color:white;">
        <h1>🎬 TeraBox Video Downloader</h1>
        <p style="color:#00ff88;font-size:24px;">✅ Bot is running!</p>
        <p><a href="/setwebhook" style="color:#00d4ff;">Setup Webhook</a></p>
        <p><a href="https://t.me/teraboxxdonbot" style="color:#00d4ff;font-size:20px;">Open Bot on Telegram</a></p>
    </body>
    </html>
    '''


@app.route('/setwebhook')
def set_webhook():
    webhook_url = f"{WEBHOOK_BASE}/webhook"
    url = f"{TELEGRAM_API}/setWebhook?url={webhook_url}"
    result = requests.get(url).json()
    
    if result.get('ok'):
        return f'''
        <html>
        <body style="font-family:Arial;padding:50px;text-align:center;background:#1a1a2e;color:white;">
            <h1 style="color:#00ff88;">✅ Webhook Set!</h1>
            <p>URL: {webhook_url}</p>
            <p><a href="https://t.me/teraboxxdonbot" style="color:#00d4ff;">Test the Bot</a></p>
        </body>
        </html>
        '''
    return f'<h1 style="color:red;">❌ Error: {result}</h1>'


@app.route('/test')
def test():
    url = request.args.get('url', '')
    if not url:
        return jsonify({'error': 'Add ?url=TERABOX_URL'})
    return jsonify(extract_terabox(url))


@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        if 'message' not in data:
            return 'ok'
        
        chat_id = data['message']['chat']['id']
        text = data['message'].get('text', '')
        
        if text == '/start':
            send_message(chat_id, """
🎬 *Welcome to TeraBox Video Downloader!*

Send me any TeraBox link and I'll get the download URL!

*Supported:*
• terabox.com
• 1024terabox.com
• 1024tera.com

Just paste your link! 🚀
            """)
            return 'ok'
        
        if text == '/help':
            send_message(chat_id, """
📖 *Help*

Just send a TeraBox link!

*Example:*
`https://1024tera.com/wap/share/filelist?surl=xxxxx`
            """)
            return 'ok'
        
        urls = re.findall(r'https?://[^\s]+', text)
        terabox_urls = [u for u in urls if is_terabox_url(u)]
        
        if not terabox_urls:
            send_message(chat_id, "❌ Please send a valid TeraBox link.")
            return 'ok'
        
        for url in terabox_urls:
            send_message(chat_id, "⏳ Processing your link...")
            result = extract_terabox(url)
            
            if result['success']:
                size_text = f"\n📊 Size: {format_size(result.get('size'))}" if result.get('size') else ""
                msg = f"✅ *Video Found!*\n\n📁 `{result.get('file_name', 'Video')}`{size_text}\n\n👇 Click to download:"
                markup = {"inline_keyboard": [[{"text": "📥 Download Video", "url": result['download_link']}]]}
                
                if result.get('thumbnail'):
                    send_photo(chat_id, result['thumbnail'], msg, markup)
                else:
                    send_message(chat_id, msg, markup)
            else:
                send_message(chat_id, f"❌ *Failed*\n\n{result.get('error')}")
        
        return 'ok'
    except Exception as e:
        return 'ok'


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
