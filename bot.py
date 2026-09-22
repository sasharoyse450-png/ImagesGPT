import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from main import BOT_TOKEN, ADMIN_ID, WEBAPP_URL, IMAGE_COST, ensure, balance, sb

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎨 Создать изображение", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile"), InlineKeyboardButton("💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton("📜 История", callback_data="history")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")],
    ])

def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎨 Создать изображение", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("◀️ Назад", callback_data="main")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message: return
    db_user = ensure(user.id, user.username or "", user.full_name or "")
    await update.message.reply_text(
        f"🤖 <b>ImagesGPT</b>\n\nСоздавай изображения с помощью нейросети прямо в Telegram.\n\n💰 Баланс: <b>{db_user.get('balance', 0)} 🪙</b>\n\nВыбери действие:",
        parse_mode="HTML", reply_markup=main_keyboard())

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q: return
    await q.answer()
    user = q.from_user
    db_user = ensure(user.id, user.username or "", user.full_name or "")
    action = q.data
    if action == "main":
        await q.edit_message_text(f"🤖 <b>ImagesGPT</b>\n\nСоздавай изображения прямо в Telegram.\n\n💰 Баланс: <b>{db_user.get('balance', 0)} 🪙</b>\n\nВыбери действие:", parse_mode="HTML", reply_markup=main_keyboard())
    elif action == "profile":
        result = sb.table("history").select("id", count="exact").eq("user_id", user.id).eq("status", "done").execute()
        username = f"@{user.username}" if user.username else "не указан"
        text = f"👤 <b>Профиль</b>\n\n🆔 ID: <code>{user.id}</code>\n👤 Username: {username}\n📛 Имя: {user.full_name}\n\n💰 Баланс: <b>{db_user.get('balance', 0)} 🪙</b>\n🎨 Создано изображений: <b>{result.count or 0}</b>\n\n📅 Регистрация: {db_user.get('created_at', '—')}"
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=back_keyboard())
    elif action == "balance":
        await q.edit_message_text(f"💰 <b>Баланс</b>\n\nНа твоём балансе: <b>{db_user.get('balance', 0)} 🪙</b>\n\n🎨 1 изображение = {IMAGE_COST} 🪙", parse_mode="HTML", reply_markup=back_keyboard())
    elif action == "history":
        result = sb.table("history").select("id,prompt,size,status,image_url,created_at").eq("user_id", user.id).order("id", desc=True).limit(10).execute()
        items = result.data or []
        if not items:
            text = "📜 <b>История</b>\n\nУ тебя пока нет генераций."
        else:
            lines = ["📜 <b>Последние генерации</b>\n"]
            for item in items:
                icon = "✅" if item.get("status") == "done" else "⏳" if item.get("status") == "processing" else "❌"
                prompt = item.get("prompt", "").replace("\n", " ")
                if len(prompt) > 55: prompt = prompt[:55] + "..."
                lines.append(f"{icon} <b>#{item.get('id')}</b> {prompt}")
            text = "\n".join(lines)
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=back_keyboard())
    elif action == "help":
        text = f"ℹ️ <b>Помощь</b>\n\n🎨 <b>Создать изображение</b> — открывает генератор.\n\n👤 <b>Профиль</b> — статистика и данные.\n\n💰 <b>Баланс</b> — доступные монеты.\n\n📜 <b>История</b> — последние генерации.\n\n💳 Стоимость генерации: {IMAGE_COST} 🪙"
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=back_keyboard())

async def addbalance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message: return
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ У тебя нет доступа.")
        return
    if len(context.args) != 2:
        await update.message.reply_text("Использование:\n/addbalance USER_ID AMOUNT\n\nНапример:\n/addbalance 123456789 10")
        return
    try:
        uid, amount = int(context.args[0]), int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ USER_ID и AMOUNT должны быть числами.")
        return
    ensure(uid)
    new_balance = balance(uid, amount)
    await update.message.reply_text(f"✅ Баланс пользователя <code>{uid}</code> изменён.\n\n💰 Новый баланс: <b>{new_balance} 🪙</b>", parse_mode="HTML")

async def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addbalance", addbalance))
    application.add_handler(CallbackQueryHandler(callbacks))
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    try:
        await asyncio.Event().wait()
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    asyncio.run(run_bot())
