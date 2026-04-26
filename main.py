import os
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
    prompt = "この商品のメルカリ出品情報を日本語で作成してください。\n\n【タイトル】（40文字以内）\n\n【商品説明】\n・ブランド・商品名\n・素材・色・サイズ\n・状態\n・付属品\n\n【検索ワード】（スペース区切りで10個）\n\n【価格】（相場を考えた適正価格）"
    model = genai.GenerativeModel('gemini-1.5-flash')
    result = model.generate_content([{'mime_type': 'image/jpeg', 'data': image_data}, prompt])
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
    app.run(host="0.0.0.0", port=5000)
