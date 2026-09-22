import os
import hmac
import hashlib
import json
import time
import base64
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import parse_qsl

import httpx

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel

from supabase import create_client, Client

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)


# ============================================================
# CONFIG
# ============================================================

ROOT = Path(__file__).parent

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

SUPABASE_BUCKET = os.getenv(
    "SUPABASE_BUCKET",
    "generated-images"
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    ""
).rstrip("/")

API_BASE = os.getenv(
    "API_BASE",
    "https://tooken.club/v1"
).rstrip("/")

API_KEY = os.getenv("API_KEY", "")

IMAGE_MODEL = os.getenv(
    "IMAGE_MODEL",
    "gpt-image-2"
)

MODERATION_MODEL = os.getenv(
    "MODERATION_MODEL",
    "deepseek-v4-flash"
)

# Новым пользователям выдаём 3 монеты
START_BALANCE = int(
    os.getenv("START_BALANCE", "3")
)

# Стоимость одного изображения
IMAGE_COST = int(
    os.getenv("IMAGE_COST", "1")
)

MAX_CONCURRENT = int(
    os.getenv("MAX_CONCURRENT", "8")
)

TIMEOUT = int(
    os.getenv("GENERATION_TIMEOUT", "180")
)


# ============================================================
# VALIDATION
# ============================================================

if not SUPABASE_URL:
    raise RuntimeError(
        "SUPABASE_URL is required"
    )

if not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_KEY is required"
    )

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is required"
    )


# ============================================================
# CLIENTS
# ============================================================

sb: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

sem = asyncio.Semaphore(
    MAX_CONCURRENT
)

app = FastAPI(
    title="ImagesGPT"
)


# ============================================================
# STATIC WEB APP
# ============================================================

WEBAPP_DIR = ROOT / "webapp"

if WEBAPP_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(WEBAPP_DIR)),
        name="static"
    )


# ============================================================
# HELPERS
# ============================================================

def now():
    return datetime.now(
        timezone.utc
    ).isoformat()


def ensure(uid, username="", name=""):
    """
    Создаёт пользователя, если его ещё нет.
    Новому пользователю выдаётся START_BALANCE монет.
    """

    result = (
        sb.table("users")
        .select("*")
        .eq("user_id", uid)
        .maybe_single()
        .execute()
    )

    if not result.data:
        row = {
            "user_id": uid,
            "username": username or "",
            "full_name": name or "",
            "balance": START_BALANCE,
            "created_at": now(),
            "last_seen": now(),
        }

        sb.table("users").insert(row).execute()

        return row

    sb.table("users").update({
        "username": username or "",
        "full_name": name or "",
        "last_seen": now(),
    }).eq(
        "user_id",
        uid
    ).execute()

    result = (
        sb.table("users")
        .select("*")
        .eq("user_id", uid)
        .single()
        .execute()
    )

    return result.data


def get_user(uid):
    """
    Получает пользователя из Supabase.
    """

    result = (
        sb.table("users")
        .select("*")
        .eq("user_id", uid)
        .maybe_single()
        .execute()
    )

    return result.data


def balance(uid, delta):
    """
    Изменение баланса через Supabase RPC.
    """

    result = sb.rpc(
        "change_user_balance",
        {
            "p_user_id": uid,
            "p_delta": delta,
        }
    ).execute()

    return result.data


def reserve(uid):
    """
    Резервирует монету перед генерацией.
    """

    result = sb.rpc(
        "reserve_user_coin",
        {
            "p_user_id": uid,
            "p_cost": IMAGE_COST,
        }
    ).execute()

    return bool(result.data)


def addhist(
    uid,
    prompt,
    size,
    status,
    url=None
):
    """
    Добавляет генерацию в историю.
    """

    result = (
        sb.table("history")
        .insert({
            "user_id": uid,
            "prompt": prompt,
            "size": size,
            "status": status,
            "image_url": url,
            "created_at": now(),
        })
        .execute()
    )

    return result.data[0]["id"]


