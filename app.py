# TeraBox Video Downloader Telegram Bot
# Using ytshorts.savetube.me API (from working r0ld3x bot)

from flask import Flask, request, jsonify
import requests
import json
import re
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


def find_between(data, first, last):
    try:
        start = data.index(first) + len(first)
        end = data.index(last, start)
        return data[start:end]
    except ValueError:
        return None


def format_size(size_bytes):
    if not size_bytes:
        return None
    if isinstance(size_bytes, str):
        return size_bytes
    size_bytes = int(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def extract_terabox(url):
    """Extract using ytshorts.savetube.me API (from working bot)."""
    
    debug = {'url': url, 'steps': []}
    
    try:
        # Normalize URL domain to 1024terabox.com
        netloc = urlparse(url).netloc
        normalized_url = url.replace(netloc, "1024terabox.com")
        
        # Step 1: Get thumbnail from page
        default_thumbnail = None
        try:
            page_resp = requests.get(url, timeout=15)
            if page_resp.status_code == 200:
                default_thumbnail = find_between(page_resp.text, 'og:image" content="', '"')
        except:
            pass
        
        debug['steps'].append({'step': 'page', 'thumbnail': bool(default_thumbnail)})
        
        # Step 2: Use ytshorts.savetube.me API
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/json",
            "Origin": "https://ytshorts.savetube.me",
            "Alt-Used": "ytshorts.savetube.me",
            "Referer": "https://ytshorts.savetube.me/",
        }
        
        api_response = requests.post(
            "https://ytshorts.savetube.me/api/v1/terabox-downloader",
            headers=headers,
            json={"url": normalized_url},
            timeout=30
        )
        
        step2 = {'step': 'api', 'status': api_response.status_code}
        
        if api_response.status_code != 200:
            step2['error'] = f'API status: {api_response.status_code}'
            debug['steps'].append(step2)
            return {'success': False, 'error': f'API error: {api_response.status_code}', 'debug': debug}
        
        data = api_response.json()
        step2['response_keys'] = list(data.keys())
        responses = data.get("response", [])
        
        if not responses:
            step2['error'] = 'No response data'
            debug['steps'].append(step2)
            return {'success': False, 'error': 'No data from API', 'debug': debug}
        
        resolutions = responses[0].get("resolutions", {})
        step2['resolutions'] = list(resolutions.keys()) if resolutions else []
        debug['steps'].append(step2)
        
        if not resolutions:
            return {'success': False, 'error': 'No resolutions found', 'debug': debug}
        
        # Get links
        fast_download = resolutions.get("Fast Download", "")
        hd_video = resolutions.get("HD Video", "")
        
        if not (hd_video or fast_download):
            return {'success': False, 'error': 'No download links found', 'debug': debug}
        
        # Get file info from video link
        file_name = None
        content_length = None
        
        try:
            head_resp = requests.head(hd_video or fast_download, timeout=10)
            content_length = head_resp.headers.get("Content-Length")
            
            content_disposition = head_resp.headers.get("content-disposition", "")
            if content_disposition:
                fname_match = re.findall('filename="(.+)"', content_disposition)
                if fname_match:
                    file_name = fname_match[0]
        except:
            pass
        
        # Get direct link
        direct_link = None
        if fast_download:
            try:
                redirect_resp = requests.head(fast_download, timeout=10, allow_redirects=False)
                direct_link = redirect_resp.headers.get("location", fast_download)
            except:
                direct_link = fast_download
        
        return {
            'success': True,
            'file_name': file_name or 'TeraBox Video',
            'download_link': hd_video,
            'fast_download': direct_link or fast_download,
            'thumbnail': default_thumbnail,
            'size': format_size(int(content_length)) if content_length else None,
            'size_bytes': int(content_length) if content_length else None,
            'debug': debug
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e), 'debug': debug}


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
            send_message(chat_id, "🎬 *TeraBox Video Downloader!*\n\nSend me any TeraBox link!")
            return 'ok'
        
        urls = re.findall(r'https?://[^\s]+', text)
        terabox_urls = [u for u in urls if is_terabox_url(u)]
        
        if not terabox_urls:
            send_message(chat_id, "❌ Please send a valid TeraBox link.")
            return 'ok'
        
        for url in terabox_urls:
            send_message(chat_id, "⏳ Processing...")
            result = extract_terabox(url)
            
            if result['success']:
                size_text = f"\n📊 Size: {result.get('size')}" if result.get('size') else ""
                msg = f"✅ *Video Found!*\n\n📁 `{result.get('file_name', 'Video')}`{size_text}\n\n👇 Download:"
                
                buttons = []
                if result.get('fast_download'):
                    buttons.append([{"text": "⚡ Fast Download", "url": result['fast_download']}])
                if result.get('download_link'):
                    buttons.append([{"text": "🎬 HD Video", "url": result['download_link']}])
                
                markup = {"inline_keyboard": buttons}
                
                if result.get('thumbnail'):
                    send_photo(chat_id, result['thumbnail'], msg, markup)
                else:
                    send_message(chat_id, msg, markup)
            else:
                send_message(chat_id, f"❌ Failed: {result.get('error')}")
        
        return 'ok'
    except:
        return 'ok'


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
