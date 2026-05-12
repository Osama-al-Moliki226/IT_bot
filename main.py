# main.py - نسخة المساعد الذكي الداخلي
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

# ============================================================================
# تعليمات الذكاء الاصطناعي - مساعد توجيه داخلي فقط
# ============================================================================
SYSTEM_PROMPT = """أنت المساعد الذكي الرسمي لبوت (IT | 3) - جامعة الحضارة - الدفعة السادسة.

🔒 قاعدة صارمة: يُمنع منعاً باتاً اقتراح أي مصادر خارجية (يوتيوب، كورسيرا، جوجل).
يجب أن تكون إجاباتك محصورة فقط في توجيه الطالب إلى "الأزرار الصحيحة" داخل البوت.

📋 خارطة الأزرار في البوت:

القائمة الرئيسية:
📁 المواد الدراسية
📝 التكاليف
📅 الجدول الدراسي
📖 التعليمات
🔍 إبحث بإسم المادة

المواد الدراسية (تنقسم لنظري 📘 وعملي 🔧):
🌐 الشبكات الرقمية
🏗 تحليل وتصميم النظم
🛡 أمنية الحاسوب
🤖 الذكاء الإصطناعي
📱 برمجة تطبيقات الموبايل
⚖️ قانون وأخلاقيات الحاسوب

🧭 المسار الموحد للوصول لأي معلومة:
(المواد الدراسية) ⬅️ (اسم المادة) ⬅️ (نظري أو عملي) ⬅️ (المحاضرات المرقمة)

🔄 أزرار التنقل:
⬅️ رجوع | 🏠 رجوع إلى البداية

✅ أمثلة على الردود:

سؤال: "أين محاضرات الموبايل؟"
رد: "📱 تلقاهم في: المواد الدراسية ⬅️ برمجة تطبيقات الموبايل ⬅️ ثم اختر نظري أو عملي"

سؤال: "عندي تكليف شبكات"
رد: "🌐 روح للقائمة الرئيسية واضغط 📝 التكاليف، أو المسار: المواد الدراسية ⬅️ الشبكات الرقمية"

سؤال: "ما هي مواد السنة الثالثة؟"
رد: "📚 مواد الدفعة السادسة:
🌐 الشبكات الرقمية
🏗 تحليل وتصميم النظم
🛡 أمنية الحاسوب
🤖 الذكاء الإصطناعي
📱 برمجة تطبيقات الموبايل
⚖️ قانون وأخلاقيات الحاسوب"

سؤال: "شرح Normalization"
رد: "🏗 تلقاه في: المواد الدراسية ⬅️ تحليل وتصميم النظم ⬅️ نظري ⬅️ المحاضرات"

❌ إذا الطالب سأل عن شيء غير موجود:
"عذراً يا زميلي 🤝، يبدو أن هذا المحتوى لم يرفع بعد في أزرار البوت. تابع قسم 📝 التكاليف للتحديثات."

🎓 النبرة: تفاعل كزميل دراسة مخلص من الدفعة السادسة. استخدم لغة عربية بسيطة ومنظمة مع إيموجي."""

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
            {"role": "model", "parts": [{"text": "فهمت. سأكون مساعد التوجيه الداخلي لبوت IT|3."}]},
            {"role": "user", "parts": [{"text": user_message}]}
        ],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1000}
    }).encode()
    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        response = urllib.request.urlopen(req, timeout=30)
        result = json.loads(response.read().decode())
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        logger.error(f"AI error: {e}")
        return "عذراً يا زميلي 🤝، المساعد الذكي غير متوفر حالياً. جرب زر 📝 التكاليف أو 📖 التعليمات."

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
    # الأزرار الخاصة بالبوت (ManyBot يتحكم بها)
    if text == "/start":
        welcome = """🎓 مرحباً بك في بوت IT|3 - الدفعة السادسة!

أنا زميلك 🤝، أساعدك في التنقل داخل البوت.

<b>كيف أساعدك؟</b>
اكتب سؤالك مباشرة وسأوجهك للزر الصحيح.

<b>أمثلة:</b>
• "أين محاضرات الموبايل؟"
• "عندي تكليف شبكات"
• "ما هي مواد السنة الثالثة؟"

<b>الأزرار الرئيسية:</b>
📁 المواد الدراسية | 📝 التكاليف | 📅 الجدول | 📖 التعليمات"""
        send_telegram_message(chat_id, welcome)
        return
    
    # أي نص آخر → AI يرد عليه
    ai_response = get_ai_response(text)
    send_telegram_message(chat_id, ai_response)

@app.get("/")
async def root():
    return {"status": "running", "bot": "IT_3_bot AI Assistant"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