def upd(
    history_id,
    status,
    url=None
):
    """
    Обновляет историю генерации.
    """

    sb.table("history").update({
        "status": status,
        "image_url": url,
    }).eq(
        "id",
        history_id
    ).execute()


# ============================================================
# TELEGRAM WEB APP INIT DATA
# ============================================================

def validate_telegram_init_data(init_data):
    """
    Проверяет Telegram Web App initData.

    Возвращает данные пользователя Telegram.
    """

    if not init_data:
        raise HTTPException(
            status_code=401,
            detail="Telegram initData is missing"
        )

    try:
        parsed = dict(
            parse_qsl(
                init_data,
                keep_blank_values=True
            )
        )
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid Telegram initData"
        )

    received_hash = parsed.get("hash")

    if not received_hash:
        raise HTTPException(
            status_code=401,
            detail="Telegram hash is missing"
        )

    data_check_items = []

    for key in sorted(parsed.keys()):
        if key == "hash":
            continue

        data_check_items.append(
            f"{key}={parsed[key]}"
        )

    data_check_string = "\n".join(
        data_check_items
    )

    secret_key = hmac.new(
        b"WebAppData",
        BOT_TOKEN.encode("utf-8"),
        hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(
        calculated_hash,
        received_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid Telegram initData"
        )

    # Telegram user JSON
    user_raw = parsed.get("user")

    if not user_raw:
        raise HTTPException(
            status_code=401,
            detail="Telegram user is missing"
        )

    try:
        telegram_user = json.loads(
            user_raw
        )
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid Telegram user data"
        )

    uid = telegram_user.get("id")

    if not uid:
        raise HTTPException(
            status_code=401,
            detail="Telegram user ID is missing"
        )

    username = telegram_user.get(
        "username",
        ""
    )

    first_name = telegram_user.get(
        "first_name",
        ""
    )

    last_name = telegram_user.get(
        "last_name",
        ""
    )

    full_name = (
        f"{first_name} {last_name}"
    ).strip()

    return {
        "user_id": int(uid),
        "username": username,
        "full_name": full_name,
    }


async def current(init_data):
    """
    Проверяет Telegram Web App пользователя
    и возвращает пользователя из Supabase.
    """

    telegram_user = validate_telegram_init_data(
        init_data
    )

    return ensure(
        telegram_user["user_id"],
        telegram_user["username"],
        telegram_user["full_name"]
    )


# ============================================================
# AI MODERATION
# ============================================================

async def moderate(prompt):
    """
    Модерация через TokenClub.
    """

    if not API_KEY:
        return True

    payload = {
        "model": MODERATION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Reply only ALLOW or BLOCK. "
                    "Block disallowed sexual content, "
                    "sexual content involving minors, "
                    "graphic gore, or serious wrongdoing "
                    "instructions.\n\n"
                    "Prompt: "
                    + prompt
                ),
            }
        ],
        "temperature": 0,
    }

    try:
        async with httpx.AsyncClient(
            timeout=45
        ) as client:

            response = await client.post(
                API_BASE + "/chat/completions",
                headers={
                    "Authorization":
                        "Bearer " + API_KEY,
                    "Content-Type":
                        "application/json",
                },
                json=payload,
            )

            if not response.is_success:
                return False

            data = response.json()

            answer = (
                data["choices"][0]
                ["message"]["content"]
                .strip()
                .upper()
            )

            return answer.startswith(
                "ALLOW"
            )

    except Exception:
        return False


# ============================================================
# IMAGE GENERATION
# ============================================================

