from flask import Flask, request
import threading
import os

app = Flask(__name__)

@app.route('/')
def index():
    return "✅ Bot ishlayapti!"

@app.route('/webhook', methods=['POST'])
def webhook():
    from main import dp, bot
    if request.headers.get('content-type') == 'application/json':
        update = request.get_json()
        dp.feed_update(bot, update)
        return {"status": "ok"}
    else:
        return {"status": "invalid content type"}, 403

def run():
    port = int(os.environ.get("PORT", 5000))  # Render port beradi
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()
