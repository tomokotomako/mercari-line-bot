import os
import base64
import google.generativeai as genai
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, ImageMessageContent
import urllib.request

app = Flask(__name__)
configuration = Configuration(access_token=os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    message_id = event.message.id
    headers = {'Authorization': f'Bearer {os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")}'}
    url = f'https://api-data.line.me/v2/bot/message/{message_id}/content'
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        image_data = resp.read()
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    prompt = "この商品のメルカリ出品情報を日本語で作成してください。"
    model = genai.GenerativeModel('gemini-1.5-flash')
    result = model.generate_content([{'mime_type': 'image/jpeg', 'data': image_base64}, prompt])
    reply_text = result.text
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