async def make_image(
    prompt,
    size
):
    """
    Генерация изображения через TokenClub.
    """

    payload = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "size": size,
        "n": 1,
    }

    async with sem:

        async with httpx.AsyncClient(
            timeout=TIMEOUT
        ) as client:

            response = await client.post(
                API_BASE + "/images/generations",
                headers={
                    "Authorization":
                        "Bearer " + API_KEY,
                    "Content-Type":
                        "application/json",
                },
                json=payload,
            )

            response.raise_for_status()

            data = response.json()

            item = data["data"][0]

    # TokenClub вернул URL
    if item.get("url"):
        return item["url"]

    # TokenClub вернул base64
    if item.get("b64_json"):

        raw = base64.b64decode(
            item["b64_json"]
        )

        filename = (
            f"{int(time.time() * 1000)}_"
            f"{hashlib.sha256(raw).hexdigest()[:12]}"
            ".png"
        )

        sb.storage.from_(
            SUPABASE_BUCKET
        ).upload(
            filename,
            raw,
            {
                "content-type":
                    "image/png",
                "upsert":
                    "false",
            }
        )

        public_url = (
            sb.storage
            .from_(SUPABASE_BUCKET)
            .get_public_url(filename)
        )

        return public_url

    raise RuntimeError(
        "No image returned by TokenClub"
    )


# ============================================================
# WEB APP API
# ============================================================

class GenReq(BaseModel):
    prompt: str
    size: str = "1024x1024"


@app.get("/")
async def root():

    index_file = (
        ROOT /
        "webapp" /
        "index.html"
    )

    if not index_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Web App not found"
        )

    return FileResponse(
        index_file
    )


@app.get("/health")
async def health():
    return {
        "ok": True,
        "service": "ImagesGPT"
    }


@app.get("/api/me")
async def me(
    x_telegram_init_data: str | None =
        Header(default=None)
):

    user = await current(
        x_telegram_init_data
    )

    result = (
        sb.table("history")
        .select(
            "id",
            count="exact"
        )
        .eq(
            "user_id",
            user["user_id"]
        )
        .eq(
            "status",
            "done"
        )
        .execute()
    )

    total_images = result.count or 0

    return {
        "user": {
            "user_id":
                user["user_id"],
            "username":
                user.get("username", ""),
            "full_name":
                user.get("full_name", ""),
            "balance":
                user.get("balance", 0),
            "created_at":
                user.get("created_at"),
            "id":
                user["user_id"],
            "total_images":
                total_images,
        }
    }


@app.get("/api/history")
async def history(
    x_telegram_init_data: str | None =
        Header(default=None)
):

    user = await current(
        x_telegram_init_data
    )

    result = (
        sb.table("history")
        .select(
            "id,prompt,size,status,image_url,created_at"
        )
        .eq(
            "user_id",
            user["user_id"]
        )
        .order(
            "id",
            desc=True
        )
        .limit(30)
        .execute()
    )

    return {
        "items":
            result.data or []
    }


@app.post("/api/generate")
async def generate(
    q: GenReq,
    x_telegram_init_data: str | None =
        Header(default=None)
):

    user = await current(
        x_telegram_init_data
    )

    prompt = q.prompt.strip()

    allowed_sizes = {
        "1024x1024",
        "1536x1024",
        "1024x1536",
    }

    size = (
        q.size
        if q.size in allowed_sizes
        else "1024x1024"
    )

    if not prompt:
        raise HTTPException(
            status_code=400,
            detail="Введите описание"
        )

    if len(prompt) > 2000:
        raise HTTPException(
            status_code=400,
            detail="Промпт слишком длинный"
        )

    if user["balance"] < IMAGE_COST:
        raise HTTPException(
            status_code=402,
            detail="Недостаточно монет"
        )

    # Модерация
    allowed = await moderate(
        prompt
    )

    if not allowed:
        raise HTTPException(
            status_code=400,
            detail="Запрос не прошёл модерацию"
        )

    # Резервируем монету
    if not reserve(
        user["user_id"]
    ):
        raise HTTPException(
            status_code=402,
            detail="Недостаточно монет"
        )

    history_id = addhist(
        user["user_id"],
        prompt,
        size,
        "processing"
    )

    try:

        image_url = await make_image(
            prompt,
            size
        )

        upd(
            history_id,
            "done",
            image_url
        )

        fresh = ensure(
            user["user_id"],
            user.get("username", ""),
            user.get("full_name", "")
        )

        return {
            "ok": True,
            "image_url":
                image_url,
            "balance":
                fresh["balance"],
        }

    except Exception as error:

        # Возвращаем монету
        balance(
            user["user_id"],
            IMAGE_COST
        )

        upd(
            history_id,
            "error"
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Генерация не удалась: "
                + str(error)[:250]
            )
        )


