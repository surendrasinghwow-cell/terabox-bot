# TeraBox Video Downloader - Using terabox-dl.qtcloud.workers.dev
# Based on Abdul97233/TeraBox-Downloader-Bot approach

from flask import Flask, request, jsonify
import requests
import json
import re
import time
from urllib.parse import urlparse, parse_qs
import os

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8481194301:AAHPoP38OxzK1mXpXjnNzmK8J_6DflgVurs")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
WEBHOOK_BASE = os.environ.get("RENDER_EXTERNAL_URL", "https://terabox-bot-ynxr.onrender.com")

TERABOX_DOMAINS = ['terabox.com', 'teraboxapp.com', '1024terabox.com', '1024tera.com', '4funbox.com', 'mirrobox.com', 'nephobox.com', 'freeterabox.com', 'momerybox.com', 'tibibox.com']


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
    patterns = [
        r"ww\.mirrobox\.com", r"www\.nephobox\.com", r"freeterabox\.com",
        r"www\.freeterabox\.com", r"1024tera\.com", r"4funbox\.co",
        r"www\.4funbox\.com", r"mirrobox\.com", r"nephobox\.com",
        r"terabox\.app", r"terabox\.com", r"www\.terabox\.ap",
        r"www\.terabox\.com", r"www\.1024tera\.co", r"www\.momerybox\.com",
        r"teraboxapp\.com", r"momerybox\.com", r"tibibox\.com",
        r"www\.tibibox\.com", r"www\.teraboxapp\.com",
    ]
    for pattern in patterns:
        if re.search(pattern, url):
            return True
    return False


def get_formatted_size(size_bytes):
    if not size_bytes:
        return None
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def retry_request(method, url, attempts=3, delay=2, **kwargs):
    """Retry wrapper for requests."""
    for i in range(1, attempts + 1):
        try:
            resp = requests.request(method, url, timeout=25, **kwargs)
            if resp.status_code in (200, 302):
                return resp
        except Exception as e:
            print(f"[Retry {i}] Error: {e}")
        time.sleep(delay)
    return None


def try_api_1(url):
    """Try terabox-dl.qtcloud.workers.dev API."""
    try:
        api_url = f"https://terabox-dl.qtcloud.workers.dev/api?url={url}"
        resp = retry_request("GET", api_url, attempts=2, delay=1)
        
        if resp and resp.status_code == 200:
            data = resp.json()
            if data.get('ok') or data.get('success') or data.get('downloadLink'):
                return {
                    'success': True,
                    'download_link': data.get('downloadLink') or data.get('link') or data.get('download_link'),
                    'file_name': data.get('file_name') or data.get('filename') or 'Video',
                    'size': data.get('size'),
                    'thumb': data.get('thumb'),
                    'source': 'qtcloud'
                }
    except:
        pass
    return None


def try_api_2(url):
    """Try teraboxvideodownloader.online API."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        resp = retry_request("POST", "https://teraboxvideodownloader.online/api.php", 
                           data={"url": url}, headers=headers, attempts=2, delay=1)
        
        if resp and resp.status_code == 200:
            data = resp.json()
            if data.get('downloadLink') or data.get('link'):
                return {
                    'success': True,
                    'download_link': data.get('downloadLink') or data.get('link'),
                    'file_name': data.get('filename') or 'Video',
                    'size': data.get('size'),
                    'thumb': data.get('thumb'),
                    'source': 'teraboxvideodownloader'
                }
    except:
        pass
    return None


def try_api_3(url):
    """Try teraboxdownloaderbot API."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json',
        }
        
        resp = retry_request("GET", f"https://teraboxdownloaderbot.vercel.app/api?url={url}",
                           headers=headers, attempts=2, delay=1)
        
        if resp and resp.status_code == 200:
            data = resp.json()
            if data.get('download_link') or data.get('direct_link'):
                return {
                    'success': True,
                    'download_link': data.get('download_link') or data.get('direct_link'),
                    'file_name': data.get('file_name') or data.get('filename') or 'Video',
                    'size': data.get('size'),
                    'thumb': data.get('thumb'),
                    'source': 'vercel'
                }
    except:
        pass
    return None


def try_api_4(url):
    """Try tera-box.vercel API."""
    try:
        resp = retry_request("GET", f"https://tera-box.vercel.app/api?url={url}", attempts=2, delay=1)
        
        if resp and resp.status_code == 200:
            data = resp.json()
            if data.get('direct_link') or data.get('downloadLink'):
                return {
                    'success': True,
                    'download_link': data.get('direct_link') or data.get('downloadLink'),
                    'file_name': data.get('file_name') or 'Video',
                    'size': data.get('size'),
                    'thumb': data.get('thumb'),
                    'source': 'tera-box-vercel'
                }
    except:
        pass
    return None


def extract_terabox(url):
    """Try multiple APIs."""
    
    apis = [try_api_1, try_api_2, try_api_3, try_api_4]
    debug = {'url': url, 'tried': []}
    
    for api_func in apis:
        try:
            result = api_func(url)
            if result and result.get('success') and result.get('download_link'):
                result['debug'] = debug
                return result
            debug['tried'].append({'api': api_func.__name__, 'result': 'failed'})
        except Exception as e:
            debug['tried'].append({'api': api_func.__name__, 'error': str(e)})
    
    return {
        'success': False,
        'error': 'All APIs failed. Please try again later.',
        'debug': debug
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
        <p><a href="https://t.me/teraboxxdonbot" style="color:#00d4ff;font-size:20px;">Open Bot</a></p>
    </body>
    </html>
    '''


@app.route('/setwebhook')
def set_webhook():
    webhook_url = f"{WEBHOOK_BASE}/webhook"
    result = requests.get(f"{TELEGRAM_API}/setWebhook?url={webhook_url}").json()
    status = "✅ Set!" if result.get('ok') else f"❌ Error: {result}"
    return f'<h1>{status}</h1><p>URL: {webhook_url}</p>'


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
            send_message(chat_id, "🎬 *TeraBox Video Downloader!*\n\nSend any TeraBox link!")
            return 'ok'
        
        urls = re.findall(r'https?://[^\s]+', text)
        terabox_urls = [u for u in urls if is_terabox_url(u)]
        
        if not terabox_urls:
            send_message(chat_id, "❌ Send a valid TeraBox link.")
            return 'ok'
        
        for url in terabox_urls:
            send_message(chat_id, "⏳ Processing...")
            result = extract_terabox(url)
            
            if result['success']:
                size_text = f"\n📊 Size: {result.get('size')}" if result.get('size') else ""
                msg = f"✅ *Video Found!*\n\n📁 `{result.get('file_name', 'Video')}`{size_text}"
                markup = {"inline_keyboard": [[{"text": "📥 Download", "url": result['download_link']}]]}
                
                if result.get('thumb'):
                    send_photo(chat_id, result['thumb'], msg, markup)
                else:
                    send_message(chat_id, msg, markup)
            else:
                send_message(chat_id, f"❌ {result.get('error')}")
        
        return 'ok'
    except:
        return 'ok'


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
