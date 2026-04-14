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
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        message_id = event.message.id
        headers = {'Authorization': f'Bearer {os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")}'}
        url = f'https://api-data.line.me/v2/bot/message/{message_id}/content'
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            image_data = response.read()

    model = genai.GenerativeModel('gemini-1.5-flash')
    import PIL.Image
    import io
    image = PIL.Image.open(io.BytesIO(image_data))

    prompt = """
この商品のメルカリ出品情報を日本語で作成してください。

【タイトル】（40文字以内）

【商品説明】
・ブランド・商品名
・素材・色・サイズ
・状態
・付属品

【検索ワード】（スペース区切りで10個）

【価格】（相場を考えた適正価格）
"""

    response = model.generate_content([prompt, image])

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingAp
