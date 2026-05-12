# main.py - بوت IT|3 المساعد الذكي المتطور جداً v5.0 (دعم الأزرار والملفات)
import os
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, BackgroundTasks
import urllib.request
import urllib.parse

# ============================================================================
# الإعدادات
# ============================================================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ============================================================================
# ذاكرة البوت المتقدمة (جلسات، تفضيلات، إحصائيات)
# ============================================================================
MAX_HISTORY = 5
conversation_history = defaultdict(list)
user_preferences = defaultdict(lambda: defaultdict(int))
global_stats = defaultdict(int)

# ============================================================================
# بيانات التكاليف القادمة (قابلة للتعديل)
# ============================================================================
DEADLINES = [
    {"subject": "الشبكات الرقمية", "task": "تقرير نظري حول TCP/IP", "deadline": "2026-05-18"},
    {"subject": "تحليل وتصميم النظم", "task": "تسليم مشروع ERD + Normalization", "deadline": "2026-05-20"},
    {"subject": "أمنية الحاسوب", "task": "تسليم تقرير العملي عن Firewall", "deadline": "2026-05-22"},
    {"subject": "الذكاء الإصطناعي", "task": "تطبيق عملي Machine Learning", "deadline": "2026-05-25"},
    {"subject": "برمجة تطبيقات الموبايل", "task": "مشروع Flutter النهائي", "deadline": "2026-05-23"},
    {"subject": "قانون وأخلاقيات الحاسوب", "task": "دراسة حالة قانونية", "deadline": "2026-05-19"},
]

# ============================================================================
# قاعدة المعرفة المتقدمة - خارطة البوت الكاملة + تعليمات ذكية
# ============================================================================
KNOWLEDGE_BASE = """
🎓 أنت المساعد الذكي الرسمي لبوت (IT | 3) - جامعة الحضارة - الدفعة السادسة.

🔒 قواعد صارمة:
• يُمنع منعاً باتاً اقتراح أي مصادر خارجية (يوتيوب، كورسيرا، جوجل، ويكيبيديا)
• إجاباتك محصورة فقط في توجيه الطالب إلى أزرار البوت أو المعلومات المرفوعة
• إذا لم تجد المعلومة: قل "لم يرفع بعد، تابع قسم التكاليف"

📋 خارطة البوت الكاملة:

🏠 القائمة الرئيسية:
├─ 📁 المواد الدراسية
├─ 📝 التكاليف  
├─ 📅 الجدول الدراسي
├─ 📖 التعليمات
├─ 🔍 إبحث بإسم المادة
└─ ⬅️ رجوع | 🏠 رجوع إلى البداية

📁 المواد الدراسية (6 مواد):
├─ 🌐 الشبكات الرقمية (Digital Networks)
│   ├─ 📘 نظري: محاضرات 1-12
│   └─ 🔧 عملي: تمارين عملية + مشاريع
│
├─ 🏗 تحليل وتصميم النظم (System Analysis)
│   ├─ 📘 نظري: UML, ERD, Normalization, DFD
│   └─ 🔧 عملي: مشروع النظام
│
├─ 🛡 أمنية الحاسوب (Computer Security)
│   ├─ 📘 نظري: تشفير، Firewall، Ethical Hacking
│   └─ 🔧 عملي: labs + CTF challenges
│
├─ 🤖 الذكاء الإصطناعي (AI)
│   ├─ 📘 نظري: Machine Learning, Neural Networks, NLP
│   └─ 🔧 عملي: Python + TensorFlow + Projects
│
├─ 📱 برمجة تطبيقات الموبايل (Mobile Dev)
│   ├─ 📘 نظري: Flutter, React Native, UI/UX
│   └─ 🔧 عملي: تطبيقات عملية
│
└─ ⚖️ قانون وأخلاقيات الحاسوب (Cyber Law)
    ├─ 📘 نظري: قوانين إلكترونية، حقوق الملكية
    └─ 🔧 عملي: دراسات حالة

📝 التكاليف:
├─ تكاليف نظري
├─ تكاليف عملي
├─ مشاريع الفصل
└─ مواعيد التسليم

📅 الجدول الدراسي:
├─ أيام المحاضرات
├─ أوقات المحاضرات
├─ أسماء الدكاترة
└─ القاعات

📖 التعليمات:
├─ كيفية استخدام البوت
├─ تنزيل الملفات
├─ البحث عن المادة
└─ التواصل مع المشرف

🔍 البحث:
└─ كتابة اسم المادة للوصول السريع
"""

# ============================================================================
# قاموس الكلمات المفتاحية للتوجيه السريع
# ============================================================================
KEYWORD_MAP = {
    "شبكات": "🌐 الشبكات الرقمية",
    "network": "🌐 الشبكات الرقمية",
    "networks": "🌐 الشبكات الرقمية",
    "رقمية": "🌐 الشبكات الرقمية",
    # ... (باقي المفاتيح كما في الإصدار السابق مع إضافة اختصارات للملفات والمحاضرات)
    "محاضرة": "📁 المواد الدراسية",
    "ملف": "📁 المواد الدراسية",
    "تكليف": "📝 التكاليف",
    "واجب": "📝 التكاليف",
    "جدول": "📅 الجدول الدراسي",
    "موعد": "📅 الجدول الدراسي",
    "تعليم": "📖 التعليمات",
    "مساعدة": "📖 التعليمات",
    "help": "📖 التعليمات",
    "كيف": "📖 التعليمات",
    "بحث": "🔍 إبحث بإسم المادة",
    "search": "🔍 إبحث بإسم المادة",
    "قائمة": "🏠 القائمة الرئيسية",
    "الرئيسية": "🏠 القائمة الرئيسية",
    "home": "🏠 القائمة الرئيسية",
    "بداية": "🏠 القائمة الرئيسية",
    "رجوع": "⬅️ رجوع",
    "back": "⬅️ رجوع",
    "رجوع إلى البداية": "🏠 رجوع إلى البداية",
    "المواد الدراسية": "📁 المواد الدراسية",
    "التكاليف": "📝 التكاليف",
    "الجدول الدراسي": "📅 الجدول الدراسي",
    "التعليمات": "📖 التعليمات",
    "إبحث بإسم المادة": "🔍 إبحث بإسم المادة",
    "نظري": "📘 نظري",
    "عملي": "🔧 عملي",
    "محاضرات": "📁 المواد الدراسية",
    "مشاريع": "📝 التكاليف",
}

# ============================================================================
# أسماء الأزرار التفاعلية الكاملة (التي يضغطها المستخدم فعلاً)
# ============================================================================
BUTTON_NAMES = {
    "🏠 القائمة الرئيسية": "main_menu",
    "📁 المواد الدراسية": "subjects_menu",
    "📝 التكاليف": "assignments_menu",
    "📅 الجدول الدراسي": "schedule_menu",
    "📖 التعليمات": "instructions_menu",
    "🔍 إبحث بإسم المادة": "search_prompt",
    "⬅️ رجوع": "back",
    "🏠 رجوع إلى البداية": "go_home",
    "🌐 الشبكات الرقمية": "subject_networks",
    "🏗 تحليل وتصميم النظم": "subject_sa",
    "🛡 أمنية الحاسوب": "subject_security",
    "🤖 الذكاء الإصطناعي": "subject_ai",
    "📱 برمجة تطبيقات الموبايل": "subject_mobile",
    "⚖️ قانون وأخلاقيات الحاسوب": "subject_law",
    "📘 نظري": "theoretical",
    "🔧 عملي": "practical",
}

# ============================================================================
# دوال إدارة السياق والتفضيلات والإحصائيات (نفس السابق)
# ============================================================================
def update_conversation_history(user_id, role, content):
    conversation_history[user_id].append({"role": role, "text": content})
    if len(conversation_history[user_id]) > MAX_HISTORY * 2:
        conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY * 2:]

def get_user_context_string(user_id):
    history = conversation_history.get(user_id, [])
    if not history:
        return ""
    context = "🗨️ سياق المحادثة السابق مع الطالب:\n"
    for msg in history[-6:]:
        prefix = "👤 الطالب" if msg["role"] == "user" else "🤖 البوت"
        context += f"{prefix}: {msg['text']}\n"
    return context

def update_user_preferences(user_id, text):
    text_lower = text.lower()
    for keyword, subject in KEYWORD_MAP.items():
        if keyword in text_lower:
            user_preferences[user_id][subject] += 1

def update_global_stats(text):
    text_lower = text.lower()
    for keyword in KEYWORD_MAP:
        if keyword in text_lower:
            global_stats[keyword] += 1

def get_preferences_summary(user_id):
    prefs = user_preferences.get(user_id, {})
    if not prefs:
        return "لم تتفاعل مع مواد محددة بعد."
    sorted_prefs = sorted(prefs.items(), key=lambda x: x[1], reverse=True)
    summary = "📊 أكثر المواد التي سألت عنها:\n"
    for subject, count in sorted_prefs[:3]:
        summary += f"• {subject} ({count} مرات)\n"
    return summary

def get_upcoming_deadlines():
    today = datetime.now().date()
    upcoming = []
    for item in DEADLINES:
        deadline = datetime.strptime(item["deadline"], "%Y-%m-%d").date()
        if deadline >= today:
            days_left = (deadline - today).days
            upcoming.append(f"📌 {item['subject']} - {item['task']} (خلال {days_left} يوم)")
    if not upcoming:
        return "🎉 لا توجد تكاليف قادمة حالياً، أنت في أمان!"
    return "🔔 **التكاليف القادمة:**\n" + "\n".join(upcoming)

# ============================================================================
# دالة إرسال رسالة Telegram
# ============================================================================
def send_telegram_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    data = urllib.parse.urlencode(payload).encode()
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        logger.error(f"Telegram error: {e}")

# ============================================================================
# دالة Gemini AI مع سياق المستخدم (تستخدم فقط للأسئلة الحرة)
# ============================================================================
def get_ai_response(user_message, user_id):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    context = get_user_context_string(user_id)
    prefs = user_preferences.get(user_id, {})
    pref_text = ""
    if prefs:
        sorted_prefs = sorted(prefs.items(), key=lambda x: x[1], reverse=True)
        pref_text = "📌 تفضيلات الطالب (من الأسئلة السابقة): " + ", ".join([s for s, _ in sorted_prefs[:3]]) + "\n"
    full_prompt = KNOWLEDGE_BASE + "\n\n" + context + pref_text
    payload = json.dumps({
        "contents": [
            {"role": "user", "parts": [{"text": full_prompt}]},
            {"role": "model", "parts": [{"text": "فهمت. أنا مساعد التوجيه الداخلي لبوت IT|3. سأوجه الطلاب دائماً لأزرار البوت فقط."}]},
            {"role": "user", "parts": [{"text": user_message}]}
        ],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1500}
    }).encode()
    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        response = urllib.request.urlopen(req, timeout=30)
        result = json.loads(response.read().decode())
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        logger.error(f"AI error: {e}")
        return "عذراً يا زميلي 🤝، المساعد الذكي غير متوفر حالياً.\n\nجرب الأزرار الرئيسية:\n📁 المواد الدراسية\n📝 التكاليف\n📅 الجدول الدراسي"

# ============================================================================
# التوجيه المباشر لأسماء الملفات والمحاضرات
# ============================================================================
def resolve_file_request(text):
    """محاولة فهم طلب ملف/محاضرة وإرجاع توجيه للزر المناسب"""
    text_lower = text.lower()
    # نمط: محاضرة (رقم) + مادة
    match = re.match(r"محاضرة\s*(\d+)\s*(.*)", text_lower)
    if match:
        num, subj = match.groups()
        subj = subj.strip()
        for keyword, subject in KEYWORD_MAP.items():
            if subj and keyword in subj:
                return f"📘 لتحميل الملف:\n اضغط: 📁 المواد الدراسية ➡️ {subject} ➡️ 📘 نظري ➡️ محاضرة {num}"
        return f"📁 ابحث عن المحاضرة {num} في 📁 المواد الدراسية ➡️ اختر المادة ➡️ 📘 نظري"
    # طلب ملف عام
    if "ملف" in text_lower or "تنزيل" in text_lower:
        return "⬇️ لتنزيل الملفات:\n اختر 📁 المواد الدراسية ➡️ المادة ➡️ المحاضرة"
    return None

# ============================================================================
# معالجة النص من الأزرار المعروفة (تحكم مباشر دون AI)
# ============================================================================
def handle_known_button(chat_id, text, user_id):
    """إذا تطابق النص مع زر معروف، يتم الرد برسالة محددة ويترك التحكم للبوت المصنع"""
    # التحقق من أسماء الأزرار الكاملة
    if text in BUTTON_NAMES:
        # نرسل رسالة توضيحية فقط، على افتراض أن المنصة ستوفر الأزرار الفعلية
        if BUTTON_NAMES[text] == "main_menu":
            msg = "🏠 <b>القائمة الرئيسية</b>\n\nاختر القسم الذي تريده.\n(الأزرار يتم توفيرها بواسطة المصنع)"
        elif BUTTON_NAMES[text] == "subjects_menu":
            msg = "📁 <b>المواد الدراسية</b>\n\nاختر المادة من القائمة.\n(تنقل بواسطة الأزرار)"
        elif BUTTON_NAMES[text] == "assignments_menu":
            msg = "📝 <b>التكاليف</b>\n\nاختر نوع التكليف.\n(الأزرار من المصنع)"
        elif BUTTON_NAMES[text] == "schedule_menu":
            msg = "📅 <b>الجدول الدراسي</b>\n\nاختر اليوم أو استعرض المحاضرات.\n(الأزرار تدار خارجياً)"
        elif BUTTON_NAMES[text] == "instructions_menu":
            msg = "📖 <b>التعليمات</b>\n\nكيفية استخدام البوت وتنزيل الملفات.\n(الأزرار من المصنع)"
        elif BUTTON_NAMES[text] == "search_prompt":
            msg = "🔍 اكتب اسم المادة أو الملف للبحث السريع."
        elif BUTTON_NAMES[text] in ("back", "go_home"):
            msg = "⬅️ عُد للخلف. الأزرار من المصنع."
        else:
            # للمواد والنظري/عملي
            msg = f"✅ اخترت {text}\nسيتم التنقل بالقائمة المناسبة.\n(إدارة الأزرار تعود للمصنع)"
        send_telegram_message(chat_id, msg)
        update_conversation_history(user_id, "model", msg)
        return True
    return False

# ============================================================================
# Webhook
# ============================================================================
@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    logger.info(f"Received: {json.dumps(data, ensure_ascii=False)}")

    # التعامل مع Callback Query (ضغط الأزرار الحقيقي)
    if "callback_query" in data:
        callback = data["callback_query"]
        chat_id = callback["message"]["chat"]["id"]
        callback_data = callback.get("data", "")
        user_id = callback["from"]["id"]
        # هنا نترك التحكم للمصنع، نكتفي بتأكيد الاستلام
        logger.info(f"Callback received: {callback_data} from user {user_id}")
        # يمكن إرسال رد منفصل بأن التحكم بيد الأزرار
        # لا نعالج أي منطق إضافي
        return {"status": "callback_ignored"}

    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    user_id = message.get("from", {}).get("id")

    if not chat_id or not text:
        return {"status": "ignored"}

    background_tasks.add_task(process_message, chat_id, text, user_id)
    return {"status": "processing"}