# ============================================================
# TELEGRAM BOT MENU
# ============================================================

def main_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎨 Создать изображение",
                web_app=WebAppInfo(
                    url=WEBAPP_URL
                )
            )
        ],
        [
            InlineKeyboardButton(
                "👤 Профиль",
                callback_data="profile"
            ),
            InlineKeyboardButton(
                "💰 Баланс",
                callback_data="balance"
            ),
        ],
        [
            InlineKeyboardButton(
                "📜 История",
                callback_data="history"
            )
        ],
        [
            InlineKeyboardButton(
                "ℹ️ Помощь",
                callback_data="help"
            )
        ],
    ])


def back_keyboard():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎨 Создать изображение",
                web_app=WebAppInfo(
                    url=WEBAPP_URL
                )
            )
        ],
        [
            InlineKeyboardButton(
                "◀️ Назад",
                callback_data="main"
            )
        ]
    ])


# ============================================================
# /START
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    db_user = ensure(
        user.id,
        user.username or "",
        user.full_name or ""
    )

    text = (
        "🤖 <b>ImagesGPT</b>\n\n"
        "Создавай изображения с помощью "
        "нейросети прямо в Telegram.\n\n"
        f"💰 Баланс: "
        f"<b>{db_user.get('balance', 0)} 🪙</b>\n\n"
        "Выбери действие:"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=main_keyboard()
    )


# ============================================================
# CALLBACKS
# ============================================================

