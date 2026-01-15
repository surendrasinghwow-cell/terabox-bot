# TeraBox Video Downloader Telegram Bot
# Render.com Deployment

from flask import Flask, request, jsonify
import requests
import json
import re
from urllib.parse import urlparse, parse_qs
import os

app = Flask(__name__)

# Bot Token - can also use environment variable
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8481194301:AAHPoP38OxzK1mXpXjnNzmK8J_6DflgVurs")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# TeraBox Cookie - can also use environment variable
NDUS_COOKIE = os.environ.get("NDUS_COOKIE", "YvAFiL8peHuihk_jSkmddTzXJ1GZalDIQV64qeuX")
COOKIE_STRING = f"ndus={NDUS_COOKIE}; lang=en"

# Webhook URL - UPDATE THIS after Render deployment
WEBHOOK_BASE = os.environ.get("RENDER_EXTERNAL_URL", "https://your-app.onrender.com")

TERABOX_DOMAINS = ['terabox.com', 'teraboxapp.com', '1024terabox.com', '1024tera.com', '4funbox.com']


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


def extract_terabox(url):
    """Extract download link from TeraBox."""
    
    surl = get_surl(url)
    if not surl:
        return {'success': False, 'error': 'Invalid URL'}
    
    session = requests.Session()
    
    domains = ['dm.1024terabox.com', 'www.1024terabox.com', 'www.terabox.com', 'www.1024tera.com']
    
    for domain in domains:
        try:
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cookie': COOKIE_STRING,
                'Host': domain,
                'Origin': f'https://{domain}',
                'Referer': f'https://{domain}/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
            
            api_url = f"https://{domain}/api/shorturlinfo?shorturl={surl}&root=1"
            resp = session.get(api_url, headers=headers, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                
                if data.get('errno') == 0 and data.get('list'):
                    file_info = data['list'][0]
                    dlink = file_info.get('dlink')
                    
                    if dlink:
                        return {
                            'success': True,
                            'download_link': dlink,
                            'file_name': file_info.get('server_filename', 'Video'),
                            'size': file_info.get('size'),
                            'thumbnail': file_info.get('thumbs', {}).get('url3') if isinstance(file_info.get('thumbs'), dict) else None
                        }
                        
        except Exception as e:
            continue
    
    return {'success': False, 'error': 'Could not extract download link'}


@app.route('/')
def home():
    return '''
    <html>
    <head><title>TeraBox Bot</title></head>
    <body style="font-family:Arial;padding:50px;text-align:center;background:#1a1a2e;color:white;">
        <h1>🎬 TeraBox Video Downloader</h1>
        <p style="color:#00ff88;font-size:24px;">✅ Bot is running on Render!</p>
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