def process_message(chat_id, text, user_id):
    logger.info(f"User {user_id}: {text}")

    # تحديث السجلات
    update_conversation_history(user_id, "user", text)
    update_user_preferences(user_id, text)
    update_global_stats(text)

    # ===== 1. أوامر خاصة =====
    if text.startswith("/"):
        command = text.split()[0].lower()
        if command in ["/start", "/بدء"]:
            welcome = """🎓 <b>مرحباً بك في بوت IT|3</b>

أنا زميلك من الدفعة السادسة 🤝
أساعدك في التنقل داخل البوت وإيجاد المحاضرات والتكاليف.

<b>كيف أساعدك؟</b>
اكتب سؤالك مباشرة وسأوجهك للزر الصحيح:

• "محاضرات الموبايل 📱"
• "تكليف شبكات 🌐"
• "جدول الأحد 📅"
• "شرح Normalization 🏗"

<b>الأزرار يتم توفيرها بواسطة مصنع البوتات.</b>
يمكنك استخدامها للتنقل بسهولة."""
            send_telegram_message(chat_id, welcome)
            update_conversation_history(user_id, "model", welcome)
            return
        elif command in ["/تذكير", "/reminders"]:
            msg = get_upcoming_deadlines()
            send_telegram_message(chat_id, f"⏰ <b>التذكير بالتكاليف القادمة</b>\n\n{msg}")
            update_conversation_history(user_id, "model", msg)
            return
        elif command in ["/احصائيات", "/stats"]:
            if not global_stats:
                msg = "📊 لا توجد إحصائيات بعد."
            else:
                sorted_stats = sorted(global_stats.items(), key=lambda x: x[1], reverse=True)[:10]
                msg = "📊 <b>أكثر الكلمات المفتاحية استخداماً:</b>\n" + "\n".join([f"• {k}: {v} مرة" for k, v in sorted_stats])
            send_telegram_message(chat_id, msg)
            update_conversation_history(user_id, "model", msg)
            return
        elif command in ["/تفضيلاتي", "/myprefs"]:
            msg = get_preferences_summary(user_id)
            send_telegram_message(chat_id, f"🧠 <b>تفضيلاتك الخاصة:</b>\n{msg}")
            update_conversation_history(user_id, "model", msg)
            return
        elif command in ["/سياق", "/context"]:
            ctx = get_user_context_string(user_id) or "لا يوجد سياق."
            send_telegram_message(chat_id, f"💬 {ctx}")
            update_conversation_history(user_id, "model", ctx)
            return

    # ===== 2. التعامل مع نصوص الأزرار المعروفة =====
    if handle_known_button(chat_id, text, user_id):
        return

    # ===== 3. أسماء الملفات والمحاضرات المباشرة =====
    file_guide = resolve_file_request(text)
    if file_guide:
        send_telegram_message(chat_id, file_guide)
        update_conversation_history(user_id, "model", file_guide)
        return

    # ===== 4. التوجيه السريع بالكلمات المفتاحية (بدون AI) =====
    text_lower = text.lower()
    for keyword, subject in KEYWORD_MAP.items():
        if keyword in text_lower:
            guide = f"🎯 <b>توجيه سريع:</b>\n\n{text} ➡️ {subject}\n\nاستخدم الأزرار المتاحة من المصنع للوصول."
            send_telegram_message(chat_id, guide)
            update_conversation_history(user_id, "model", guide)
            return

    # ===== 5. أي نص آخر → الذكاء الاصطناعي =====
    ai_response = get_ai_response(text, user_id)
    send_telegram_message(chat_id, ai_response)
    update_conversation_history(user_id, "model", ai_response)

# ============================================================================
# صفحات التحقق
# ============================================================================
@app.get("/")
async def root():
    return {
        "status": "running",
        "bot": "IT_3_bot AI Assistant",
        "version": "5.0",
        "features": ["context_memory", "preferences", "stats", "deadlines", "button_aware"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
