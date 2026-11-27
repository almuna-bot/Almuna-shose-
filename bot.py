import os
import logging
import secrets
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from google import genai

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
BASE_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN or not GEMINI_KEY:
    raise ValueError("BOT_TOKEN أو GEMINI_API_KEY غير موجود")

client = genai.Client(api_key=GEMINI_KEY)

telegram_app = Application.builder().token(TOKEN).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً بك في Al Muna AI 👋\n\n"
        "أنا مساعدك الذكي لتصميم وتصنيع الأحذية.\n\n"
        "أستطيع مساعدتك في:\n"
        "👠 تصميم الموديلات والألوان\n"
        "📐 الباترونات والمقاسات\n"
        "🏭 التصنيع والخامات\n"
        "📸 تحليل صور الأحذية\n"
        "📦 المخزون والطلبات والأرباح\n\n"
        "ما الذي تريد العمل عليه اليوم؟"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text

    prompt = (
        "أنت Al Muna AI، مساعد متخصص في صناعة وتصميم الأحذية. "
        "ساعد المستخدم باللغة العربية في التصميم والباترونات "
        "والخامات والتصنيع والتسويق وإدارة المنتجات. "
        "أجب بدقة وبأسلوب عملي واضح.\n\n"
        f"رسالة المستخدم: {question}"
    )

    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        answer = response.text or "لم أتمكن من إنشاء إجابة."
        await update.message.reply_text(answer)

    except Exception:
        logger.exception("Gemini error")
        await update.message.reply_text(
            "حدث خطأ مؤقت أثناء الاتصال بالذكاء الاصطناعي. حاول مجدداً."
        )


telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, messages)
)


@asynccontextmanager
async def lifespan(api: FastAPI):
    if not BASE_URL or not WEBHOOK_SECRET:
        raise RuntimeError("إعدادات Render أو WEBHOOK_SECRET ناقصة")

    await telegram_app.initialize()
    await telegram_app.start()

    await telegram_app.bot.set_webhook(
        url=f"{BASE_URL}/telegram/webhook",
        secret_token=WEBHOOK_SECRET,
        allowed_updates=Update.ALL_TYPES
    )

    logger.info("Al Muna AI webhook started")

    yield

    await telegram_app.stop()
    await telegram_app.shutdown()


api = FastAPI(lifespan=lifespan)


@api.get("/")
async def home():
    return {"status": "online", "bot": "Al Muna AI"}


@api.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    supplied_secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token", ""
    )

@api.get("/")
@api.head("/")
async def home():
    return {"status": "online", "bot": "Al Muna AI"}    if not secrets.compare_digest(supplied_secret, WEBHOOK_SECRET):
        raise HTTPException(status_code=403, detail="Forbidden")

    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)

    await telegram_app.process_update(update)

    return {"ok": True}
