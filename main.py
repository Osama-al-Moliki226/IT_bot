# main.py - بوت IT الذكي
import os
import json
import logging
from fastapi import FastAPI, Request, BackgroundTasks
import urllib.request
import urllib.parse

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

SYSTEM_PROMPT = """أنت مساعد ذكي لقسم تكنولوجيا المعلومات (IT). أجب بالعربية الفصحى."""

def send_telegram_message(chat_id: int, text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }).encode()
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        logger.error(f"Telegram error: {e}")

def get_ai_response(user_message: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = json.dumps({
        "contents": [
            {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
            {"role": "model", "parts": [{"text": "فهمت. سأساعد طلاب قسم IT."}]},
            {"role": "user", "parts": [{"text": user_message}]}
        ],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1000}
    }).encode()
    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        response = urllib.request.urlopen(req, timeout=30)
        result = json.loads(response.read().decode())
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        logger.error(f"AI error: {e}")
        return "عذراً، المساعد الذكي غير متوفر حالياً."

@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    if not chat_id or not text:
        return {"status": "ignored"}
    background_tasks.add_task(process_message, chat_id, text)
    return {"status": "processing"}

def process_message(chat_id: int, text: str):
    if text == "/start":
        welcome = "🎓 مرحباً بك في بوت قسم IT!\n\nاكتب سؤالك وسأجيب عليه بالذكاء الاصطناعي."
        send_telegram_message(chat_id, welcome)
        return
    ai_response = get_ai_response(text)
    send_telegram_message(chat_id, ai_response)

@app.get("/")
async def root():
    return {"status": "running", "bot": "IT_3_bot AI"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