async def callbacks(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user = query.from_user

    if not user:
        return

    db_user = ensure(
        user.id,
        user.username or "",
        user.full_name or ""
    )

    action = query.data

    # --------------------------------------------------------
    # MAIN
    # --------------------------------------------------------

    if action == "main":

        text = (
            "🤖 <b>ImagesGPT</b>\n\n"
            "Создавай изображения прямо "
            "в Telegram.\n\n"
            f"💰 Баланс: "
            f"<b>{db_user.get('balance', 0)} 🪙</b>\n\n"
            "Выбери действие:"
        )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=main_keyboard()
        )

        return

    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

    if action == "profile":

        result = (
            sb.table("history")
            .select(
                "id",
                count="exact"
            )
            .eq(
                "user_id",
                user.id
            )
            .eq(
                "status",
                "done"
            )
            .execute()
        )

        total_images = (
            result.count or 0
        )

        username = (
            f"@{user.username}"
            if user.username
            else "не указан"
        )

        text = (
            "👤 <b>Профиль</b>\n\n"
            f"🆔 ID: <code>{user.id}</code>\n"
            f"👤 Username: {username}\n"
            f"📛 Имя: {user.full_name}\n\n"
            f"💰 Баланс: "
            f"<b>{db_user.get('balance', 0)} 🪙</b>\n"
            f"🎨 Создано изображений: "
            f"<b>{total_images}</b>\n\n"
            f"📅 Регистрация: "
            f"{db_user.get('created_at', '—')}"
        )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )

        return

    # --------------------------------------------------------
    # BALANCE
    # --------------------------------------------------------

    if action == "balance":

        current_balance = (
            db_user.get(
                "balance",
                0
            )
        )

        text = (
            "💰 <b>Баланс</b>\n\n"
            f"На твоём балансе: "
            f"<b>{current_balance} 🪙</b>\n\n"
            f"🎨 1 изображение = "
            f"{IMAGE_COST} 🪙"
        )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )

        return

    # --------------------------------------------------------
    # HISTORY
    # --------------------------------------------------------

    if action == "history":

        result = (
            sb.table("history")
            .select(
                "id,prompt,size,status,image_url,created_at"
            )
            .eq(
                "user_id",
                user.id
            )
            .order(
                "id",
                desc=True
            )
            .limit(10)
            .execute()
        )

        items = result.data or []

        if not items:

            text = (
                "📜 <b>История</b>\n\n"
                "У тебя пока нет генераций."
            )

        else:

            lines = [
                "📜 <b>Последние генерации</b>\n"
            ]

            for item in items:

                status = item.get(
                    "status",
                    "unknown"
                )

                if status == "done":
                    icon = "✅"
                elif status == "processing":
                    icon = "⏳"
                else:
                    icon = "❌"

                prompt = (
                    item.get(
                        "prompt",
                        ""
                    )
                    .replace("\n", " ")
                )

                if len(prompt) > 55:
                    prompt = (
                        prompt[:55]
                        + "..."
                    )

                lines.append(
                    f"{icon} "
                    f"<b>#{item.get('id')}</b> "
                    f"{prompt}"
                )

            text = "\n".join(lines)

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )

        return

    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

    if action == "help":

        text = (
            "ℹ️ <b>Помощь</b>\n\n"
            "🎨 <b>Создать изображение</b> — "
            "открывает генератор.\n\n"
            "👤 <b>Профиль</b> — "
            "твоя статистика и данные.\n\n"
            "💰 <b>Баланс</b> — "
            "количество доступных монет.\n\n"
            "📜 <b>История</b> — "
            "последние генерации.\n\n"
            f"💳 Стоимость генерации: "
            f"{IMAGE_COST} 🪙"
        )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )

        return


# ============================================================
# ADMIN
# ============================================================

async def addbalance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    if user.id != ADMIN_ID:

        await update.message.reply_text(
            "❌ У тебя нет доступа."
        )

        return

    if len(context.args) != 2:

        await update.message.reply_text(
            "Использование:\n"
            "/addbalance USER_ID AMOUNT\n\n"
            "Например:\n"
            "/addbalance 123456789 10"
        )

        return

    try:

        uid = int(
            context.args[0]
        )

        amount = int(
            context.args[1]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ USER_ID и AMOUNT должны "
            "быть числами."
        )

        return

    ensure(uid)

    new_balance = balance(
        uid,
        amount
    )

    await update.message.reply_text(
        f"✅ Баланс пользователя "
        f"<code>{uid}</code> изменён.\n\n"
        f"💰 Новый баланс: "
        f"<b>{new_balance} 🪙</b>",
        parse_mode="HTML"
    )


# ============================================================
# TELEGRAM BOT
# ============================================================

async def start_bot():

    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "addbalance",
            addbalance
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            callbacks
        )
    )

    await application.initialize()

    await application.start()

    if application.updater:

        await application.updater.start_polling(
            drop_pending_updates=True
        )

    return application


# ============================================================
# DATABASE INIT
# ============================================================

def init_db():
    """
    Supabase schema создаётся через schema.sql.
    Локальная SQLite база не используется.
    """
    return


# ============================================================
# FASTAPI STARTUP
# ============================================================

@app.on_event("startup")
async def startup():

    init_db()

    app.state.bot = (
        await start_bot()
    )


@app.on_event("shutdown")
async def shutdown():

    bot = getattr(
        app.state,
        "bot",
        None
    )

    if bot:

        if bot.updater:

            try:
                await bot.updater.stop()
            except Exception:
                pass

        try:
            await bot.stop()
        except Exception:
            pass

        try:
            await bot.shutdown()
        except Exception:
            pass


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                "10000"
            )
        ),
    )
