import asyncio,base64,html,logging,sqlite3,time,uuid,traceback,random,os
from datetime import datetime,timedelta
from urllib.parse import quote
import httpx
from telegram import(Update,InlineKeyboardButton,InlineKeyboardMarkup,InputMediaPhoto,LabeledPrice,InlineQueryResultArticle,InputTextMessageContent)
from telegram.constants import ParseMode,ChatAction
from telegram.ext import(Application,CommandHandler,MessageHandler,CallbackQueryHandler,ContextTypes,filters,PreCheckoutQueryHandler,InlineQueryHandler,ChosenInlineResultHandler)

# ═══════════ CONFIG ═══════════
BOT_TOKEN='8979688376:AAG_QM3t0NKOEiieC3_38wvb-ZsmziaXzRE'
ADMIN_ID=8130244626
API_KEY='tc_live_6a7075340c595455d423a0471dc7a534d8450dddd9c6de39'
API_BASE='https://tooken.club/v1'
IMAGE_MODEL='gpt-image-2'
MODERATION_MODEL='deepseek-v4-flash'
TIMEOUT_DEFAULT=600
DB=os.environ.get('DB_PATH','gptimages.db')
PRIVACY_URL='https://telegra.ph/POLITIKA-KONFIDENCIALNOSTI-08-12-99'
OFFER_URL='https://telegra.ph/PUBLICHNAYA-OFERTA-08-12-15'
BOT_USERNAME='ImagesGPTbot'
HISTORY_PAGE_SIZE=10
CAPTION_MAX=1000
STAR_RATE=1.3
STAR_PACKS=[(10,10),(25,30),(50,70),(100,150)]
REF_L1=10
REF_L2=5
ROULETTE_PRIZES=[(0,20),(1,35),(2,25),(3,12),(5,6),(10,2)]
ADV_DEFAULT_PERCENT=20
NEW_USER_HOURS=1
NEW_USER_LIMIT_COUNT=10
NEW_USER_LIMIT_WINDOW=300
REF_WITHDRAW_TO_BALANCE_MIN=10
REF_WITHDRAW_TO_CARD_MIN=100
GEN_COOLDOWN=300
# 💎 Premium
PREMIUM_STARS=100
PREMIUM_DAYS=30
PREMIUM_COOLDOWN=30
# 🚀 Ускорение
RUSH_COST=2
PORT=int(os.environ.get('PORT',8080))
WEBHOOK_PATH='/webhook'
PUBLIC_DOMAIN=os.environ.get('RAILWAY_PUBLIC_DOMAIN')

SEED_APIS=[
 ('image','Tooken #1','https://tooken.club/v1','tc_live_e59a923d4d019e06418c15a939be0bd54ce3a4c9a94a6b0a','gpt-image-2',100),
 ('image','Tooken #2','https://tooken.club/v1','tc_live_32603684062beef0cd789f1798f34e8161e3d2dd28c6cac6','gpt-image-2',200),
 ('image','Tooken #3','https://tooken.club/v1','tc_live_715d21ae8549dc1e205dcbdca6d5956aa7d59b0cc7054535','gpt-image-2',300),
 ('image','Tooken Old','https://tooken.club/v1','tc_live_6a7075340c595455d423a0471dc7a534d8450dddd9c6de39','gpt-image-2',400),
 ('mod','Mod #1','https://tooken.club/v1','tc_live_e59a923d4d019e06418c15a939be0bd54ce3a4c9a94a6b0a','deepseek-v4-flash',100),
 ('mod','Mod #2','https://tooken.club/v1','tc_live_32603684062beef0cd789f1798f34e8161e3d2dd28c6cac6','deepseek-v4-flash',200),
 ('mod','Mod #3','https://tooken.club/v1','tc_live_715d21ae8549dc1e205dcbdca6d5956aa7d59b0cc7054535','deepseek-v4-flash',300),
 ('mod','Mod Old','https://tooken.club/v1','tc_live_6a7075340c595455d423a0471dc7a534d8450dddd9c6de39','deepseek-v4-flash',400)]

BANNERS_DIR=os.path.join(os.path.dirname(os.path.abspath(__file__)),'banners')
BANNER_KEYS={'menu':'Главное меню','balance':'Профиль','topup':'Донат','exchange':'Обмен','history':'История','promo':'Промокод','ref':'Партнёрка','support':'Поддержка','help':'Помощь','lang':'Язык'}

logging.basicConfig(level=logging.INFO,format='%(asctime)s | %(levelname)s | %(message)s')
log=logging.getLogger('ImagesGPT')

# ═══════════ I18N ═══════════
LANGS=('ru','en')
LANGS_NAMES={'ru':'🇷🇺 Русский','en':'🇬🇧 English'}

TR={'ru':{
'menu_title':'🤖 <b>ImagesGPT</b>','balance':'💰 Профиль','topup':'💝 Пожертвование','history':'📜 История',
'promo':'🎁 Промокод','ref':'👥 Пригласить друга','support':'🆘 Поддержка','help':'ℹ️ Помощь',
'lang':'🌐 Язык','roulette':'🎰 Рулетка','premium':'💎 Premium','create_btn':'🎨 Создать изображение',
'back_menu':'◀️ В меню','back':'◀️ Назад','cancel':'❌ Отмена','rubles':'Рубли','coins':'Монеты',
'rate':'Курс','gen_cost':'Генерация','choose_action':'Выбери действие ниже 👇',
'your_balance':'💰 <b>Профиль</b>\n━━━━━━━━━━━━━━━━━━━━',
'topup_title':'💝 <b>Поддержать проект</b>',
'topup_note':'Бот <b>полностью бесплатный</b>. Если хочешь поддержать разработку — можешь отправить звёзды.\n\nВ благодарность начислим бонусные монеты (они для фана).',
'support_btn':'🆘 Написать в поддержку','exchange_btn':'🔄 Обменять на монеты',
'exchange_title':'🔄 <b>Обмен рублей на монеты</b>','exchange_ask':'Напиши, сколько рублей хочешь обменять:',
'exchange_must_be_multiple':'Сумма должна быть кратна {rate} ₽','exchange_done':'✅ <b>Обмен выполнен</b>',
'exchange_spent':'Списано','exchange_got':'Получено','history_empty':'📜 <b>История пуста.</b>',
'history_title':'📜 <b>Последние генерации</b>','history_hint':'<i>Нажми на номер, чтобы открыть.</i>',
'history_not_found':'❌ Запись не найдена','history_failed':'❌ <i>Генерация не завершилась успешно</i>',
'history_img_unavail':'⚠️ <i>Картинка недоступна</i>','ref_title':'👥 <b>Пригласить друга</b>',
'ref_your_link':'🔗 Твоя ссылка:','ref_you_get':'💸 Ты получаешь <b>{percent}%</b> с донатов друзей.',
'ref_earn_rub':'💵 Заработанное начисляется в реферальный баланс.',
'ref_invited':'👤 Приглашено','ref_earned':'💵 Заработано','ref_share':'📤 Поделиться',
'ref_note':'<i>Бонус начисляется автоматически при донате друга.</i>',
'ref_balance':'Реферальный баланс','ref_withdraw':'💸 Вывести',
'ref_withdraw_title':'💸 <b>Вывод реферальных</b>',
'ref_withdraw_text':'🎁 Реферальный баланс: <b>{bal} ₽</b>\n\n💸 <b>На основной баланс</b> — от {min_bal} ₽, мгновенно.\n💳 <b>На карту</b> — от {min_card} ₽, заявка обрабатывается админом.\n\nИстория: /ref_history',
'ref_withdraw_to_balance':'💸 На баланс (от {min_bal} ₽)',
'ref_withdraw_to_card':'💳 На карту (от {min_card} ₽)',
'ref_withdraw_to_balance_ask':'💸 Введи сумму в ₽.\nМинимум: <b>{min_bal} ₽</b>\nДоступно: <b>{bal} ₽</b>',
'ref_withdraw_to_card_ask':'💳 Введи сумму в ₽.\nМинимум: <b>{min_card} ₽</b>\nДоступно: <b>{bal} ₽</b>',
'ref_withdraw_card_number':'💳 Введи <b>номер карты</b> или реквизиты.\n<i>Сумма: {amount} ₽</i>',
'ref_withdraw_too_low':'❌ Минимум: <b>{min} ₽</b>. У тебя: <b>{bal} ₽</b>.',
'ref_withdraw_not_enough':'❌ Недостаточно средств. У тебя <b>{bal} ₽</b>.',
'ref_withdraw_balance_ok':'✅ <b>Переведено на баланс</b>\n\n💸 Списано: <b>{amount} ₽</b>\n💵 Баланс: <b>{bal} ₽</b>',
'ref_withdraw_card_ok':'✅ <b>Заявка на вывод создана</b>\n\n💳 Сумма: <b>{amount} ₽</b>\n🔢 Заявка: <b>#{wid}</b>',
'ref_history_title':'📜 <b>История выводов</b>','ref_history_empty':'📜 <i>Пока нет выводов.</i>',
'promo_ask':'🎁 <b>Введи промокод:</b>','promo_ok':'🎉 Промокод активирован!',
'promo_credited':'Начислено: <b>+{n}</b> монет','support_title':'🆘 <b>Поддержка</b>',
'support_open_exists':'У тебя есть открытый тикет <b>#{tid}</b>.','support_desc':'Опиши проблему — ответим как можно скорее.',
'support_new':'✍️ Создать новый тикет','support_my':'📋 Мои тикеты',
'support_continue':'💬 Продолжить тикет #{tid}','support_create_ask':'✍️ <b>Опиши проблему</b> (текст или фото):',
'support_created':'✅ <b>Тикет #{tid} создан.</b>','support_none':'📋 У тебя пока нет тикетов.',
'support_my_title':'📋 <b>Твои тикеты</b>','help_title':'ℹ️ <b>Помощь</b>',
'help_text':'🎨 <b>Создать изображение</b> — <b>бесплатно</b>, 1 раз в 5 минут.\n\n💎 <b>Premium</b> — быстрее и приоритетнее.\n\n💰 <b>Профиль</b> — статистика и монеты.\n\n💝 <b>Пожертвование</b> — если хочешь поддержать.\n\n🎰 <b>Рулетка</b> — раз в неделю крути монеты.\n\n📜 <b>История</b> — список генераций.\n\n👥 <b>Пригласить друга</b> — {percent}% с донатов.\n\n🎁 <b>Промокод</b> — бонусный код.\n\n🆘 <b>Поддержка</b> — тикет.\n\n✨ <b>Inline</b> — @{bot} промпт в любом чате.',
'free_gen':'🎨 <b>Бесплатно</b>',
'create_prompt':'🎨 <b>Напиши описание изображения:</b>\n\nМаксимум 4000 символов.',
'checking':'🔎 Проверяю запрос…','blocked':'❌ <b>Запрос отклонён.</b>','choose_size':'📐 <b>Выбери размер:</b>',
'size_1024':'🟦 1024×1024','confirm_title':'🎨 <b>Проверь запрос</b>','confirm_create':'✅ Создать',
'queue_title':'⏳ <b>В очереди</b>','queue_pos':'Позиция','queue_cancel':'❌ Отменить',
'in_progress':'🎨 <b>Генерирую…</b>\nОбычно 30–90 секунд.\nЛимит: {limit}.','done_title':'✅ <b>Готово!</b>',
'time_label':'⏱ Время','left_coins':'💰 Монеты','timeout':'⏱ Превышен лимит ({limit}). Попробуй ещё раз.',
'error_gen':'❌ Ошибка генерации. Попробуй ещё раз.',
'cooldown':'⏱ <b>Следующая генерация через {time}</b>\n\nЛимит: 1 генерация раз в 5 минут.\n\n💎 <b>Premium</b> — кулдаун 30 сек → /premium',
'insufficient_coins':'❌ Недостаточно монет.',
'terms_title':'📄 <b>Перед началом работы</b>','terms_lead':'Ознакомься с документами:',
'terms_privacy':'🔒 Политика конфиденциальности','terms_offer':'📜 Пользовательское соглашение',
'terms_note':'Для использования бота необходимо принять условия.',
'terms_accept':'✅ Согласен с условиями','terms_reject':'❌ Отклонить','terms_accepted':'✅ Условия приняты.',
'terms_rejected':'❌ Вы отклонили условия.\n\nДоступ закрыт. Если передумаете — /start.',
'terms_first':'❌ Сначала примите условия. /start','banned_access':'⛔ Доступ ограничен.',
'banned_title':'⛔ <b>Доступ к боту ограничен.</b>','banned_reason':'Причина','menu_hint':'Выбери действие в меню 👇',
'lang_title':'🌐 <b>Выбор языка</b>','lang_current':'Текущий язык','lang_switched':'✅ Язык: {lang}',
'rate_limit':'⏱ Слишком часто. Подожди ещё {sec} сек.','not_enough_rub':'❌ Недостаточно рублей.',
'min_exchange':'Минимум для обмена','you_have':'У тебя','ticket_msg_added':'📩 Сообщение добавлено в тикет #{tid}.',
'ticket_closed':'🔒 Тикет #{tid} закрыт.','support_reply':'💬 <b>Ответ поддержки (тикет #{tid}):</b>',
'reply_here':'Ответь сюда, чтобы продолжить.','roulette_title':'🎰 <b>Рулетка</b>',
'roulette_rules':'Рулетка доступна <b>раз в неделю</b> (Пн–Вс).\n\nВозможные призы: <b>0, 1, 2, 3, 5, 10</b> монет.',
'roulette_spin':'🎰 Крутить','roulette_spinning':'🎰 <b>Крутим…</b>','roulette_won':'🎉 <b>Ты выиграл {n} 🪙!</b>',
'roulette_empty':'💨 <b>Пусто.</b> Сегодня не повезло.','roulette_done':'✅ Приходи на следующей неделе!',
'roulette_already_this_week':'✅ Ты уже крутил рулетку на этой неделе.\n\nСледующая попытка — в понедельник.',
'new_user_limit':'🛡 Лимит нового аккаунта. Попробуй позже.',
'share_btn':'📤 Поделиться',
'donate_thanks':'💝 <b>Спасибо за поддержку!</b>\n\n⭐ Звёзд: <b>{stars}</b>\n🎁 Монет начислено: <b>+{coins}</b> 🪙\n\n<i>Генерация и так бесплатна — это благодарность.</i>'},
'en':{
'menu_title':'🤖 <b>ImagesGPT</b>','balance':'💰 Profile','topup':'💝 Donate','history':'📜 History',
'promo':'🎁 Promo','ref':'👥 Invite a friend','support':'🆘 Support','help':'ℹ️ Help',
'lang':'🌐 Language','roulette':'🎰 Roulette','premium':'💎 Premium','create_btn':'🎨 Create image',
'back_menu':'◀️ Menu','back':'◀️ Back','cancel':'❌ Cancel','rubles':'Rubles','coins':'Coins',
'rate':'Rate','gen_cost':'Generation','choose_action':'Choose an action 👇',
'your_balance':'💰 <b>Profile</b>\n━━━━━━━━━━━━━━━━━━━━',
'topup_title':'💝 <b>Support the project</b>',
'topup_note':'The bot is <b>completely free</b>. If you want to support development — send some stars.\n\nAs a thank you we credit bonus coins (for fun).',
'support_btn':'🆘 Contact support','exchange_btn':'🔄 Exchange',
'exchange_title':'🔄 <b>Exchange rubles to coins</b>','exchange_ask':'How many rubles?',
'exchange_must_be_multiple':'Must be a multiple of {rate} ₽','exchange_done':'✅ <b>Exchange complete</b>',
'exchange_spent':'Spent','exchange_got':'Received','history_empty':'📜 <b>History is empty.</b>',
'history_title':'📜 <b>Recent generations</b>','history_hint':'<i>Tap a number to open.</i>',
'history_not_found':'❌ Not found','history_failed':'❌ <i>Generation failed</i>',
'history_img_unavail':'⚠️ <i>Image unavailable</i>','ref_title':'👥 <b>Invite a friend</b>',
'ref_your_link':'🔗 Your link:','ref_you_get':'💸 You get <b>{percent}%</b> of friend donations.',
'ref_earn_rub':'💵 Earnings go to referral balance.',
'ref_invited':'👤 Invited','ref_earned':'💵 Earned','ref_share':'📤 Share',
'ref_note':'<i>Bonus credited automatically on friend donation.</i>',
'ref_balance':'Referral balance','ref_withdraw':'💸 Withdraw',
'ref_withdraw_title':'💸 <b>Withdraw referral earnings</b>',
'ref_withdraw_text':'🎁 Referral balance: <b>{bal} ₽</b>\n\n💸 <b>To main balance</b> — min {min_bal} ₽.\n💳 <b>To card</b> — min {min_card} ₽.\n\nHistory: /ref_history',
'ref_withdraw_to_balance':'💸 To balance (min {min_bal} ₽)',
'ref_withdraw_to_card':'💳 To card (min {min_card} ₽)',
'ref_withdraw_to_balance_ask':'💸 Enter amount.\nMin: <b>{min_bal} ₽</b>\nAvailable: <b>{bal} ₽</b>',
'ref_withdraw_to_card_ask':'💳 Enter amount.\nMin: <b>{min_card} ₽</b>\nAvailable: <b>{bal} ₽</b>',
'ref_withdraw_card_number':'💳 Enter <b>card number</b>.\n<i>Amount: {amount} ₽</i>',
'ref_withdraw_too_low':'❌ Minimum: <b>{min} ₽</b>. You have: <b>{bal} ₽</b>.',
'ref_withdraw_not_enough':'❌ Not enough funds. You have <b>{bal} ₽</b>.',
'ref_withdraw_balance_ok':'✅ <b>Transferred</b>\n\n💸 From referral: <b>{amount} ₽</b>\n💵 Balance: <b>{bal} ₽</b>',
'ref_withdraw_card_ok':'✅ <b>Withdrawal request created</b>\n\n💳 Amount: <b>{amount} ₽</b>\n🔢 Request: <b>#{wid}</b>',
'ref_history_title':'📜 <b>Withdrawal history</b>','ref_history_empty':'📜 <i>No withdrawals yet.</i>',
'promo_ask':'🎁 <b>Enter promo code:</b>','promo_ok':'🎉 Promo activated!',
'promo_credited':'Credited: <b>+{n}</b> coins','support_title':'🆘 <b>Support</b>',
'support_open_exists':'You have an open ticket <b>#{tid}</b>.','support_desc':'Describe your issue.',
'support_new':'✍️ New ticket','support_my':'📋 My tickets',
'support_continue':'💬 Continue ticket #{tid}','support_create_ask':'✍️ <b>Describe the issue</b>:',
'support_created':'✅ <b>Ticket #{tid} created.</b>','support_none':'📋 You have no tickets yet.',
'support_my_title':'📋 <b>Your tickets</b>','help_title':'ℹ️ <b>Help</b>',
'help_text':'🎨 <b>Create image</b> — <b>free</b>, once per 5 min.\n\n💎 <b>Premium</b> — faster, priority.\n\n💰 <b>Profile</b> — stats and coins.\n\n💝 <b>Donate</b> — if you want.\n\n🎰 <b>Roulette</b> — free coins weekly.\n\n📜 <b>History</b> — generations.\n\n👥 <b>Invite</b> — {percent}% of donations.\n\n🎁 <b>Promo</b> — bonus code.\n\n🆘 <b>Support</b> — ticket.\n\n✨ <b>Inline</b> — @{bot} prompt in any chat.',
'free_gen':'🎨 <b>Free</b>',
'create_prompt':'🎨 <b>Write a description:</b>\n\nMax 4000 chars.',
'checking':'🔎 Checking…','blocked':'❌ <b>Request blocked.</b>','choose_size':'📐 <b>Choose size:</b>',
'size_1024':'🟦 1024×1024','confirm_title':'🎨 <b>Confirm request</b>','confirm_create':'✅ Create',
'queue_title':'⏳ <b>In queue</b>','queue_pos':'Position','queue_cancel':'❌ Cancel',
'in_progress':'🎨 <b>Generating…</b>\nUsually 30–90 sec.\nLimit: {limit}.','done_title':'✅ <b>Done!</b>',
'time_label':'⏱ Time','left_coins':'💰 Coins','timeout':'⏱ Limit exceeded ({limit}). Try again.',
'error_gen':'❌ Generation error. Try again.',
'cooldown':'⏱ <b>Next generation in {time}</b>\n\nLimit: 1 per 5 min.\n\n💎 <b>Premium</b> — 30 sec cooldown → /premium',
'insufficient_coins':'❌ Not enough coins.',
'terms_title':'📄 <b>Before you start</b>','terms_lead':'Please review the documents:',
'terms_privacy':'🔒 Privacy Policy','terms_offer':'📜 Terms of Service',
'terms_note':'You must accept the terms to use the bot.',
'terms_accept':'✅ I agree to the terms','terms_reject':'❌ Decline','terms_accepted':'✅ Terms accepted.',
'terms_rejected':'❌ You declined the terms.\n\nAccess closed. If you change your mind — /start.',
'terms_first':'❌ Please accept the terms first. /start','banned_access':'⛔ Access denied.',
'banned_title':'⛔ <b>Access restricted.</b>','banned_reason':'Reason','menu_hint':'Choose an action in the menu 👇',
'lang_title':'🌐 <b>Language selection</b>','lang_current':'Current language','lang_switched':'✅ Language: {lang}',
'rate_limit':'⏱ Too often. Wait {sec} more sec.','not_enough_rub':'❌ Not enough rubles.',
'min_exchange':'Minimum for exchange','you_have':'You have','ticket_msg_added':'📩 Message added to ticket #{tid}.',
'ticket_closed':'🔒 Ticket #{tid} closed.','support_reply':'💬 <b>Support reply (ticket #{tid}):</b>',
'reply_here':'Reply here to continue.','roulette_title':'🎰 <b>Roulette</b>',
'roulette_rules':'Roulette is available <b>once a week</b> (Mon–Sun).\n\nPossible prizes: <b>0, 1, 2, 3, 5, 10</b> coins.',
'roulette_spin':'🎰 Spin','roulette_spinning':'🎰 <b>Spinning…</b>','roulette_won':'🎉 <b>You won {n} 🪙!</b>',
'roulette_empty':'💨 <b>Empty.</b> No luck today.','roulette_done':'✅ Come back next week!',
'roulette_already_this_week':'✅ You already spun the roulette this week.\n\nNext attempt — on Monday.',
'new_user_limit':'🛡 New account limit. Try later.',
'share_btn':'📤 Share',
'donate_thanks':'💝 <b>Thank you for your support!</b>\n\n⭐ Stars: <b>{stars}</b>\n🎁 Coins credited: <b>+{coins}</b> 🪙\n\n<i>Generation is free anyway — this is just a thank you.</i>'}}

# ═══════════ DB ═══════════
_db=None
def db():
    global _db
    if _db is None:
        _db=sqlite3.connect(DB,check_same_thread=False)
        _db.row_factory=sqlite3.Row
    return _db

_lang_cache={}
_settings_cache={}

def init_db():
    c=db()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,username TEXT,full_name TEXT,
            balance INTEGER NOT NULL DEFAULT 0,rub_balance INTEGER NOT NULL DEFAULT 0,
            ref_balance INTEGER NOT NULL DEFAULT 0,created_at TEXT,last_seen TEXT,
            terms_accepted INTEGER NOT NULL DEFAULT 0,banned INTEGER NOT NULL DEFAULT 0,
            ban_reason TEXT,banned_at TEXT,banned_by INTEGER,referred_by INTEGER,
            ref_reward_given INTEGER NOT NULL DEFAULT 0,lang TEXT DEFAULT 'ru');
        CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,
            prompt TEXT,size TEXT,status TEXT,created_at TEXT,file_id TEXT,elapsed REAL);
        CREATE TABLE IF NOT EXISTS tickets(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',created_at TEXT,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS ticket_messages(id INTEGER PRIMARY KEY AUTOINCREMENT,ticket_id INTEGER NOT NULL,
            sender TEXT NOT NULL,text TEXT,photo_file_id TEXT,created_at TEXT);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
        CREATE TABLE IF NOT EXISTS referrals(id INTEGER PRIMARY KEY AUTOINCREMENT,inviter_id INTEGER,
            invited_id INTEGER,reward_paid INTEGER NOT NULL DEFAULT 0,created_at TEXT);
        CREATE TABLE IF NOT EXISTS promo_codes(code TEXT PRIMARY KEY,amount INTEGER NOT NULL,
            uses_left INTEGER NOT NULL,total_uses INTEGER NOT NULL,expires_at TEXT,
            created_by INTEGER,created_at TEXT);
        CREATE TABLE IF NOT EXISTS promo_uses(id INTEGER PRIMARY KEY AUTOINCREMENT,code TEXT,
            user_id INTEGER,created_at TEXT);
        CREATE TABLE IF NOT EXISTS topups(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,method TEXT,created_at TEXT,by_admin INTEGER);
        CREATE TABLE IF NOT EXISTS ref_earnings(id INTEGER PRIMARY KEY AUTOINCREMENT,referrer_id INTEGER NOT NULL,
            referred_id INTEGER NOT NULL,amount INTEGER NOT NULL,source_topup_id INTEGER,created_at TEXT);
        CREATE TABLE IF NOT EXISTS admins(user_id INTEGER PRIMARY KEY,added_by INTEGER,added_at TEXT);
        CREATE TABLE IF NOT EXISTS banners(key TEXT PRIMARY KEY,file_id TEXT NOT NULL,updated_at TEXT);
        CREATE TABLE IF NOT EXISTS banners_cache(key TEXT PRIMARY KEY,file_id TEXT NOT NULL,cached_at TEXT);
        CREATE TABLE IF NOT EXISTS apis(id INTEGER PRIMARY KEY AUTOINCREMENT,type TEXT NOT NULL,name TEXT,
            base_url TEXT NOT NULL,api_key TEXT NOT NULL,model TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1,
            priority INTEGER NOT NULL DEFAULT 100,created_at TEXT);
        CREATE TABLE IF NOT EXISTS roulette_spins(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,
            prize INTEGER NOT NULL,spun_at TEXT);
        CREATE TABLE IF NOT EXISTS stars_payments(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,
            stars INTEGER,rub INTEGER,charge_id TEXT UNIQUE,created_at TEXT);
        CREATE TABLE IF NOT EXISTS adv_partners(user_id INTEGER PRIMARY KEY,code TEXT UNIQUE NOT NULL,
            percent INTEGER NOT NULL DEFAULT 20,created_at TEXT);
        CREATE TABLE IF NOT EXISTS inline_prompts(id TEXT PRIMARY KEY,user_id INTEGER,prompt TEXT,created_at TEXT);
        CREATE TABLE IF NOT EXISTS ref_withdrawals(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,method TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',
            card TEXT,created_at TEXT,processed_at TEXT,processed_by INTEGER,note TEXT);
        CREATE TABLE IF NOT EXISTS premium(user_id INTEGER PRIMARY KEY,expires_at TEXT,bought_at TEXT);
    ''')
    for stmt in [
        'ALTER TABLE users ADD COLUMN banned INTEGER NOT NULL DEFAULT 0',
        'ALTER TABLE users ADD COLUMN ban_reason TEXT',
        'ALTER TABLE users ADD COLUMN banned_at TEXT','ALTER TABLE users ADD COLUMN banned_by INTEGER',
        'ALTER TABLE users ADD COLUMN referred_by INTEGER',
        'ALTER TABLE users ADD COLUMN ref_reward_given INTEGER NOT NULL DEFAULT 0',
        'ALTER TABLE users ADD COLUMN rub_balance INTEGER NOT NULL DEFAULT 0',
        'ALTER TABLE users ADD COLUMN ref_balance INTEGER NOT NULL DEFAULT 0',
        'ALTER TABLE users ADD COLUMN lang TEXT DEFAULT "ru"',
        'ALTER TABLE history ADD COLUMN file_id TEXT','ALTER TABLE history ADD COLUMN elapsed REAL',
        'ALTER TABLE ticket_messages ADD COLUMN photo_file_id TEXT',
        'CREATE INDEX IF NOT EXISTS idx_history_user ON history(user_id,id DESC)',
        'CREATE INDEX IF NOT EXISTS idx_topups_user_date ON topups(user_id,created_at)',
        'CREATE INDEX IF NOT EXISTS idx_roulette_user_date ON roulette_spins(user_id,spun_at)']:
        try: c.execute(stmt)
        except sqlite3.OperationalError: pass
    for k,v in {'log_level':'2','max_concurrent':'1','image_cost':'0','start_balance':'10',
        'coin_rate':'2','ref_percent':'10','timeout':str(TIMEOUT_DEFAULT),
        'rate_limit_count':'10','rate_limit_window':'60',
        'premium_stars':str(PREMIUM_STARS),'premium_days':str(PREMIUM_DAYS),
        'premium_cooldown':str(PREMIUM_COOLDOWN),'rush_cost':str(RUSH_COST)}.items():
        c.execute('INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)',(k,v))
    c.commit()
    seed_apis()

def seed_apis():
    c=db()
    if c.execute('SELECT COUNT(*) AS n FROM apis').fetchone()['n']>0: return
    now=datetime.now().isoformat(timespec='seconds')
    for typ,name,url,key,model,pr in SEED_APIS:
        try:
            c.execute('INSERT INTO apis(type,name,base_url,api_key,model,active,priority,created_at) VALUES(?,?,?,?,?,1,?,?)',
                (typ,name,url,key,model,pr,now))
        except: pass
    c.commit()
    log.info('Seeded %s APIs',len(SEED_APIS))

def setting(key,default=None):
    if key in _settings_cache: return _settings_cache[key]
    r=db().execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
    v=r['value'] if r else default
    if v is not None: _settings_cache[key]=v
    return v
def set_setting(key,value):
    c=db(); c.execute('INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)',(key,str(value))); c.commit()
    _settings_cache[key]=str(value)
def get_timeout():
    try: return int(setting('timeout',str(TIMEOUT_DEFAULT)))
    except: return TIMEOUT_DEFAULT
def coin_rate():
    try: return max(1,int(setting('coin_rate','2')))
    except: return 2
def ref_percent():
    try: return max(0,int(setting('ref_percent','10')))
    except: return 10
def rate_limit_count():
    try: return max(1,int(setting('rate_limit_count','10')))
    except: return 10
def rate_limit_window():
    try: return max(5,int(setting('rate_limit_window','60')))
    except: return 60

# ═══════════ PREMIUM ═══════════
def premium_until(uid):
    r=db().execute('SELECT expires_at FROM premium WHERE user_id=?',(uid,)).fetchone()
    if not r or not r['expires_at']: return None
    try: return datetime.fromisoformat(r['expires_at'])
    except: return None
def is_premium(uid):
    exp=premium_until(uid)
    return bool(exp and exp>datetime.now())
def premium_days_left(uid):
    exp=premium_until(uid)
    if not exp or exp<=datetime.now(): return 0
    return max(0,(exp-datetime.now()).days)
def activate_premium(uid,days=None):
    days=days or int(setting('premium_days',str(PREMIUM_DAYS)))
    now=datetime.now()
    cur=premium_until(uid)
    base=cur if cur and cur>now else now
    new_exp=base+timedelta(days=days)
    c=db()
    c.execute('INSERT OR REPLACE INTO premium(user_id,expires_at,bought_at) VALUES(?,?,?)',
        (uid,new_exp.isoformat(timespec='seconds'),now.isoformat(timespec='seconds')))
    c.commit()
    return new_exp

# ═══════════ BANNERS ═══════════
def banner_file(key):
    p=os.path.join(BANNERS_DIR,f'{key}.png')
    return p if os.path.isfile(p) else None
def db_has_banner(key):
    return bool(db().execute('SELECT 1 FROM banners WHERE key=?',(key,)).fetchone())
def banner_cache_get(key):
    r=db().execute('SELECT file_id FROM banners_cache WHERE key=?',(key,)).fetchone()
    return r['file_id'] if r else None
def banner_cache_set(key,fid):
    c=db(); c.execute('INSERT OR REPLACE INTO banners_cache(key,file_id,cached_at) VALUES(?,?,?)',
        (key,fid,datetime.now().isoformat(timespec='seconds'))); c.commit()
def banner_cache_clear(key=None):
    c=db()
    if key: c.execute('DELETE FROM banners_cache WHERE key=?',(key,))
    else: c.execute('DELETE FROM banners_cache')
    c.commit()
def get_banner(key):
    r=db().execute('SELECT file_id FROM banners WHERE key=?',(key,)).fetchone()
    if r: return ('id',r['file_id'])
    cached=banner_cache_get(key)
    if cached: return ('id',cached)
    p=banner_file(key)
    if p: return ('file',p)
    return None
def set_banner(key,fid):
    c=db(); c.execute('INSERT OR REPLACE INTO banners(key,file_id,updated_at) VALUES(?,?,?)',
        (key,fid,datetime.now().isoformat(timespec='seconds'))); c.commit()
def delete_banner(key):
    c=db(); c.execute('DELETE FROM banners WHERE key=?',(key,)); c.commit()
    banner_cache_clear(key)
def list_banners():
    have={r['key'] for r in db().execute('SELECT key FROM banners').fetchall()}
    if os.path.isdir(BANNERS_DIR):
        for f in os.listdir(BANNERS_DIR):
            if f.endswith('.png'):
                k=f[:-4]
                if k in BANNER_KEYS: have.add(k)
    return have
def banner_source(key):
    has_db=db_has_banner(key); has_file=bool(banner_file(key)); has_cache=bool(banner_cache_get(key))
    parts=[]
    if has_db: parts.append('✅ БД')
    if has_file: parts.append('📁 файл')
    if has_cache: parts.append('⚡ кэш')
    return ' + '.join(parts) if parts else '⬜ нет'
def _strip_header(bkey,text):
    if not bkey: return text
    if not get_banner(bkey): return text
    lines=text.split('\n')
    if len(lines)>=2 and lines[1].strip() and set(lines[1].strip())<={'━'}:
        return '\n'.join(lines[2:]).lstrip('\n')
    return text
async def upload_banner_files(app):
    if not os.path.isdir(BANNERS_DIR): return
    for key in BANNER_KEYS:
        p=banner_file(key)
        if not p: continue
        if db_has_banner(key): continue
        if banner_cache_get(key): continue
        try:
            msg=await app.bot.send_photo(chat_id=ADMIN_ID,photo=open(p,'rb'),
                caption=f'⬆️ Кэш баннера: <b>{BANNER_KEYS[key]}</b> ({key})',parse_mode=ParseMode.HTML)
            if msg.photo:
                banner_cache_set(key,msg.photo[-1].file_id)
                try: await msg.delete()
                except: pass
                log.info('Banner %s cached',key)
        except Exception as e:
            log.warning('banner cache %s: %s',key,e)

# ═══════════ SCREENS ═══════════
async def show_screen(q,context,uid,bkey,text,kb):
    msg=q.message
    banner=get_banner(bkey) if bkey else None
    use_photo=bool(banner) and len(text)<=CAPTION_MAX
    was_photo=bool(msg.photo)
    if use_photo:
        text=_strip_header(bkey,text)
        try:
            btype,bval=banner
            if btype=='id': media=InputMediaPhoto(media=bval,caption=text,parse_mode=ParseMode.HTML)
            else: media=InputMediaPhoto(media=open(bval,'rb'),caption=text,parse_mode=ParseMode.HTML)
            await msg.edit_media(media=media,reply_markup=kb); return
        except Exception as e: log.warning('edit_media: %s',e)
    if was_photo:
        try: await msg.delete()
        except: pass
        try:
            if use_photo:
                btype,bval=banner
                if btype=='id': await context.bot.send_photo(msg.chat_id,bval,caption=text,parse_mode=ParseMode.HTML,reply_markup=kb)
                else: await context.bot.send_photo(msg.chat_id,open(bval,'rb'),caption=text,parse_mode=ParseMode.HTML,reply_markup=kb)
            else: await context.bot.send_message(msg.chat_id,text,parse_mode=ParseMode.HTML,reply_markup=kb)
        except Exception as e: log.warning('send fb: %s',e)
        return
    try: await msg.edit_text(text,parse_mode=ParseMode.HTML,reply_markup=kb)
    except Exception as e:
        log.warning('edit_text: %s',e)
        try: await msg.delete()
        except: pass
        try:
            if use_photo:
                btype,bval=banner
                if btype=='id': await context.bot.send_photo(msg.chat_id,bval,caption=text,parse_mode=ParseMode.HTML,reply_markup=kb)
                else: await context.bot.send_photo(msg.chat_id,open(bval,'rb'),caption=text,parse_mode=ParseMode.HTML,reply_markup=kb)
            else: await context.bot.send_message(msg.chat_id,text,parse_mode=ParseMode.HTML,reply_markup=kb)
        except: pass
async def send_screen(update,uid,bkey,text,kb):
    banner=get_banner(bkey) if bkey else None
    use_photo=bool(banner) and len(text)<=CAPTION_MAX
    if use_photo: text=_strip_header(bkey,text)
    chat=update.effective_chat
    if use_photo:
        btype,bval=banner
        try:
            if btype=='id': await chat.send_photo(bval,caption=text,parse_mode=ParseMode.HTML,reply_markup=kb)
            else: await chat.send_photo(open(bval,'rb'),caption=text,parse_mode=ParseMode.HTML,reply_markup=kb)
            return
        except Exception as e: log.warning('send_photo: %s',e)
    await chat.send_message(text,parse_mode=ParseMode.HTML,reply_markup=kb)

# ═══════════ API MANAGER ═══════════
def api_list(typ=None):
    if typ: return db().execute('SELECT * FROM apis WHERE type=? ORDER BY priority ASC,id ASC',(typ,)).fetchall()
    return db().execute('SELECT * FROM apis ORDER BY type,priority ASC,id ASC').fetchall()
def api_get(aid):
    return db().execute('SELECT * FROM apis WHERE id=?',(aid,)).fetchone()
def api_add(typ,name,url,key,model,pr=100):
    c=db()
    cur=c.execute('INSERT INTO apis(type,name,base_url,api_key,model,active,priority,created_at) VALUES(?,?,?,?,?,1,?,?)',
        (typ,name,url,key,model,pr,datetime.now().isoformat(timespec='seconds')))
    c.commit(); return cur.lastrowid
def api_del(aid):
    c=db(); c.execute('DELETE FROM apis WHERE id=?',(aid,)); c.commit()
def api_toggle(aid):
    c=db(); r=c.execute('SELECT active FROM apis WHERE id=?',(aid,)).fetchone()
    if r: c.execute('UPDATE apis SET active=? WHERE id=?',(0 if r['active'] else 1,aid)); c.commit()
def api_set_priority(aid,pr):
    c=db(); c.execute('UPDATE apis SET priority=? WHERE id=?',(pr,aid)); c.commit()
def api_active(typ):
    rows=db().execute('SELECT * FROM apis WHERE type=? AND active=1 ORDER BY priority ASC,id ASC',(typ,)).fetchall()
    if rows: return list(rows)
    if typ=='image': return [{'id':0,'name':'env','base_url':API_BASE,'api_key':API_KEY,'model':IMAGE_MODEL}]
    return [{'id':0,'name':'env','base_url':API_BASE,'api_key':API_KEY,'model':MODERATION_MODEL}]

async def fetch_api_balance(api):
    try:
        headers={'Authorization':'Bearer '+api['api_key'],'Content-Type':'application/json'}
        async with httpx.AsyncClient(timeout=20) as c:
            r=await c.get(api['base_url']+'/balance',headers=headers)
        if r.status_code==404: return '❌ /balance не найден'
        if r.status_code==401: return '❌ 401 неверный ключ'
        r.raise_for_status()
        data=r.json()
        cands=[data.get('balance'),data.get('available'),data.get('total_available'),
               data.get('credits'),data.get('amount'),data.get('value')]
        if isinstance(data.get('data'),dict):
            d=data['data']
            cands+=[d.get('balance'),d.get('available'),d.get('total_available'),
                    d.get('credits'),d.get('amount'),d.get('value')]
        for v in cands:
            if v is not None and not isinstance(v,(dict,list)):
                return f'💰 <b>{v}</b>'
        return f'⚠️ <code>{html.escape(r.text[:300])}</code>'
    except httpx.HTTPStatusError as e: return f'❌ HTTP {e.response.status_code}'
    except Exception as e: return f'❌ {html.escape(str(e)[:100])}'

async def collect_balances():
    rows=api_list()
    if not rows: return '📭 Нет API.'
    lines=['💳 <b>Балансы API</b>','━━━━━━━━━━━━━━━━━━━━','']
    for r in rows:
        icon='🖼' if r['type']=='image' else '🧠'
        status='✅' if r['active'] else '⚪'
        lines.append(f'{status} {icon} <b>#{r["id"]} {html.escape(r["name"] or "—")}</b>')
        if not r['active']:
            lines.append('   ⚪ выключен'); lines.append(''); continue
        bal=await fetch_api_balance(r)
        lines.append(f'   {bal}'); lines.append('')
    return '\n'.join(lines).rstrip()

# ═══════════ STARS ═══════════
def stars_payment_exists(cid):
    return bool(db().execute('SELECT 1 FROM stars_payments WHERE charge_id=?',(cid,)).fetchone())
def add_stars_payment(uid,stars,rub,cid):
    c=db(); c.execute('INSERT INTO stars_payments(user_id,stars,rub,charge_id,created_at) VALUES(?,?,?,?,?)',
        (uid,stars,rub,cid,datetime.now().isoformat(timespec='seconds'))); c.commit()

# ═══════════ ROULETTE ═══════════
def _iso_week_bounds(dt=None):
    dt=dt or datetime.now()
    monday=(dt-timedelta(days=dt.weekday())).replace(hour=0,minute=0,second=0,microsecond=0)
    sunday=monday+timedelta(days=7)-timedelta(seconds=1)
    return monday,sunday
def _iso_week_key(dt=None):
    dt=dt or datetime.now()
    y,w,_=dt.isocalendar()
    return f'{y}-W{w:02d}'
def roulette_spun_this_week(uid):
    start,end=_iso_week_bounds()
    r=db().execute('SELECT 1 FROM roulette_spins WHERE user_id=? AND spun_at>=? AND spun_at<=? LIMIT 1',
        (uid,start.isoformat(timespec='seconds'),end.isoformat(timespec='seconds'))).fetchone()
    return bool(r)
def roulette_status(uid):
    week=_iso_week_key()
    if roulette_spun_this_week(uid):
        return {'can_spin':False,'reason':'already','week_key':week}
    return {'can_spin':True,'reason':'ok','week_key':week}
def roulette_spin(uid):
    total=sum(w for _,w in ROULETTE_PRIZES)
    r=random.randint(1,total); acc=0; prize=0
    for coins,w in ROULETTE_PRIZES:
        acc+=w
        if r<=acc: prize=coins; break
    c=db(); c.execute('INSERT INTO roulette_spins(user_id,prize,spun_at) VALUES(?,?,?)',
        (uid,prize,datetime.now().isoformat(timespec='seconds'))); c.commit()
    if prize>0: change_balance(uid,prize)
    return prize

# ═══════════ RATE LIMITS ═══════════
_rate_log={}
_gen_cooldown={}
def check_rate(uid):
    limit=rate_limit_count(); window=rate_limit_window(); now=time.time()
    times=[x for x in _rate_log.get(uid,[]) if now-x<window]
    if len(times)>=limit:
        wait=int(window-(now-times[0]))+1; _rate_log[uid]=times; return False,wait
    times.append(now); _rate_log[uid]=times; return True,0
def check_gen_cooldown(uid):
    now=time.time()
    cd=GEN_COOLDOWN
    if is_premium(uid):
        try: cd=int(setting('premium_cooldown',str(PREMIUM_COOLDOWN)))
        except: cd=PREMIUM_COOLDOWN
    last=_gen_cooldown.get(uid,0)
    if now-last<cd:
        return False,int(cd-(now-last))+1
    _gen_cooldown[uid]=now
    return True,0
_new_user_log={}
def is_new_account(uid):
    r=db().execute('SELECT created_at FROM users WHERE user_id=?',(uid,)).fetchone()
    if not r or not r['created_at']: return False
    try:
        created=datetime.fromisoformat(r['created_at'])
        return (datetime.now()-created) < timedelta(hours=NEW_USER_HOURS)
    except: return False
def check_new_user_limit(uid):
    if not is_new_account(uid): return True,0
    now=time.time()
    times=[x for x in _new_user_log.get(uid,[]) if now-x<NEW_USER_LIMIT_WINDOW]
    if len(times)>=NEW_USER_LIMIT_COUNT:
        wait=int(NEW_USER_LIMIT_WINDOW-(now-times[0]))+1
        _new_user_log[uid]=times
        return False,wait
    times.append(now); _new_user_log[uid]=times
    return True,0

# ═══════════ ADMINS ═══════════
def is_admin(uid):
    if uid==ADMIN_ID: return True
    return bool(db().execute('SELECT 1 FROM admins WHERE user_id=?',(uid,)).fetchone())
def add_admin(uid,by):
    c=db(); c.execute('INSERT OR IGNORE INTO admins(user_id,added_by,added_at) VALUES(?,?,?)',
        (uid,by,datetime.now().isoformat(timespec='seconds'))); c.commit()
def remove_admin(uid):
    if uid==ADMIN_ID: return False
    c=db(); c.execute('DELETE FROM admins WHERE user_id=?',(uid,)); c.commit(); return True
def list_admins():
    return db().execute('SELECT user_id,added_by,added_at FROM admins ORDER BY added_at').fetchall()

# ═══════════ ADV ═══════════
def adv_get_by_uid(uid):
    return db().execute('SELECT * FROM adv_partners WHERE user_id=?',(uid,)).fetchone()
def adv_get_by_code(code):
    return db().execute('SELECT * FROM adv_partners WHERE code=?',(code,)).fetchone()
def adv_create(uid,code,percent=None):
    pct=percent if percent is not None else ADV_DEFAULT_PERCENT
    c=db()
    try:
        c.execute('INSERT INTO adv_partners(user_id,code,percent,created_at) VALUES(?,?,?,?)',
            (uid,code,pct,datetime.now().isoformat(timespec='seconds'))); c.commit()
        return True
    except sqlite3.IntegrityError: return False
def adv_delete(code):
    c=db(); c.execute('DELETE FROM adv_partners WHERE code=?',(code,)); c.commit()
def adv_list():
    return db().execute('SELECT * FROM adv_partners ORDER BY created_at DESC').fetchall()

# ═══════════ INLINE PROMPTS ═══════════
def inline_prompt_save(uid,prompt):
    sid=uuid.uuid4().hex[:12]
    c=db(); c.execute('INSERT INTO inline_prompts(id,user_id,prompt,created_at) VALUES(?,?,?,?)',
        (sid,uid,prompt,datetime.now().isoformat(timespec='seconds'))); c.commit()
    return sid
def inline_prompt_get(sid):
    return db().execute('SELECT * FROM inline_prompts WHERE id=?',(sid,)).fetchone()
def inline_prompt_purge():
    cutoff=(datetime.now()-timedelta(hours=1)).isoformat(timespec='seconds')
    c=db(); c.execute('DELETE FROM inline_prompts WHERE created_at<?',(cutoff,)); c.commit()

# ═══════════ USERS ═══════════
def ensure_user(u):
    c=db(); now=datetime.now().isoformat(timespec='seconds')
    r=c.execute('SELECT user_id FROM users WHERE user_id=?',(u.id,)).fetchone()
    if r is None:
        sb=int(setting('start_balance','10'))
        c.execute('INSERT INTO users(user_id,username,full_name,balance,created_at,last_seen,lang) VALUES(?,?,?,?,?,?,?)',
            (u.id,u.username or '',u.full_name or '',sb,now,now,'ru'))
    else:
        c.execute('UPDATE users SET username=?,full_name=?,last_seen=? WHERE user_id=?',
            (u.username or '',u.full_name or '',now,u.id))
    c.commit()
def ensure_user_by_id(uid):
    c=db(); now=datetime.now().isoformat(timespec='seconds')
    r=c.execute('SELECT user_id FROM users WHERE user_id=?',(uid,)).fetchone()
    if r is None:
        sb=int(setting('start_balance','10'))
        c.execute('INSERT INTO users(user_id,username,full_name,balance,created_at,last_seen,lang) VALUES(?,?,?,?,?,?,?)',
            (uid,'','',sb,now,now,'ru'))
    c.commit()
def get_user(uid):
    return db().execute('SELECT * FROM users WHERE user_id=?',(uid,)).fetchone()
def balance(uid):
    r=db().execute('SELECT balance FROM users WHERE user_id=?',(uid,)).fetchone()
    return r['balance'] if r else 0
def rub_balance(uid):
    r=db().execute('SELECT rub_balance FROM users WHERE user_id=?',(uid,)).fetchone()
    return r['rub_balance'] if r else 0
def ref_balance(uid):
    r=db().execute('SELECT ref_balance FROM users WHERE user_id=?',(uid,)).fetchone()
    return r['ref_balance'] if r else 0
def change_balance(uid,n):
    c=db(); c.execute('UPDATE users SET balance=balance+? WHERE user_id=?',(n,uid)); c.commit()
def change_ref_balance(uid,n):
    c=db(); c.execute('UPDATE users SET ref_balance=ref_balance+? WHERE user_id=?',(n,uid)); c.commit()
def set_balance_exact(uid,n):
    c=db(); c.execute('UPDATE users SET balance=? WHERE user_id=?',(n,uid)); c.commit()
def set_rub_exact(uid,n):
    c=db(); c.execute('UPDATE users SET rub_balance=? WHERE user_id=?',(n,uid)); c.commit()
def has_accepted(uid):
    r=db().execute('SELECT terms_accepted FROM users WHERE user_id=?',(uid,)).fetchone()
    return bool(r and r['terms_accepted'])
def accept_terms(uid):
    c=db(); c.execute('UPDATE users SET terms_accepted=1 WHERE user_id=?',(uid,)); c.commit()
def is_banned(uid):
    r=db().execute('SELECT banned FROM users WHERE user_id=?',(uid,)).fetchone()
    return bool(r and r['banned'])
def set_ban(uid,val,reason=None,by=None):
    c=db()
    if val:
        c.execute('UPDATE users SET banned=1,ban_reason=?,banned_at=?,banned_by=? WHERE user_id=?',
            (reason or '',datetime.now().isoformat(timespec='seconds'),by,uid))
    else:
        c.execute('UPDATE users SET banned=0,ban_reason=NULL,banned_at=NULL,banned_by=NULL WHERE user_id=?',(uid,))
    c.commit()
def list_banned(limit=50):
    return db().execute('SELECT user_id,username,full_name,ban_reason,banned_at FROM users WHERE banned=1 ORDER BY banned_at DESC LIMIT ?',(limit,)).fetchall()
def add_history(uid,prompt,size,status,file_id=None,elapsed=None):
    c=db(); c.execute('INSERT INTO history(user_id,prompt,size,status,created_at,file_id,elapsed) VALUES(?,?,?,?,?,?,?)',
        (uid,prompt,size,status,datetime.now().isoformat(timespec='seconds'),file_id,elapsed)); c.commit()
def user_history(uid,limit=10):
    return db().execute('SELECT prompt,size,status,created_at,file_id,elapsed FROM history WHERE user_id=? ORDER BY id DESC LIMIT ?',(uid,limit)).fetchall()
def user_history_total(uid):
    r=db().execute('SELECT COUNT(*) AS n FROM history WHERE user_id=?',(uid,)).fetchone()
    return r['n'] if r else 0
def user_history_page(uid,off,lim):
    return db().execute('SELECT id,prompt,size,status,created_at,file_id,elapsed FROM history WHERE user_id=? ORDER BY id DESC LIMIT ? OFFSET ?',(uid,lim,off)).fetchall()
def get_history_item(uid,hid):
    return db().execute('SELECT id,prompt,size,status,created_at,file_id,elapsed FROM history WHERE id=? AND user_id=?',(hid,uid)).fetchone()
def gen_time_stats():
    r=db().execute('SELECT AVG(elapsed) AS a,MIN(elapsed) AS mn,MAX(elapsed) AS mx,COUNT(elapsed) AS c FROM history WHERE status="success" AND elapsed IS NOT NULL').fetchone()
    return (r['a'] or 0,r['mn'] or 0,r['mx'] or 0,r['c'] or 0)

# ═══════════ REF WITHDRAWALS ═══════════
def ref_withdrawals_list(uid,limit=20):
    return db().execute('SELECT * FROM ref_withdrawals WHERE user_id=? ORDER BY id DESC LIMIT ?',(uid,limit)).fetchall()
def ref_withdrawal_create(uid,amount,method,card=None):
    c=db()
    cur=c.execute('INSERT INTO ref_withdrawals(user_id,amount,method,status,card,created_at) VALUES(?,?,?,?,?,?)',
        (uid,amount,method,'pending',card,datetime.now().isoformat(timespec='seconds')))
    c.commit(); return cur.lastrowid
def ref_withdrawal_get(wid):
    return db().execute('SELECT * FROM ref_withdrawals WHERE id=?',(wid,)).fetchone()
def ref_withdrawal_set_status(wid,status,by=None,note=None):
    c=db()
    c.execute('UPDATE ref_withdrawals SET status=?,processed_at=?,processed_by=?,note=? WHERE id=?',
        (status,datetime.now().isoformat(timespec='seconds'),by,note,wid)); c.commit()
def ref_withdrawals_pending(limit=50):
    return db().execute('SELECT * FROM ref_withdrawals WHERE status="pending" ORDER BY id DESC LIMIT ?',(limit,)).fetchall()

# ═══════════ RUB / REFS / PROMO ═══════════
def referrer_of(uid):
    r=db().execute('SELECT referred_by FROM users WHERE user_id=?',(uid,)).fetchone()
    return r['referred_by'] if r else None
def referred_by_at_level(uid,lvl):
    cur=uid
    for _ in range(lvl):
        cur=referrer_of(cur)
        if cur is None: return None
    return cur
def topup_rub(uid,amount,method='manual',by_admin=None):
    if amount==0: return []
    c=db(); now=datetime.now().isoformat(timespec='seconds')
    c.execute('UPDATE users SET rub_balance=rub_balance+? WHERE user_id=?',(amount,uid)); c.commit()
    payouts=[]
    if amount>0:
        cur=c.execute('INSERT INTO topups(user_id,amount,method,created_at,by_admin) VALUES(?,?,?,?,?)',
            (uid,amount,method,now,by_admin)); c.commit()
        tid=cur.lastrowid
        l1=referred_by_at_level(uid,1)
        if l1:
            adv=adv_get_by_uid(l1)
            pct=adv['percent'] if adv else REF_L1
            bonus=int(amount*pct/100)
            if bonus>0:
                c.execute('UPDATE users SET ref_balance=ref_balance+? WHERE user_id=?',(bonus,l1))
                c.execute('INSERT INTO ref_earnings(referrer_id,referred_id,amount,source_topup_id,created_at) VALUES(?,?,?,?,?)',
                    (l1,uid,bonus,tid,now)); c.commit()
                payouts.append((l1,1,bonus))
            if not adv:
                l2=referred_by_at_level(uid,2)
                if l2:
                    bonus2=int(amount*REF_L2/100)
                    if bonus2>0:
                        c.execute('UPDATE users SET ref_balance=ref_balance+? WHERE user_id=?',(bonus2,l2))
                        c.execute('INSERT INTO ref_earnings(referrer_id,referred_id,amount,source_topup_id,created_at) VALUES(?,?,?,?,?)',
                            (l2,uid,bonus2,tid,now)); c.commit()
                        payouts.append((l2,2,bonus2))
    return payouts
def exchange_rub_to_coins(uid,rub):
    rate=coin_rate()
    if rub<=0: return False,'bad_amount'
    if rub%rate!=0: return False,'not_multiple'
    coins=rub//rate
    if rub_balance(uid)<rub: return False,'not_enough_rub'
    c=db(); c.execute('UPDATE users SET rub_balance=rub_balance-?,balance=balance+? WHERE user_id=?',(rub,coins,uid)); c.commit()
    return True,coins
def set_referrer(new_uid,ref_id):
    if new_uid==ref_id: return
    u=get_user(new_uid)
    if not u or u['referred_by'] is not None: return
    if not get_user(ref_id): return
    c=db()
    c.execute('UPDATE users SET referred_by=? WHERE user_id=?',(ref_id,new_uid))
    c.execute('INSERT INTO referrals(inviter_id,invited_id,reward_paid,created_at) VALUES(?,?,0,?)',
        (ref_id,new_uid,datetime.now().isoformat(timespec='seconds'))); c.commit()
def ref_stats(uid):
    c=db()
    total=c.execute('SELECT COUNT(*) AS n FROM referrals WHERE inviter_id=?',(uid,)).fetchone()['n']
    earned=c.execute('SELECT COALESCE(SUM(amount),0) AS s FROM ref_earnings WHERE referrer_id=?',(uid,)).fetchone()['s']
    return total,earned
def ref_link(uid):
    return f'https://t.me/{BOT_USERNAME}?start=ref_{uid}'
def adv_link(code):
    return f'https://t.me/{BOT_USERNAME}?start=adv_{code}'
def share_bot_url(uid):
    ref=f'https://t.me/{BOT_USERNAME}?start=ref_{uid}'
    text=quote(f'Зацени что я сделал в @{BOT_USERNAME}! Попробуй тоже 👇')
    return f'https://t.me/share/url?url={ref}&text={text}'
def create_promo(code,amount,uses,days=None,by=None):
    now=datetime.now()
    exp=(now+timedelta(days=days)).isoformat(timespec='seconds') if days else None
    c=db()
    try:
        c.execute('INSERT INTO promo_codes(code,amount,uses_left,total_uses,expires_at,created_by,created_at) VALUES(?,?,?,?,?,?,?)',
            (code,amount,uses,uses,exp,by,now.isoformat(timespec='seconds'))); c.commit()
        return True,None
    except sqlite3.IntegrityError: return False,'exists'
def activate_promo(code,uid):
    c=db(); p=c.execute('SELECT * FROM promo_codes WHERE code=?',(code,)).fetchone()
    if not p: return False,'not_found'
    if p['uses_left']<=0: return False,'exhausted'
    if p['expires_at']:
        try:
            if datetime.fromisoformat(p['expires_at'])<datetime.now(): return False,'expired'
        except: pass
    if c.execute('SELECT 1 FROM promo_uses WHERE code=? AND user_id=?',(code,uid)).fetchone():
        return False,'already_used'
    change_balance(uid,p['amount'])
    c.execute('UPDATE promo_codes SET uses_left=uses_left-1 WHERE code=?',(code,))
    c.execute('INSERT INTO promo_uses(code,user_id,created_at) VALUES(?,?,?)',
        (code,uid,datetime.now().isoformat(timespec='seconds'))); c.commit()
    return True,p['amount']
def list_promos(limit=50):
    return db().execute('SELECT code,amount,uses_left,total_uses,expires_at FROM promo_codes ORDER BY created_at DESC LIMIT ?',(limit,)).fetchall()
def delete_promo(code):
    c=db(); c.execute('DELETE FROM promo_codes WHERE code=?',(code,)); c.commit()
def get_promo(code):
    return db().execute('SELECT * FROM promo_codes WHERE code=?',(code,)).fetchone()

# ═══════════ TICKETS ═══════════
def create_ticket(uid,text=None,photo_id=None):
    now=datetime.now().isoformat(timespec='seconds'); c=db()
    tid=c.execute('INSERT INTO tickets(user_id,status,created_at,updated_at) VALUES(?,?,?,?)',(uid,'open',now,now)).lastrowid
    c.execute('INSERT INTO ticket_messages(ticket_id,sender,text,photo_file_id,created_at) VALUES(?,?,?,?,?)',
        (tid,'user',text,photo_id,now)); c.commit(); return tid
def add_ticket_msg(tid,sender,text=None,photo_id=None):
    now=datetime.now().isoformat(timespec='seconds'); c=db()
    c.execute('INSERT INTO ticket_messages(ticket_id,sender,text,photo_file_id,created_at) VALUES(?,?,?,?,?)',
        (tid,sender,text,photo_id,now))
    c.execute('UPDATE tickets SET updated_at=? WHERE id=?',(now,tid)); c.commit()
def close_ticket(tid):
    c=db(); c.execute('UPDATE tickets SET status=?,updated_at=? WHERE id=?',
        ('closed',datetime.now().isoformat(timespec='seconds'),tid)); c.commit()
def get_ticket(tid):
    return db().execute('SELECT * FROM tickets WHERE id=?',(tid,)).fetchone()
def get_open_ticket(uid):
    r=db().execute('SELECT id FROM tickets WHERE user_id=? AND status="open" ORDER BY id DESC LIMIT 1',(uid,)).fetchone()
    return r['id'] if r else None
def ticket_msgs(tid,limit=50):
    return db().execute('SELECT sender,text,photo_file_id,created_at FROM ticket_messages WHERE ticket_id=? ORDER BY id ASC LIMIT ?',(tid,limit)).fetchall()
def list_user_tickets(uid,limit=10):
    return db().execute('SELECT id,status,updated_at FROM tickets WHERE user_id=? ORDER BY id DESC LIMIT ?',(uid,limit)).fetchall()
def list_open_tickets(limit=30):
    return db().execute('SELECT id,user_id,updated_at FROM tickets WHERE status="open" ORDER BY updated_at DESC LIMIT ?',(limit,)).fetchall()

# ═══════════ I18N ═══════════
def t(uid,key,**kw):
    lang=get_lang(uid); s=TR.get(lang,TR['ru']).get(key) or TR['ru'].get(key) or key
    return s.format(**kw) if kw else s
def get_lang(uid):
    if uid in _lang_cache: return _lang_cache[uid]
    r=db().execute('SELECT lang FROM users WHERE user_id=?',(uid,)).fetchone()
    lang=r['lang'] if r and r['lang'] in LANGS else 'ru'
    _lang_cache[uid]=lang
    return lang
def set_lang(uid,lang):
    if lang not in LANGS: return
    c=db(); c.execute('UPDATE users SET lang=? WHERE user_id=?',(lang,uid)); c.commit()
    _lang_cache[uid]=lang

# ═══════════ KEYBOARDS ═══════════
def kb_menu(uid):
    rows=[
        [InlineKeyboardButton(t(uid,'create_btn'),callback_data='create')],
        [InlineKeyboardButton(t(uid,'premium'),callback_data='premium')],
        [InlineKeyboardButton(t(uid,'balance'),callback_data='balance'),
         InlineKeyboardButton(t(uid,'topup'),callback_data='topup')],
        [InlineKeyboardButton(t(uid,'history'),callback_data='history'),
         InlineKeyboardButton(t(uid,'promo'),callback_data='promo')],
        [InlineKeyboardButton(t(uid,'roulette'),callback_data='roulette'),
         InlineKeyboardButton(t(uid,'ref'),callback_data='ref')],
        [InlineKeyboardButton(t(uid,'support'),callback_data='support'),
         InlineKeyboardButton(t(uid,'help'),callback_data='help')],
        [InlineKeyboardButton(t(uid,'lang'),callback_data='lang')]]
    return InlineKeyboardMarkup(rows)
def kb_done(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(uid,'share_btn'),url=share_bot_url(uid))],
        [InlineKeyboardButton(t(uid,'create_btn'),callback_data='create')],
        [InlineKeyboardButton(t(uid,'balance'),callback_data='balance'),
         InlineKeyboardButton(t(uid,'history'),callback_data='history')],
        [InlineKeyboardButton(t(uid,'back_menu'),callback_data='menu')]])
def kb_done_inline(uid):
    return InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,'share_btn'),url=share_bot_url(uid))]])
def kb_balance(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(uid,'topup'),callback_data='topup'),
         InlineKeyboardButton(t(uid,'exchange_btn'),callback_data='exchange')],
        [InlineKeyboardButton(t(uid,'back_menu'),callback_data='menu')]])
def kb_sizes(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(uid,'size_1024'),callback_data='size:1024x1024')],
        [InlineKeyboardButton('🟧 1536×1024',callback_data='size:1536x1024'),
         InlineKeyboardButton('🟪 1024×1536',callback_data='size:1024x1536')],
        [InlineKeyboardButton(t(uid,'back'),callback_data='menu'),
         InlineKeyboardButton(t(uid,'cancel'),callback_data='cancel')]])
def kb_confirm(uid,tok):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t(uid,'confirm_create'),callback_data='ok:'+tok),
        InlineKeyboardButton(t(uid,'cancel'),callback_data='no:'+tok)]])
def kb_terms(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(uid,'terms_accept'),callback_data='terms:accept')],
        [InlineKeyboardButton(t(uid,'terms_reject'),callback_data='terms:reject')]])
def kb_lang(uid):
    cur=get_lang(uid); rows=[]
    for code,name in LANGS_NAMES.items():
        rows.append([InlineKeyboardButton(('✅ ' if code==cur else '')+name,callback_data=f'lang:set:{code}')])
    rows.append([InlineKeyboardButton(t(uid,'back_menu'),callback_data='menu')])
    return InlineKeyboardMarkup(rows)
def kb_history(uid,page,total):
    ps=HISTORY_PAGE_SIZE; rows=user_history_page(uid,page*ps,ps)
    if not rows:
        return InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,'back_menu'),callback_data='menu')]])
    kr=[]; row=[]
    for i,item in enumerate(rows):
        row.append(InlineKeyboardButton(str(page*ps+i+1),callback_data=f'hist:show:{item["id"]}'))
        if len(row)==5: kr.append(row); row=[]
    if row: kr.append(row)
    tp=(total+ps-1)//ps
    if tp>1:
        nav=[]
        if page>0: nav.append(InlineKeyboardButton('◀️',callback_data=f'hist:p:{page-1}'))
        nav.append(InlineKeyboardButton(f'{page+1}/{tp}',callback_data='hist:noop'))
        if page<tp-1: nav.append(InlineKeyboardButton('▶️',callback_data=f'hist:p:{page+1}'))
        kr.append(nav)
    kr.append([InlineKeyboardButton(t(uid,'back_menu'),callback_data='menu')])
    return InlineKeyboardMarkup(kr)
def kb_support(uid,open_tid=None):
    rows=[]
    if open_tid: rows.append([InlineKeyboardButton(t(uid,'support_continue',tid=open_tid),callback_data=f'support:view:{open_tid}')])
    rows.append([InlineKeyboardButton(t(uid,'support_new'),callback_data='support:new')])
    rows.append([InlineKeyboardButton(t(uid,'support_my'),callback_data='support:list')])
    rows.append([InlineKeyboardButton(t(uid,'back_menu'),callback_data='menu')])
    return InlineKeyboardMarkup(rows)
def kb_ticket_user(uid,tid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('🔒',callback_data=f'support:close:{tid}')],
        [InlineKeyboardButton(t(uid,'back'),callback_data='support')]])
def kb_ticket_admin(tid):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton('✍️ Ответить',callback_data=f'ticket_reply:{tid}'),
        InlineKeyboardButton('🔒 Закрыть',callback_data=f'ticket_close:{tid}')]])
def kb_queue_cancel(uid,jid,can_rush=False):
    rows=[]
    if can_rush and not is_premium(uid):
        try: rc=int(setting('rush_cost',str(RUSH_COST)))
        except: rc=RUSH_COST
        rows.append([InlineKeyboardButton(f'🚀 Ускорить за {rc} 🪙',callback_data=f'q:rush:{jid}')])
    rows.append([InlineKeyboardButton(t(uid,'queue_cancel'),callback_data=f'q:cancel:{jid}')])
    return InlineKeyboardMarkup(rows)
def kb_roulette(uid,can_spin=True):
    rows=[]
    if can_spin: rows.append([InlineKeyboardButton(t(uid,'roulette_spin'),callback_data='roulette:spin')])
    rows.append([InlineKeyboardButton(t(uid,'back_menu'),callback_data='menu')])
    return InlineKeyboardMarkup(rows)
def kb_ref_withdraw(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(uid,'ref_withdraw_to_balance',min_bal=REF_WITHDRAW_TO_BALANCE_MIN),callback_data='refw:bal')],
        [InlineKeyboardButton(t(uid,'ref_withdraw_to_card',min_card=REF_WITHDRAW_TO_CARD_MIN),callback_data='refw:card')],
        [InlineKeyboardButton('📜 История',callback_data='refw:history')],
        [InlineKeyboardButton(t(uid,'back'),callback_data='ref')]])
def kb_admin():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('📊 Статистика',callback_data='adm:stats'),
         InlineKeyboardButton('🆘 Тикеты',callback_data='adm:tickets')],
        [InlineKeyboardButton('👥 Пользователь',callback_data='adm:user'),
         InlineKeyboardButton('📢 Рассылка',callback_data='adm:broadcast')],
        [InlineKeyboardButton('🚫 Бан-лист',callback_data='adm:banlist'),
         InlineKeyboardButton('🎁 Промокоды',callback_data='adm:promos')],
        [InlineKeyboardButton('🖼 Баннеры',callback_data='adm:banners'),
         InlineKeyboardButton('📡 API',callback_data='adm:api')],
        [InlineKeyboardButton('💳 Баланс бота',callback_data='adm:botbalance')],
        [InlineKeyboardButton('🎯 Инфлюенсеры',callback_data='adm:adv'),
         InlineKeyboardButton('💸 Выводы',callback_data='adm:refw')],
        [InlineKeyboardButton('⚙️ Настройки',callback_data='adm:settings')],
        [InlineKeyboardButton('🔄 Обновить',callback_data='adm:main')]])
def kb_admin_adv():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('➕ Назначить',callback_data='adm:adv:new')],
        [InlineKeyboardButton('📋 Список',callback_data='adm:adv:list')],
        [InlineKeyboardButton('◀️ Назад',callback_data='adm:main')]])
def kb_admin_refw():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('📋 Ожидают',callback_data='adm:refw:pending')],
        [InlineKeyboardButton('◀️ Назад',callback_data='adm:main')]])
def kb_admin_banners():
    have=list_banners(); kr=[]
    for k,n in BANNER_KEYS.items():
        kr.append([InlineKeyboardButton(f'{"✅" if k in have else "⬜"} {n}',callback_data=f'adm:ban:view:{k}')])
    kr.append([InlineKeyboardButton('◀️ Назад',callback_data='adm:main')])
    return InlineKeyboardMarkup(kr)
def kb_banner_actions(key):
    in_db=db_has_banner(key)
    rows=[[InlineKeyboardButton('📤 Загрузить/заменить',callback_data=f'adm:ban:upload:{key}')]]
    if in_db: rows.append([InlineKeyboardButton('❌ Удалить из БД',callback_data=f'adm:ban:del:{key}')])
    rows.append([InlineKeyboardButton('◀️ Назад',callback_data='adm:banners')])
    return InlineKeyboardMarkup(rows)
def kb_admin_api():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('🖼 API картинок',callback_data='adm:api:list:image')],
        [InlineKeyboardButton('🧠 API модераторов',callback_data='adm:api:list:mod')],
        [InlineKeyboardButton('◀️ Назад',callback_data='adm:main')]])
def kb_api_list(typ):
    rows=api_list(typ); kr=[]
    for r in rows:
        kr.append([InlineKeyboardButton(f'{"✅" if r["active"] else "⚪"} #{r["id"]} • {r["name"] or "—"} • p{r["priority"]}',
            callback_data=f'adm:api:view:{r["id"]}')])
    kr.append([InlineKeyboardButton('➕ Добавить',callback_data=f'adm:api:add:{typ}')])
    kr.append([InlineKeyboardButton('◀️ Назад',callback_data='adm:api')])
    return InlineKeyboardMarkup(kr)
def kb_api_detail(aid):
    r=api_get(aid)
    if not r: return InlineKeyboardMarkup([[InlineKeyboardButton('◀️ Назад',callback_data='adm:api')]])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('🔄 Вкл/Выкл',callback_data=f'adm:api:toggle:{aid}')],
        [InlineKeyboardButton('🔢 Priority',callback_data=f'adm:api:prio:{aid}')],
        [InlineKeyboardButton('🗑 Удалить',callback_data=f'adm:api:del:{aid}')],
        [InlineKeyboardButton('◀️ Назад',callback_data=f'adm:api:list:{r["type"]}')]])
def kb_admin_settings():
    ll=setting('log_level','2'); ll_names={'0':'выкл','1':'только ошибки','2':'ошибки + генерации','3':'всё'}
    tmo=get_timeout(); tmo_str=f'{tmo//60} мин' if tmo%60==0 else f'{tmo} сек'
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f'📝 Логи: {ll_names.get(ll,ll)}',callback_data='adm:log')],
        [InlineKeyboardButton(f'🎁 Старт: {setting("start_balance","10")} 🪙',callback_data='adm:set:start_balance')],
        [InlineKeyboardButton(f'👷 Параллельно: {setting("max_concurrent","1")}',callback_data='adm:set:max_concurrent')],
        [InlineKeyboardButton(f'⏱ Таймаут: {tmo_str}',callback_data='adm:set:timeout')],
        [InlineKeyboardButton(f'📊 Курс: 1 🪙 = {coin_rate()} ₽',callback_data='adm:set:coin_rate')],
        [InlineKeyboardButton(f'💸 Реф: {ref_percent()}%',callback_data='adm:set:ref_percent')],
        [InlineKeyboardButton(f'⏳ Rate-limit: {rate_limit_count()}/{rate_limit_window()}с',callback_data='adm:ratelimit')],
        [InlineKeyboardButton(f'💎 Premium: {setting("premium_stars",str(PREMIUM_STARS))}⭐ / {setting("premium_days",str(PREMIUM_DAYS))}дн',callback_data='adm:premium')],
        [InlineKeyboardButton('◀️ Назад',callback_data='adm:main')]])
def kb_admin_ratelimit():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f'🔢 Кол-во: {rate_limit_count()}',callback_data='adm:set:rate_limit_count')],
        [InlineKeyboardButton(f'⏱ Окно: {rate_limit_window()} сек',callback_data='adm:set:rate_limit_window')],
        [InlineKeyboardButton('◀️ Назад',callback_data='adm:settings')]])
def kb_admin_premium():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f'⭐ Цена: {setting("premium_stars",str(PREMIUM_STARS))}',callback_data='adm:set:premium_stars')],
        [InlineKeyboardButton(f'📅 Дней: {setting("premium_days",str(PREMIUM_DAYS))}',callback_data='adm:set:premium_days')],
        [InlineKeyboardButton(f'⏱ Кулдаун: {setting("premium_cooldown",str(PREMIUM_COOLDOWN))}с',callback_data='adm:set:premium_cooldown')],
        [InlineKeyboardButton(f'🚀 Ускорение: {setting("rush_cost",str(RUSH_COST))} 🪙',callback_data='adm:set:rush_cost')],
        [InlineKeyboardButton('◀️ Назад',callback_data='adm:settings')]])
def kb_user_card(uid):
    u=get_user(uid); banned=bool(u['banned']); adv=adv_get_by_uid(uid)
    rows=[
        [InlineKeyboardButton('💰 Установить монеты',callback_data=f'adm:setbal:{uid}')],
        [InlineKeyboardButton('🪙 Добавить монеты',callback_data=f'adm:addbal:{uid}')],
        [InlineKeyboardButton('💵 Начислить рубли',callback_data=f'adm:addrub:{uid}')],
        [InlineKeyboardButton('💎 Выдать Premium 30д',callback_data=f'adm:premgive:{uid}')],
        [InlineKeyboardButton('🚫 Разбанить' if banned else '⛔ Забанить',callback_data=f'adm:userban:{uid}')],
        [InlineKeyboardButton('📜 История',callback_data=f'adm:hist:{uid}')]]
    if adv:
        rows.append([InlineKeyboardButton(f'🎯 Инфлюенсер ({adv["percent"]}%) — удалить',callback_data=f'adm:adv:del:{adv["code"]}')])
    else:
        rows.append([InlineKeyboardButton('🎯 Назначить инфлюенсером',callback_data=f'adm:adv:mk:{uid}')])
    rows.append([InlineKeyboardButton('◀️ Назад',callback_data='adm:main')])
    return InlineKeyboardMarkup(rows)
def kb_promos_main():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('➕ Создать промокод',callback_data='adm:promo:new')],
        [InlineKeyboardButton('📋 Список кодов',callback_data='adm:promo:list')],
        [InlineKeyboardButton('◀️ Назад',callback_data='adm:main')]])
def kb_promo_list():
    rows=list_promos(); kb=[]
    for p in rows:
        exp=f' • до {p["expires_at"][:10]}' if p['expires_at'] else ''
        kb.append([InlineKeyboardButton(f'❌ {p["code"]} • {p["amount"]}🪙 • {p["uses_left"]}/{p["total_uses"]}{exp}',
            callback_data=f'adm:promo:del:{p["code"]}')])
    kb.append([InlineKeyboardButton('◀️ Назад',callback_data='adm:promos')])
    return InlineKeyboardMarkup(kb)

# ═══════════ TEXTS ═══════════
def main_text(uid):
    prem=''
    if is_premium(uid):
        prem=f'\n💎 <b>Premium</b>: {premium_days_left(uid)} дн.'
    return (f'{t(uid,"menu_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n'
        f'🪙 {t(uid,"coins")}: <b>{balance(uid)}</b>\n'
        f'🎁 {t(uid,"ref_balance")}: <b>{ref_balance(uid)} ₽</b>{prem}\n\n'
        f'🎨 {t(uid,"gen_cost")}: <b>{t(uid,"free_gen")}</b>\n\n'
        f'{t(uid,"choose_action")}')
TERMS_TPL='{title}\n\n{lead}\n\n🔒 <a href="{privacy}">{privacy_t}</a>\n📜 <a href="{offer}">{offer_t}</a>\n\n{note}'
ADMIN_HELP=('🛠 <b>Админ-команды</b>\n━━━━━━━━━━━━━━━━━━━━\n\n'
    '👥 <code>/user ID</code> • <code>/setbalance</code> • <code>/addbalance</code> • <code>/setrub</code> • <code>/addrub</code>\n\n'
    '💎 <code>/givepremium ID [DAYS]</code> • <code>/unpremium ID</code>\n\n'
    '🚫 <code>/ban ID [прич]</code> • <code>/unban ID</code>\n\n'
    '⚙️ <code>/setrate N</code> • <code>/setref N</code> • <code>/settimeout N</code>\n\n'
    '🖼 <code>/setbanner KEY</code> • <code>/banners</code> • <code>/delbanner KEY</code>\n\n'
    '📡 <code>/apis</code> • 💳 <code>/botbalance</code>\n\n'
    '🎯 <code>/setadv ID CODE [PCT]</code> • <code>/deladv CODE</code> • <code>/advs</code>\n\n'
    '👑 <code>/setadmin ID</code> • <code>/unadmin ID</code> • <code>/admins</code>\n\n'
    '📢 <code>/broadcast ТЕКСТ</code> • <code>/ticket ID</code> • <code>/stats</code> • <code>/admin</code>')

async def alog(app,text,level=2):
    try: cur=int(setting('log_level','2'))
    except: cur=2
    if cur==0 or level>cur: return
    try: await app.bot.send_message(ADMIN_ID,text,parse_mode=ParseMode.HTML)
    except Exception as e: log.warning('alog: %s',e)
def fmt_timeout():
    t_=get_timeout()
    return f'{t_//60} мин' if t_%60==0 else f'{t_} сек'
def fmt_duration(sec):
    s=int(round(sec))
    if s<60: return f'{s} сек'
    m,s=divmod(s,60)
    if m<60: return f'{m} мин {s} сек'
    h,m=divmod(m,60); return f'{h} ч {m} мин'
def fmt_cooldown(sec):
    if sec<60: return f'{sec} сек'
    m,s=divmod(sec,60)
    return f'{m} мин {s} сек' if s else f'{m} мин'

# ═══════════ API CALLS ═══════════
async def moderate(prompt):
    for api in api_active('mod'):
        try:
            payload={'model':api['model'],'messages':[
                {'role':'system','content':'Moderate image prompts. Reply exactly ALLOW if allowed. Otherwise reply BLOCK: short reason.'},
                {'role':'user','content':prompt}],'temperature':0}
            headers={'Authorization':'Bearer '+api['api_key'],'Content-Type':'application/json'}
            async with httpx.AsyncClient(timeout=60) as c:
                r=await c.post(api['base_url']+'/chat/completions',json=payload,headers=headers)
                r.raise_for_status(); d=r.json()
            out=d['choices'][0]['message']['content'].strip()
            if out.upper().startswith('ALLOW'): return True,''
            return False,(out.split(':',1)[1].strip() if ':' in out else 'blocked')
        except Exception as e:
            log.warning('moderate #%s: %s',api.get('id'),e); continue
    return True,''
async def translate_prompt(prompt):
    if not prompt: return prompt
    cyr=sum(1 for c in prompt if '\u0400'<=c<='\u04FF')
    if cyr<len(prompt)*0.2: return prompt
    sys_msg='Translate the user prompt to English for an image generation model. Preserve style, mood, details. Output ONLY the translation.'
    for api in api_active('mod'):
        try:
            payload={'model':api['model'],'messages':[
                {'role':'system','content':sys_msg},
                {'role':'user','content':prompt}],'temperature':0.2}
            headers={'Authorization':'Bearer '+api['api_key'],'Content-Type':'application/json'}
            async with httpx.AsyncClient(timeout=30) as c:
                r=await c.post(api['base_url']+'/chat/completions',json=payload,headers=headers)
                r.raise_for_status(); d=r.json()
            out=d['choices'][0]['message']['content'].strip().strip('"').strip("'")
            if out and 2<len(out)<len(prompt)*4: return out
        except Exception as e:
            log.warning('translate #%s: %s',api.get('id'),e); continue
    return prompt
async def generate(prompt,size,timeout_sec):
    last=None
    for api in api_active('image'):
        try:
            payload={'model':api['model'],'prompt':prompt,'size':size,'n':1}
            headers={'Authorization':'Bearer '+api['api_key'],'Content-Type':'application/json'}
            async with httpx.AsyncClient(timeout=timeout_sec+30) as c:
                r=await c.post(api['base_url']+'/images/generations',json=payload,headers=headers)
                r.raise_for_status(); return r.json()
        except Exception as e:
            log.warning('generate #%s: %s',api.get('id'),e); last=e; continue
    raise RuntimeError(f'All APIs failed. Last: {last}')

# ═══════════ QUEUE ═══════════
pending_jobs=[]; job_lock=asyncio.Lock(); workers=[]
async def queue_position_updater(app):
    while True:
        try:
            await asyncio.sleep(5)
            async with job_lock:
                snap=[(i,j) for i,j in enumerate(pending_jobs) if not j.get('cancelled') and not j.get('inline')]
            for pos0,j in snap:
                pos=pos0+1
                if j.get('last_pos')==pos or not j.get('msg_id'): continue
                j['last_pos']=pos; uid=j['uid']
                prefix='💎 ' if j.get('priority') else ''
                try:
                    await app.bot.edit_message_text(chat_id=j['chat'],message_id=j['msg_id'],
                        text=(f'{t(uid,"queue_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n📐 {j["size"]}\n'
                              f'📝 {html.escape(j["prompt"][:120])}\n\n{prefix}{t(uid,"queue_pos")}: <b>{pos}</b>'),
                        parse_mode=ParseMode.HTML,
                        reply_markup=kb_queue_cancel(uid,j['job_id'],can_rush=not j.get('priority')))
                except: pass
        except asyncio.CancelledError: return
        except Exception as e: log.warning('queue upd: %s',e)

async def worker(app):
    while True:
        job=None
        async with job_lock:
            for i,j in enumerate(pending_jobs):
                if not j.get('cancelled'): job=pending_jobs.pop(i); break
        if job is None: await asyncio.sleep(0.5); continue
        uid=job['uid']
        is_inline=job.get('inline',False)
        chat=job.get('chat'); msg_id=job.get('msg_id'); inline_id=job.get('inline_message_id')
        timeout_sec=get_timeout(); t0=time.time()
        async def edit_safe(text):
            try:
                if is_inline: await app.bot.edit_message_text(inline_message_id=inline_id,text=text,parse_mode=ParseMode.HTML)
                else: await app.bot.edit_message_text(chat_id=chat,message_id=msg_id,text=text,parse_mode=ParseMode.HTML)
            except: pass
        try:
            if not is_inline: await app.bot.send_chat_action(chat,ChatAction.UPLOAD_PHOTO)
            await edit_safe(t(uid,'in_progress',limit=fmt_timeout()))
            await alog(app,f'🎨 <b>Генерация</b>{" (inline)" if is_inline else ""}{" 💎" if job.get("priority") else ""}\n'
                f'👤 <code>{uid}</code>\n📝 {html.escape(job["prompt"][:600])}',level=2)
            typing_task=None
            if not is_inline: typing_task=asyncio.create_task(_keep_typing(app,chat,timeout_sec))
            prompt_api=job.get('prompt_api') or job['prompt']
            try: data=await asyncio.wait_for(generate(prompt_api,job['size'],timeout_sec),timeout_sec)
            finally:
                if typing_task:
                    typing_task.cancel()
                    try: await typing_task
                    except: pass
            el=time.time()-t0; els=fmt_duration(el)
            items=data.get('data') or []
            if not items: raise RuntimeError('No image')
            item=items[0]; raw=None
            if item.get('b64_json'): raw=base64.b64decode(item['b64_json'])
            elif item.get('url'):
                async with httpx.AsyncClient(timeout=60) as c:
                    r=await c.get(item['url']); r.raise_for_status(); raw=r.content
            if not raw: raise RuntimeError('No image data')
            fid=None
            if is_inline:
                try:
                    await app.bot.edit_message_media(inline_message_id=inline_id,
                        media=InputMediaPhoto(media=raw,caption=f'{t(uid,"done_title")} • ⏱ <b>{els}</b>',parse_mode=ParseMode.HTML),
                        reply_markup=kb_done_inline(uid))
                except Exception as e: log.warning('edit inline media: %s',e)
            else:
                msg=await app.bot.send_photo(chat,raw,filename='imagesgpt.png')
                if msg and msg.photo: fid=msg.photo[-1].file_id
                await app.bot.send_message(chat,
                    f'{t(uid,"done_title")}\n━━━━━━━━━━━━━━━━━━━━\n{t(uid,"time_label")}: <b>{els}</b>\n{t(uid,"left_coins")}: <b>{balance(uid)}</b> 🪙',
                    parse_mode=ParseMode.HTML,reply_markup=kb_done(uid))
            add_history(uid,job['prompt'],job['size'],'success',fid,elapsed=el)
            await alog(app,f'✅ <b>Готово</b>{" (inline)" if is_inline else ""} • 👤 <code>{uid}</code> • ⏱ <code>{els}</code>',level=2)
        except asyncio.TimeoutError:
            el=time.time()-t0
            add_history(uid,job['prompt'],job['size'],'timeout',elapsed=el)
            if is_inline:
                try: await app.bot.edit_message_text(inline_message_id=inline_id,text='⏱ Таймаут. Попробуй ещё раз.',parse_mode=ParseMode.HTML)
                except: pass
            else: await app.bot.send_message(chat,t(uid,'timeout',limit=fmt_timeout()),reply_markup=kb_menu(uid))
            await alog(app,f'⏱ Timeout • 👤 <code>{uid}</code>',level=1)
        except Exception as e:
            el=time.time()-t0
            add_history(uid,job['prompt'],job['size'],'error',elapsed=el)
            if is_inline:
                try: await app.bot.edit_message_text(inline_message_id=inline_id,text='❌ Ошибка. Попробуй ещё раз.',parse_mode=ParseMode.HTML)
                except: pass
            else: await app.bot.send_message(chat,f'{t(uid,"error_gen")}\n\n<code>{html.escape(str(e)[:400])}</code>',
                parse_mode=ParseMode.HTML,reply_markup=kb_menu(uid))
            await alog(app,f'❌ <b>Ошибка</b> • 👤 <code>{uid}</code>\n<code>{html.escape(str(e)[:800])}</code>',level=1)
async def _keep_typing(app,chat,max_sec):
    el=0
    try:
        while el<max_sec:
            try: await app.bot.send_chat_action(chat,ChatAction.UPLOAD_PHOTO)
            except: pass
            await asyncio.sleep(4); el+=4
    except asyncio.CancelledError: return

# ═══════════ PAYMENTS ═══════════
async def pre_checkout(update,context):
    q=update.pre_checkout_query
    try:
        parts=q.invoice_payload.split(':')
        if parts[0]=='stars':
            uid=int(parts[1])
            if uid!=q.from_user.id: await q.answer(ok=False,error_message='Неверный получатель'); return
        elif parts[0]=='premium':
            uid=int(parts[1])
            if uid!=q.from_user.id: await q.answer(ok=False,error_message='Неверный получатель'); return
    except: await q.answer(ok=False,error_message='Ошибка данных'); return
    await q.answer(ok=True)

async def on_successful_payment(update,context):
    u=update.effective_user; ensure_user(u)
    sp=update.message.successful_payment
    cid=sp.telegram_payment_charge_id
    payload=sp.invoice_payload or ''
    # 💎 Premium
    if payload.startswith('premium:'):
        if stars_payment_exists(cid): return
        try:
            parts=payload.split(':')
            days=int(parts[2]); stars=int(parts[3])
        except:
            days=PREMIUM_DAYS; stars=sp.total_amount
        add_stars_payment(u.id,stars,int(stars*STAR_RATE),cid)
        new_exp=activate_premium(u.id,days)
        await update.message.reply_text(
            f'💎 <b>Premium активирован!</b>\n\n⏰ До: <b>{new_exp.strftime("%d.%m.%Y %H:%M")}</b>\n'
            f'Длительность: {days} дн.\n\n🚀 Кулдаун теперь {setting("premium_cooldown",str(PREMIUM_COOLDOWN))} сек, приоритет в очереди.',
            parse_mode=ParseMode.HTML,reply_markup=kb_menu(u.id))
        await alog(context.application,f'💎 <b>Premium</b>\n👤 <code>{u.id}</code> • {days} дн. • ⭐ {stars}',level=2)
        return
    # 💝 Обычный донат
    if stars_payment_exists(cid): return
    stars=sp.total_amount; rub=int(stars*STAR_RATE)
    add_stars_payment(u.id,stars,rub,cid)
    bonus_coins=0
    try:
        parts=payload.split(':')
        if len(parts)>=4:
            idx=int(parts[3])
            if 0<=idx<len(STAR_PACKS): bonus_coins=STAR_PACKS[idx][1]
    except: pass
    if bonus_coins: change_balance(u.id,bonus_coins)
    payouts=topup_rub(u.id,rub,method='stars')
    msg=t(u.id,'donate_thanks',stars=stars,coins=bonus_coins)
    await update.message.reply_text(msg,parse_mode=ParseMode.HTML,reply_markup=kb_menu(u.id))
    for ref,lvl,bonus in payouts:
        try: await context.bot.send_message(ref,f'💸 <b>Реферальный бонус L{lvl}</b>\n\n+<b>{bonus} ₽</b> (реф-баланс)',parse_mode=ParseMode.HTML)
        except: pass
    await alog(context.application,f'⭐ <b>Donate</b>\n👤 <code>{u.id}</code> • ⭐ {stars}',level=2)

# ═══════════ INLINE ═══════════
async def on_inline_query(update,context):
    q=update.inline_query
    query=(q.query or '').strip()
    uid=q.from_user.id
    ensure_user(q.from_user)
    if not query or len(query)>400:
        await q.answer([InlineQueryResultArticle(id='empty',title='🎨 Напиши промпт после @бота',
            description='Например: @ImagesGPTbot кот в шляпе',
            input_message_content=InputTextMessageContent('🎨 Напиши @ImagesGPTbot и промпт, например «кот в шляпе»'))],cache_time=0,is_personal=True); return
    ok,wait=check_rate(uid)
    if not ok:
        await q.answer([InlineQueryResultArticle(id='rl',title='⏱ Слишком часто',description=f'Подожди {wait} сек',
            input_message_content=InputTextMessageContent(f'⏱ Подожди {wait} сек'))],cache_time=0,is_personal=True); return
    ok2,wait2=check_gen_cooldown(uid)
    if not ok2:
        await q.answer([InlineQueryResultArticle(id='cd',title='⏱ Кулдаун',
            description=f'Подожди {fmt_cooldown(wait2)}',
            input_message_content=InputTextMessageContent(f'⏱ Подожди {fmt_cooldown(wait2)}'))],cache_time=0,is_personal=True); return
    sid=inline_prompt_save(uid,query)
    await q.answer([InlineQueryResultArticle(id=sid,title='🎨 Сгенерировать картинку',description=query[:120],
        input_message_content=InputTextMessageContent(f'🎨 <b>Генерация…</b>\n\n📝 {html.escape(query[:400])}\n\n<i>Обычно 30–90 секунд.</i>',parse_mode=ParseMode.HTML))],
        cache_time=0,is_personal=True)

async def on_chosen_inline(update,context):
    r=update.chosen_inline_result
    if not r: return
    sid=r.result_id; inline_id=r.inline_message_id; uid=r.from_user.id
    if not inline_id or sid in ('empty','rl','cd'): return
    ensure_user_by_id(uid)
    row=inline_prompt_get(sid)
    if not row:
        try: await context.bot.edit_message_text(inline_message_id=inline_id,text='❌ Промпт устарел.',parse_mode=ParseMode.HTML)
        except: pass
        return
    prompt=row['prompt']
    ok,wait=check_rate(uid)
    if not ok:
        try: await context.bot.edit_message_text(inline_message_id=inline_id,text=f'⏱ Подожди {wait} сек.',parse_mode=ParseMode.HTML)
        except: pass
        return
    ok2,wait2=check_gen_cooldown(uid)
    if not ok2:
        try: await context.bot.edit_message_text(inline_message_id=inline_id,text=f'⏱ Подожди {fmt_cooldown(wait2)}.',parse_mode=ParseMode.HTML)
        except: pass
        return
    prompt_api=await translate_prompt(prompt)
    async with job_lock:
        pending_jobs.append({'job_id':str(uuid.uuid4()),'uid':uid,'chat':None,'msg_id':None,
            'inline_message_id':inline_id,'inline':True,'prompt':prompt,'prompt_api':prompt_api,
            'size':'1024x1024','last_pos':0,'cancelled':False,'priority':is_premium(uid)})

# ═══════════ USER HANDLERS ═══════════
async def cmd_start(update,context):
    u=update.effective_user; ensure_user(u)
    if context.args:
        arg=context.args[0]
        if arg.startswith('ref_'):
            try: set_referrer(u.id,int(arg[4:]))
            except ValueError: pass
        elif arg.startswith('adv_'):
            adv=adv_get_by_code(arg[4:])
            if adv and adv['user_id']!=u.id: set_referrer(u.id,adv['user_id'])
    if is_banned(u.id):
        r=get_user(u.id); reason=r['ban_reason'] or '—'
        await update.message.reply_text(f'{t(u.id,"banned_title")}\n\n{t(u.id,"banned_reason")}: {html.escape(reason)}',parse_mode=ParseMode.HTML); return
    if not has_accepted(u.id):
        terms=TERMS_TPL.format(title=t(u.id,'terms_title'),lead=t(u.id,'terms_lead'),
            privacy=PRIVACY_URL,privacy_t=t(u.id,'terms_privacy'),
            offer=OFFER_URL,offer_t=t(u.id,'terms_offer'),note=t(u.id,'terms_note'))
        await update.message.reply_text(terms,parse_mode=ParseMode.HTML,reply_markup=kb_terms(u.id),disable_web_page_preview=True); return
    await send_screen(update,u.id,'menu',main_text(u.id),kb_menu(u.id))
async def cmd_help(update,context):
    uid=update.effective_user.id
    text=f'{t(uid,"help_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n'+t(uid,'help_text',percent=ref_percent(),bot=BOT_USERNAME)
    await send_screen(update,uid,'help',text,kb_menu(uid))
async def cmd_premium(update,context):
    uid=update.effective_user.id; ensure_user(update.effective_user)
    st_prem=is_premium(uid); days_left=premium_days_left(uid)
    stars=int(setting('premium_stars',str(PREMIUM_STARS)))
    days=int(setting('premium_days',str(PREMIUM_DAYS)))
    rub=int(stars*STAR_RATE)
    cd_prem=int(setting('premium_cooldown',str(PREMIUM_COOLDOWN)))
    if st_prem:
        text=(f'💎 <b>Premium активен</b>\n━━━━━━━━━━━━━━━━━━━━\n\n⏰ Осталось: <b>{days_left} дн.</b>\n\n'
              f'✅ Кулдаун: <b>{cd_prem} сек</b> (вместо {GEN_COOLDOWN})\n✅ Приоритет в очереди\n\n'
              f'Хочешь продлить?\n💰 <b>{stars} ⭐</b> ({rub} ₽) за {days} дн.')
    else:
        text=(f'💎 <b>Premium</b>\n━━━━━━━━━━━━━━━━━━━━\n\nЧто даёт:\n'
              f'🚀 Кулдаун <b>{cd_prem} сек</b> вместо {GEN_COOLDOWN}\n'
              f'⏩ Приоритет в очереди\n💎 Бейдж в профиле\n\n'
              f'💰 Стоимость: <b>{stars} ⭐</b> ({rub} ₽) за {days} дн.')
    await update.message.reply_text(text,parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f'⭐ Купить за {stars} ⭐',callback_data='premium:buy')],
            [InlineKeyboardButton('◀️ В меню',callback_data='menu')]]))
async def cmd_ref_history(update,context):
    u=update.effective_user; ensure_user(u); uid=u.id
    rows=ref_withdrawals_list(uid)
    if not rows:
        await update.message.reply_text(t(uid,'ref_history_empty'),parse_mode=ParseMode.HTML,reply_markup=kb_menu(uid)); return
    lines=[t(uid,'ref_history_title'),'━━━━━━━━━━━━━━━━━━━━','']
    for r in rows:
        sm={'pending':'⏳','paid':'✅','declined':'❌'}.get(r['status'],'?')
        method='💸' if r['method']=='balance' else '💳'
        lines.append(f'{sm} {method} #{r["id"]} • <b>{r["amount"]} ₽</b> • {r["created_at"]}')
    await update.message.reply_text('\n'.join(lines),parse_mode=ParseMode.HTML,reply_markup=kb_menu(uid))

async def on_callbacks(update,context):
    q=update.callback_query; await q.answer()
    u=q.from_user; ensure_user(u); uid=u.id; d=q.data

    # 💎 Premium покупка
    if d=='premium:buy':
        stars=int(setting('premium_stars',str(PREMIUM_STARS)))
        days=int(setting('premium_days',str(PREMIUM_DAYS)))
        rub=int(stars*STAR_RATE)
        try:
            await context.bot.send_invoice(
                chat_id=q.message.chat_id,
                title=f'💎 Premium — {days} дн.',
                description=f'Кулдаун 30 сек + приоритет в очереди. {stars} ⭐ ({rub} ₽).',
                payload=f'premium:{uid}:{days}:{stars}',
                provider_token='',currency='XTR',
                prices=[LabeledPrice(label=f'Premium {days} дн.',amount=stars)])
        except Exception as e:
            await q.message.reply_text(f'❌ Ошибка счёта: {e}')
        return
    if d=='premium':
        st_prem=is_premium(uid); days_left=premium_days_left(uid)
        stars=int(setting('premium_stars',str(PREMIUM_STARS)))
        days=int(setting('premium_days',str(PREMIUM_DAYS)))
        rub=int(stars*STAR_RATE)
        cd_prem=int(setting('premium_cooldown',str(PREMIUM_COOLDOWN)))
        if st_prem:
            text=(f'💎 <b>Premium активен</b>\n━━━━━━━━━━━━━━━━━━━━\n\n⏰ Осталось: <b>{days_left} дн.</b>\n\n'
                  f'✅ Кулдаун: <b>{cd_prem} сек</b> (вместо {GEN_COOLDOWN})\n✅ Приоритет в очереди\n\n'
                  f'Хочешь продлить?\n💰 <b>{stars} ⭐</b> ({rub} ₽) за {days} дн.')
        else:
            text=(f'💎 <b>Premium</b>\n━━━━━━━━━━━━━━━━━━━━\n\nЧто даёт:\n'
                  f'🚀 Кулдаун <b>{cd_prem} сек</b> вместо {GEN_COOLDOWN}\n'
                  f'⏩ Приоритет в очереди\n💎 Бейдж в профиле\n\n'
                  f'💰 Стоимость: <b>{stars} ⭐</b> ({rub} ₽) за {days} дн.')
        await show_screen(q,context,uid,None,text,InlineKeyboardMarkup([
            [InlineKeyboardButton(f'⭐ Купить за {stars} ⭐',callback_data='premium:buy')],
            [InlineKeyboardButton(t(uid,'back_menu'),callback_data='menu')]]))
        return

    if d.startswith('buy:'):
        try: idx=int(d.split(':',1)[1])
        except: return
        if idx<0 or idx>=len(STAR_PACKS): await q.answer('Пакет не найден',show_alert=True); return
        stars,bonus=STAR_PACKS[idx]; rub=int(stars*STAR_RATE)
        title=f'{stars} ⭐'; desc=f'Пожертвование {rub} ₽'
        if bonus: desc+=f' → +{bonus} 🪙'
        try:
            await context.bot.send_invoice(chat_id=q.message.chat_id,title=title,description=desc,
                payload=f'stars:{uid}:{stars}:{idx}',provider_token='',currency='XTR',
                prices=[LabeledPrice(label=title,amount=stars)])
        except Exception as e: await q.message.reply_text(f'❌ Ошибка счёта: {e}')
        return

    if d=='terms:accept':
        accept_terms(uid)
        await show_screen(q,context,uid,'menu',t(uid,'terms_accepted')+'\n\n'+main_text(uid),kb_menu(uid)); return
    if d=='terms:reject':
        await show_screen(q,context,uid,None,t(uid,'terms_rejected'),None); return
    if is_banned(uid):
        await show_screen(q,context,uid,None,t(uid,'banned_access'),None); return
    if not has_accepted(uid):
        await show_screen(q,context,uid,None,t(uid,'terms_first'),None); return
    if d=='menu':
        await show_screen(q,context,uid,'menu',main_text(uid),kb_menu(uid)); return
    if d=='help':
        text=f'{t(uid,"help_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n'+t(uid,'help_text',percent=ref_percent(),bot=BOT_USERNAME)
        await show_screen(q,context,uid,'help',text,kb_menu(uid)); return

    if d=='roulette':
        st=roulette_status(uid)
        head=f'{t(uid,"roulette_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n'
        if st['can_spin']:
            await show_screen(q,context,uid,None,head+t(uid,'roulette_rules'),kb_roulette(uid,can_spin=True)); return
        await show_screen(q,context,uid,None,head+t(uid,'roulette_already_this_week'),kb_roulette(uid,can_spin=False)); return
    if d=='roulette:spin':
        st=roulette_status(uid)
        if not st['can_spin']:
            await q.answer(t(uid,'roulette_already_this_week'),show_alert=True); return
        await q.edit_message_text(t(uid,'roulette_spinning'),parse_mode=ParseMode.HTML)
        await asyncio.sleep(1.2)
        prize=roulette_spin(uid)
        head=f'{t(uid,"roulette_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n'
        if prize>0:
            txt=head+t(uid,'roulette_won',n=prize)+f'\n\n🪙 {t(uid,"coins")}: <b>{balance(uid)}</b>\n\n'+t(uid,'roulette_done')
        else: txt=head+t(uid,'roulette_empty')+'\n\n'+t(uid,'roulette_done')
        await show_screen(q,context,uid,None,txt,kb_menu(uid)); return

    if d=='lang':
        text=f'{t(uid,"lang_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n{t(uid,"lang_current")}: <b>{LANGS_NAMES.get(get_lang(uid),"")}</b>'
        await show_screen(q,context,uid,'lang',text,kb_lang(uid)); return
    if d.startswith('lang:set:'):
        new_lang=d.split(':',2)[2]; set_lang(uid,new_lang)
        await show_screen(q,context,uid,'menu',f'{t(uid,"lang_switched",lang=LANGS_NAMES.get(new_lang,new_lang))}\n\n'+main_text(uid),kb_menu(uid)); return

    if d=='balance':
        prem=''
        if is_premium(uid): prem=f'\n💎 Premium: <b>{premium_days_left(uid)} дн.</b>'
        text=(f'{t(uid,"your_balance")}\n\n🪙 {t(uid,"coins")}: <b>{balance(uid)}</b>\n'
              f'🎁 {t(uid,"ref_balance")}: <b>{ref_balance(uid)} ₽</b>{prem}\n\n'
              f'📊 {t(uid,"rate")}: <b>1 🪙 = {coin_rate()} ₽</b>')
        await show_screen(q,context,uid,'balance',text,kb_balance(uid)); return

    if d=='topup':
        text=(f'{t(uid,"topup_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n{t(uid,"topup_note")}')
        rows=[]
        for i,(stars,bonus) in enumerate(STAR_PACKS):
            rub=int(stars*STAR_RATE); label=f'⭐ {stars} → {rub} ₽'
            if bonus: label+=f' +{bonus} 🪙'
            rows.append([InlineKeyboardButton(label,callback_data=f'buy:{i}')])
        rows.append([InlineKeyboardButton(t(uid,'support_btn'),callback_data='support:new')])
        rows.append([InlineKeyboardButton(t(uid,'back'),callback_data='balance')])
        await show_screen(q,context,uid,'topup',text,InlineKeyboardMarkup(rows)); return

    if d=='exchange':
        rb=rub_balance(uid); rate=coin_rate()
        if rb<rate:
            text=f'{t(uid,"not_enough_rub")}\n\n{t(uid,"min_exchange")}: <b>{rate} ₽</b>\n{t(uid,"you_have")}: <b>{rb} ₽</b>'
            await show_screen(q,context,uid,'exchange',text,InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,'back'),callback_data='balance')]])); return
        context.user_data['waiting']='exchange_rub'
        text=(f'{t(uid,"exchange_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n📊 {t(uid,"rate")}: <b>1 🪙 = {rate} ₽</b>\n'
              f'💵 {t(uid,"you_have")}: <b>{rb} ₽</b>\n\n{t(uid,"exchange_ask")}\n<i>{t(uid,"exchange_must_be_multiple",rate=rate)}</i>')
        await show_screen(q,context,uid,'exchange',text,InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,'cancel'),callback_data='cancel')]])); return

    if d=='history' or d.startswith('hist:p:'):
        page=0
        if d.startswith('hist:p:'):
            try: page=int(d.split(':',2)[2])
            except: page=0
        total=user_history_total(uid)
        if total==0:
            await show_screen(q,context,uid,'history',t(uid,'history_empty'),kb_menu(uid)); return
        ps=HISTORY_PAGE_SIZE; tp=max(1,(total+ps-1)//ps); page=max(0,min(page,tp-1))
        rows=user_history_page(uid,page*ps,ps)
        lines=[t(uid,'history_title'),'━━━━━━━━━━━━━━━━━━━━','']
        for i,r in enumerate(rows):
            num=page*ps+i+1; icon='✅' if r['status']=='success' else '❌'
            lines.append(f'<b>{num}.</b> {icon} {html.escape(r["prompt"][:60])}')
        lines.append(''); lines.append(t(uid,'history_hint'))
        await show_screen(q,context,uid,'history','\n'.join(lines),kb_history(uid,page,total)); return
    if d=='hist:noop': return
    if d.startswith('hist:show:'):
        try: hid=int(d.split(':',2)[2])
        except: return
        item=get_history_item(uid,hid)
        if not item:
            await q.answer(t(uid,'history_not_found'),show_alert=True); return
        caption=f'📝 {html.escape(item["prompt"][:500])}\n\n📐 {item["size"]}\n📅 {item["created_at"]}'
        if item['elapsed']: caption+=f'\n⏱ {fmt_duration(item["elapsed"])}'
        if item['status']!='success': caption=t(uid,'history_failed')+'\n\n'+caption
        if item['file_id']:
            try: await context.bot.send_photo(q.message.chat_id,item['file_id'],caption=caption,parse_mode=ParseMode.HTML)
            except: await context.bot.send_message(q.message.chat_id,t(uid,'history_img_unavail')+'\n\n'+caption,parse_mode=ParseMode.HTML)
        else: await context.bot.send_message(q.message.chat_id,caption,parse_mode=ParseMode.HTML)
        return

    if d=='ref':
        total,earned=ref_stats(uid); percent=ref_percent()
        adv=adv_get_by_uid(uid); extra=''
        if adv: extra=f'\n\n🎯 <b>Инфлюенсер-ссылка</b>\n<code>{adv_link(adv["code"])}</code>\nПроцент: <b>{adv["percent"]}%</b>'
        rb=ref_balance(uid)
        text=(f'{t(uid,"ref_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n{t(uid,"ref_your_link")}\n<code>{ref_link(uid)}</code>\n\n'
              f'{t(uid,"ref_you_get",percent=percent)}\nL1 {REF_L1}% • L2 {REF_L2}%\n{t(uid,"ref_earn_rub")}\n\n'
              f'{t(uid,"ref_invited")}: <b>{total}</b>\n🎁 <b>{t(uid,"ref_balance")}: {rb} ₽</b>\n\n{t(uid,"ref_note")}{extra}')
        kb=InlineKeyboardMarkup([
            [InlineKeyboardButton(t(uid,'ref_share'),url=f'https://t.me/share/url?url={ref_link(uid)}&text=ImagesGPT')],
            [InlineKeyboardButton(t(uid,'ref_withdraw'),callback_data='refw')],
            [InlineKeyboardButton(t(uid,'back_menu'),callback_data='menu')]])
        await show_screen(q,context,uid,'ref',text,kb); return

    if d=='refw':
        rb=ref_balance(uid)
        text=(f'{t(uid,"ref_withdraw_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n'
              +t(uid,'ref_withdraw_text',bal=rb,min_bal=REF_WITHDRAW_TO_BALANCE_MIN,min_card=REF_WITHDRAW_TO_CARD_MIN))
        await show_screen(q,context,uid,None,text,kb_ref_withdraw(uid)); return
    if d=='refw:history':
        rows=ref_withdrawals_list(uid)
        if not rows:
            await show_screen(q,context,uid,None,t(uid,'ref_history_empty'),InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,'back'),callback_data='refw')]])); return
        lines=[t(uid,'ref_history_title'),'━━━━━━━━━━━━━━━━━━━━','']
        for r in rows:
            sm={'pending':'⏳ ожидает','paid':'✅ выплачено','declined':'❌ отклонено'}.get(r['status'],r['status'])
            method='💸 баланс' if r['method']=='balance' else '💳 карта'
            lines.append(f'#{r["id"]} • {method} • <b>{r["amount"]} ₽</b>')
            lines.append(f'   {sm} • {r["created_at"]}')
        await show_screen(q,context,uid,None,'\n'.join(lines),InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,'back'),callback_data='refw')]])); return
    if d=='refw:bal':
        rb=ref_balance(uid)
        if rb<REF_WITHDRAW_TO_BALANCE_MIN:
            await q.answer(t(uid,'ref_withdraw_too_low',min=REF_WITHDRAW_TO_BALANCE_MIN,bal=rb),show_alert=True); return
        context.user_data['waiting']='refw_bal'
        await show_screen(q,context,uid,None,t(uid,'ref_withdraw_to_balance_ask',min_bal=REF_WITHDRAW_TO_BALANCE_MIN,bal=rb),
            InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,'cancel'),callback_data='refw')]])); return
    if d=='refw:card':
        rb=ref_balance(uid)
        if rb<REF_WITHDRAW_TO_CARD_MIN:
            await q.answer(t(uid,'ref_withdraw_too_low',min=REF_WITHDRAW_TO_CARD_MIN,bal=rb),show_alert=True); return
        context.user_data['waiting']='refw_card_amount'
        await show_screen(q,context,uid,None,t(uid,'ref_withdraw_to_card_ask',min_card=REF_WITHDRAW_TO_CARD_MIN,bal=rb),
            InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,'cancel'),callback_data='refw')]])); return

    if d=='promo':
        context.user_data['waiting']='promo'
        await show_screen(q,context,uid,'promo',t(uid,'promo_ask'),
            InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,'back_menu'),callback_data='menu')]])); return

    if d=='support':
        tid=get_open_ticket(uid)
        txt=f'{t(uid,"support_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n'
        txt+=t(uid,'support_open_exists',tid=tid) if tid else t(uid,'support_desc')
        await show_screen(q,context,uid,'support',txt,kb_support(uid,tid)); return
    if d=='support:new':
        context.user_data['waiting']='ticket'
        await show_screen(q,context,uid,'support',t(uid,'support_create_ask'),
            InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,'cancel'),callback_data='support')]])); return
    if d=='support:list':
        rows=list_user_tickets(uid); tid=get_open_ticket(uid)
        if not rows:
            await show_screen(q,context,uid,'support',t(uid,'support_none'),kb_support(uid,tid)); return
        lines=[t(uid,'support_my_title'),'━━━━━━━━━━━━━━━━━━━━','']
        for r in rows:
            icon='🟢' if r['status']=='open' else '⚪'
            lines.append(f'{icon} <b>#{r["id"]}</b> • {r["status"]} • {r["updated_at"]}')
        await show_screen(q,context,uid,'support','\n'.join(lines),kb_support(uid,tid)); return
    if d.startswith('support:view:'):
        tid=int(d.split(':',2)[2]); t_=get_ticket(tid)
        if not t_ or t_['user_id']!=uid:
            await show_screen(q,context,uid,'support','❌',kb_support(uid,get_open_ticket(uid))); return
        await render_ticket_to_user(q,context,tid); return
    if d.startswith('support:close:'):
        tid=int(d.split(':',2)[2]); t_=get_ticket(tid)
        if not t_ or t_['user_id']!=uid: return
        close_ticket(tid)
        await show_screen(q,context,uid,'support',t(uid,'ticket_closed',tid=tid),kb_support(uid,get_open_ticket(uid)))
        await alog(context.application,f'⚪ <code>{uid}</code> закрыл тикет #{tid}.',level=2); return

    if d.startswith('ticket_reply:'):
        if not is_admin(uid): return
        tid=int(d.split(':',1)[1]); t_=get_ticket(tid)
        if not t_: await q.edit_message_text('❌'); return
        context.user_data['admin_reply_ticket']=tid
        await q.edit_message_text(f'✍️ Ответ <b>#{tid}</b> (👤 <code>{t_["user_id"]}</code>):',parse_mode=ParseMode.HTML); return
    if d.startswith('ticket_close:'):
        if not is_admin(uid): return
        tid=int(d.split(':',1)[1]); t_=get_ticket(tid)
        if not t_: await q.edit_message_text('❌'); return
        close_ticket(tid); await q.edit_message_text(f'🔒 Тикет #{tid} закрыт.')
        try: await context.bot.send_message(t_['user_id'],t(t_['user_id'],'ticket_closed',tid=tid),parse_mode=ParseMode.HTML,reply_markup=kb_menu(t_['user_id']))
        except: pass
        return

    if d.startswith('adm:'):
        if not is_admin(uid): return
        await handle_admin_cb(q,context,d); return

    # 🚀 Ускорение
    if d.startswith('q:rush:'):
        jid=d.split(':',2)[2]
        cost=int(setting('rush_cost',str(RUSH_COST)))
        target=None
        async with job_lock:
            for j in pending_jobs:
                if j['job_id']==jid and j['uid']==uid: target=j; break
        if not target:
            await q.answer('Уже не в очереди',show_alert=True); return
        if target.get('priority'):
            await q.answer('Уже ускорено',show_alert=True); return
        if balance(uid)<cost:
            await q.answer(t(uid,'insufficient_coins'),show_alert=True); return
        change_balance(uid,-cost)
        async with job_lock:
            pending_jobs.remove(target)
            target['priority']=True
            idx=0
            for i,j in enumerate(pending_jobs):
                if j.get('priority'): idx=i+1
                else: break
            pending_jobs.insert(idx,target)
        await q.answer('🚀 Ускорено!',show_alert=False)
        text=(f'{t(uid,"queue_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n📐 {target["size"]}\n'
              f'📝 {html.escape(target["prompt"][:120])}\n\n💎 {t(uid,"queue_pos")}: <b>1</b>')
        await q.edit_message_text(text,parse_mode=ParseMode.HTML,
            reply_markup=kb_queue_cancel(uid,jid,can_rush=False))
        return

    if d.startswith('q:cancel:'):
        jid=d.split(':',2)[2]; refunded=False
        async with job_lock:
            for i,j in enumerate(pending_jobs):
                if j['job_id']==jid and j['uid']==uid: pending_jobs.pop(i); refunded=True; break
        if refunded: await show_screen(q,context,uid,'menu','❌ Отменено.',kb_menu(uid))
        else: await show_screen(q,context,uid,'menu','❌',kb_menu(uid))
        return

    if d=='create':
        ok,wait=check_rate(uid)
        if not ok:
            await show_screen(q,context,uid,'menu',t(uid,'rate_limit',sec=wait),kb_menu(uid)); return
        ok2,wait2=check_gen_cooldown(uid)
        if not ok2:
            await show_screen(q,context,uid,'menu',t(uid,'cooldown',time=fmt_cooldown(wait2)),kb_menu(uid)); return
        ok3,wait3=check_new_user_limit(uid)
        if not ok3:
            await show_screen(q,context,uid,'menu',t(uid,'new_user_limit'),kb_menu(uid)); return
        context.user_data['waiting']='image'
        await show_screen(q,context,uid,None,t(uid,'create_prompt'),
            InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,'cancel'),callback_data='cancel')]])); return
    if d=='cancel':
        context.user_data.pop('waiting',None)
        await show_screen(q,context,uid,'menu','❌',kb_menu(uid)); return
    if d.startswith('size:'):
        p=context.user_data.get('prompt')
        if not p:
            await show_screen(q,context,uid,'menu','❌',kb_menu(uid)); return
        p_api=context.user_data.get('prompt_api',p)
        tok=str(uuid.uuid4()); context.user_data['pending']={tok:(p,p_api,d.split(':',1)[1])}
        text=(f'{t(uid,"confirm_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n📝 {html.escape(p[:500])}\n\n📐 {d.split(":",1)[1]}\n\n')
        await show_screen(q,context,uid,None,text,kb_confirm(uid,tok)); return
    if d.startswith('ok:'):
        tok=d[3:]; item=context.user_data.get('pending',{}).pop(tok,None)
        if not item:
            await show_screen(q,context,uid,'menu','❌',kb_menu(uid)); return
        p,p_api,size=item; jid=str(uuid.uuid4())
        priority=is_premium(uid)
        async with job_lock:
            job={'job_id':jid,'uid':uid,'chat':q.message.chat_id,
                'prompt':p,'prompt_api':p_api,'size':size,
                'msg_id':q.message.message_id,'last_pos':0,
                'cancelled':False,'priority':priority}
            if priority:
                idx=0
                for i,j in enumerate(pending_jobs):
                    if j.get('priority'): idx=i+1
                    else: break
                pending_jobs.insert(idx,job)
            else:
                pending_jobs.append(job)
            pos=len([j for j in pending_jobs if not j.get('cancelled') and not j.get('inline')])
        prefix='💎 ' if priority else ''
        text=(f'{t(uid,"queue_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n📐 {size}\n📝 {html.escape(p[:120])}\n\n'
              f'{prefix}{t(uid,"queue_pos")}: <b>{pos}</b>')
        await show_screen(q,context,uid,None,text,kb_queue_cancel(uid,jid,can_rush=not priority)); return
    if d.startswith('no:'):
        context.user_data.pop('waiting',None)
        await show_screen(q,context,uid,'menu','❌',kb_menu(uid)); return

async def render_ticket_to_user(q,context,tid):
    uid=q.from_user.id; t_=get_ticket(tid); msgs=ticket_msgs(tid)
    lines=[f'🆘 <b>#{tid}</b> ({t_["status"]})','━━━━━━━━━━━━━━━━━━━━','']; photos=[]
    for m in msgs:
        who='👤 ' + ('Ты' if get_lang(uid)=='ru' else 'You') if m['sender']=='user' else '🛠 Support'
        body=m['text'] or ('📷' if m['photo_file_id'] else '')
        lines.append(f'{who} <i>{m["created_at"]}</i>\n{html.escape(body)}')
        if m['photo_file_id']: photos.append((m['photo_file_id'],f'#{tid}'))
    kb=kb_ticket_user(uid,tid) if t_['status']=='open' else kb_support(uid,get_open_ticket(uid))
    await show_screen(q,context,uid,'support','\n\n'.join(lines),kb)
    for fid,cap in photos[-5:]:
        try: await context.bot.send_photo(q.message.chat_id,fid,caption=cap)
        except: pass

async def on_message(update,context):
    u=update.effective_user; ensure_user(u); uid=u.id
    text=(update.message.text or '').strip()
    photo=update.message.photo[-1].file_id if update.message.photo else None
    if is_banned(uid):
        await update.message.reply_text(t(uid,'banned_access')); return
    if not has_accepted(uid):
        terms=TERMS_TPL.format(title=t(uid,'terms_title'),lead=t(uid,'terms_lead'),
            privacy=PRIVACY_URL,privacy_t=t(uid,'terms_privacy'),
            offer=OFFER_URL,offer_t=t(uid,'terms_offer'),note=t(uid,'terms_note'))
        await update.message.reply_text(terms,parse_mode=ParseMode.HTML,reply_markup=kb_terms(uid),disable_web_page_preview=True); return

    if is_admin(uid) and context.user_data.get('admin_banner_upload'):
        key=context.user_data.pop('admin_banner_upload')
        if not photo: await update.message.reply_text('❌ Пришли изображение.'); return
        set_banner(key,photo)
        await update.message.reply_text(f'✅ Баннер <b>{BANNER_KEYS.get(key,key)}</b> сохранён.',parse_mode=ParseMode.HTML,reply_markup=kb_banner_actions(key)); return

    if is_admin(uid) and context.user_data.get('admin_adv_step'):
        step=context.user_data['admin_adv_step']; data=context.user_data.get('admin_adv_data',{})
        if step=='uid':
            try: target=int(text)
            except ValueError: await update.message.reply_text('❌ ID должен быть числом.'); return
            if not get_user(target): await update.message.reply_text('❌ Пользователь не найден.'); return
            data['uid']=target; context.user_data['admin_adv_data']=data
            context.user_data['admin_adv_step']='code'
            await update.message.reply_text(f'✅ ID: <code>{target}</code>\n\n🎯 Код:',parse_mode=ParseMode.HTML); return
        if step=='code':
            code=text.lower().replace(' ','')
            if not code or len(code)>30: await update.message.reply_text('❌ 1–30 символов.'); return
            if adv_get_by_code(code): await update.message.reply_text('❌ Такой код уже есть.'); return
            data['code']=code; context.user_data['admin_adv_data']=data
            context.user_data['admin_adv_step']='percent'
            await update.message.reply_text(f'✅ Код: <code>{code}</code>\n\n💰 Процент (по умолчанию {ADV_DEFAULT_PERCENT}, «-»):',parse_mode=ParseMode.HTML); return
        if step=='percent':
            pct=ADV_DEFAULT_PERCENT
            if text.strip()!='-':
                try: pct=int(text)
                except ValueError: await update.message.reply_text('❌ Число или «-».'); return
                if pct<1 or pct>50: await update.message.reply_text('❌ 1–50%.'); return
            if adv_create(data['uid'],data['code'],pct):
                await update.message.reply_text(f'✅ Инфлюенсер назначен\n\n👤 <code>{data["uid"]}</code>\n🎯 Код: <code>{data["code"]}</code>\n💸 Процент: <b>{pct}%</b>\n🔗 <code>{adv_link(data["code"])}</code>',parse_mode=ParseMode.HTML,reply_markup=kb_admin_adv())
            else: await update.message.reply_text('❌ Ошибка.')
            context.user_data.pop('admin_adv_step',None); context.user_data.pop('admin_adv_data',None); return

    if is_admin(uid) and context.user_data.get('admin_api_step'):
        step=context.user_data['admin_api_step']; typ=context.user_data.get('admin_api_type','image'); data=context.user_data.get('admin_api_data',{})
        if step=='name':
            data['name']=text[:60] or 'api'; context.user_data['admin_api_data']=data
            context.user_data['admin_api_step']='url'
            await update.message.reply_text(f'✅ Имя: <b>{html.escape(data["name"])}</b>\n\n🌐 Base URL?',parse_mode=ParseMode.HTML); return
        if step=='url':
            data['url']=text; context.user_data['admin_api_data']=data
            context.user_data['admin_api_step']='key'
            await update.message.reply_text(f'✅ URL: <code>{html.escape(text)}</code>\n\n🔑 API Key?',parse_mode=ParseMode.HTML); return
        if step=='key':
            data['key']=text; context.user_data['admin_api_data']=data
            context.user_data['admin_api_step']='model'
            dm='gpt-image-2' if typ=='image' else 'deepseek-v4-flash'
            await update.message.reply_text(f'✅ Ключ сохранён.\n\n🎨 Модель? (по умолчанию <code>{dm}</code>)',parse_mode=ParseMode.HTML); return
        if step=='model':
            dm='gpt-image-2' if typ=='image' else 'deepseek-v4-flash'
            model=dm if text.strip()=='-' else text.strip()
            data['model']=model; context.user_data['admin_api_data']=data
            context.user_data['admin_api_step']='priority'
            await update.message.reply_text(f'✅ Модель: <code>{html.escape(model)}</code>\n\n🔢 Priority? (по умолчанию 100)',parse_mode=ParseMode.HTML); return
        if step=='priority':
            pr=100
            if text.strip()!='-':
                try: pr=int(text)
                except ValueError: await update.message.reply_text('❌ Число или «-».'); return
            aid=api_add(typ,data['name'],data['url'],data['key'],data['model'],pr)
            context.user_data.pop('admin_api_step',None); context.user_data.pop('admin_api_data',None); context.user_data.pop('admin_api_type',None)
            await update.message.reply_text(f'✅ API <b>#{aid}</b> добавлен ({typ})\n\n📛 {html.escape(data["name"])}\n🌐 <code>{html.escape(data["url"])}</code>\n🎨 {html.escape(data["model"])}\n🔢 priority: {pr}',parse_mode=ParseMode.HTML,reply_markup=kb_api_list(typ)); return

    if is_admin(uid) and context.user_data.get('admin_reply_ticket'):
        tid=context.user_data.pop('admin_reply_ticket')
        if not text and not photo: await update.message.reply_text('❌'); return
        t_=get_ticket(tid)
        if not t_ or t_['status']!='open': await update.message.reply_text('❌'); return
        add_ticket_msg(tid,'admin',text or None,photo)
        try:
            owner=t_['user_id']; reply=t(owner,'support_reply',tid=tid)
            if photo: await context.bot.send_photo(owner,photo,caption=f'{reply}\n\n{html.escape(text or "")}\n\n<i>{t(owner,"reply_here")}</i>',parse_mode=ParseMode.HTML)
            else: await context.bot.send_message(owner,f'{reply}\n\n{html.escape(text)}\n\n<i>{t(owner,"reply_here")}</i>',parse_mode=ParseMode.HTML)
            await update.message.reply_text('✅')
        except Exception as e: await update.message.reply_text(f'❌ {e}')
        return

    if is_admin(uid) and context.user_data.get('admin_input'):
        key=context.user_data.pop('admin_input')
        try: iv=int(text)
        except ValueError: await update.message.reply_text('❌'); return
        if key=='timeout' and iv<30: await update.message.reply_text('❌ min 30'); return
        if key in ('coin_rate','rate_limit_count','rate_limit_window','premium_stars','premium_days','premium_cooldown','rush_cost') and iv<1: await update.message.reply_text('❌ min 1'); return
        if key=='ref_percent' and (iv<0 or iv>100): await update.message.reply_text('❌ 0-100'); return
        set_setting(key,iv)
        await update.message.reply_text(f'✅ <b>{key}</b> = <code>{iv}</code>',parse_mode=ParseMode.HTML); return

    if is_admin(uid) and context.user_data.get('admin_api_prio_id'):
        aid=context.user_data.pop('admin_api_prio_id')
        try: pr=int(text)
        except ValueError: await update.message.reply_text('❌'); return
        api_set_priority(aid,pr); r=api_get(aid)
        if r: await update.message.reply_text(f'✅ API #{aid}: priority={pr}',parse_mode=ParseMode.HTML,reply_markup=kb_api_detail(aid))
        return

    if is_admin(uid) and context.user_data.get('admin_setbal'):
        target=context.user_data.pop('admin_setbal')
        try: amount=int(text)
        except ValueError: await update.message.reply_text('❌'); return
        set_balance_exact(target,amount)
        await update.message.reply_text(f'✅ <code>{target}</code> = <b>{amount}</b> 🪙',parse_mode=ParseMode.HTML)
        try: await context.bot.send_message(target,f'🪙 <b>{amount}</b>',parse_mode=ParseMode.HTML)
        except: pass
        return
    if is_admin(uid) and context.user_data.get('admin_addbal'):
        target=context.user_data.pop('admin_addbal')
        try: amount=int(text)
        except ValueError: await update.message.reply_text('❌'); return
        change_balance(target,amount)
        await update.message.reply_text(f'✅ <code>{target}</code> {amount:+d} → <b>{balance(target)}</b>',parse_mode=ParseMode.HTML)
        try: await context.bot.send_message(target,f'🪙 <b>{amount:+d}</b> → {balance(target)}',parse_mode=ParseMode.HTML)
        except: pass
        return
    if is_admin(uid) and context.user_data.get('admin_setrub'):
        target=context.user_data.pop('admin_setrub')
        try: amount=int(text)
        except ValueError: await update.message.reply_text('❌'); return
        set_rub_exact(target,amount)
        await update.message.reply_text(f'✅ <code>{target}</code> = <b>{amount} ₽</b>',parse_mode=ParseMode.HTML); return
    if is_admin(uid) and context.user_data.get('admin_addrub'):
        target=context.user_data.pop('admin_addrub')
        try: amount=int(text)
        except ValueError: await update.message.reply_text('❌'); return
        if amount==0: await update.message.reply_text('❌'); return
        payouts=topup_rub(target,amount,method='manual',by_admin=uid)
        msg=f'✅ <code>{target}</code> +{amount} ₽ → {rub_balance(target)} ₽'
        for ref,lvl,bonus in payouts:
            msg+=f'\n💸 L{lvl} +{bonus} ₽ → <code>{ref}</code>'
            try: await context.bot.send_message(ref,f'💸 L{lvl} +<b>{bonus} ₽</b> (реф-баланс)',parse_mode=ParseMode.HTML)
            except: pass
        await update.message.reply_text(msg,parse_mode=ParseMode.HTML)
        try: await context.bot.send_message(target,f'💵 <b>+{amount} ₽</b>\n💵 {rub_balance(target)} ₽',parse_mode=ParseMode.HTML,reply_markup=kb_menu(target))
        except: pass
        return
    if is_admin(uid) and context.user_data.get('admin_broadcast'):
        context.user_data.pop('admin_broadcast')
        if not text: await update.message.reply_text('❌'); return
        await do_broadcast(context.application,update,text); return
    if is_admin(uid) and context.user_data.get('admin_user_lookup'):
        context.user_data.pop('admin_user_lookup')
        try: target=int(text)
        except ValueError: await update.message.reply_text('❌'); return
        await show_user_card(update.message,target); return
    if is_admin(uid) and context.user_data.get('admin_ban_reason'):
        target=context.user_data.pop('admin_ban_reason')
        reason=text or '—'; set_ban(target,True,reason,uid)
        await update.message.reply_text(f'⛔ <code>{target}</code>: {html.escape(reason)}',parse_mode=ParseMode.HTML)
        try: await context.bot.send_message(target,f'{t(target,"banned_title")}\n\n{t(target,"banned_reason")}: {html.escape(reason)}',parse_mode=ParseMode.HTML)
        except: pass
        return

    if is_admin(uid) and context.user_data.get('promo_step'):
        step=context.user_data['promo_step']
        if step=='code':
            code=text.upper().replace(' ','')
            if not code or len(code)>40: await update.message.reply_text('❌ 1–40 символов.'); return
            if get_promo(code): await update.message.reply_text('❌ Такой код уже есть.'); return
            context.user_data['promo_data']={'code':code}; context.user_data['promo_step']='amount'
            await update.message.reply_text(f'✅ <code>{code}</code>\n\n💰 Сумма монет?',parse_mode=ParseMode.HTML); return
        if step=='amount':
            try: amount=int(text)
            except ValueError: await update.message.reply_text('❌'); return
            if amount<=0: await update.message.reply_text('❌ >0'); return
            context.user_data['promo_data']['amount']=amount; context.user_data['promo_step']='uses'
            await update.message.reply_text(f'✅ <b>{amount}</b> 🪙\n\n🔢 Активаций?',parse_mode=ParseMode.HTML); return
        if step=='uses':
            try: uses=int(text)
            except ValueError: await update.message.reply_text('❌'); return
            if uses<=0: await update.message.reply_text('❌ >0'); return
            context.user_data['promo_data']['uses']=uses; context.user_data['promo_step']='days'
            await update.message.reply_text(f'✅ <b>{uses}</b>\n\n⏰ Дней? (0 или «нет» — без срока)',parse_mode=ParseMode.HTML); return
        if step=='days':
            v=text.lower(); days=None
            if v not in ('0','нет','no','-'):
                try: days=int(text)
                except ValueError: await update.message.reply_text('❌'); return
                if days<=0: days=None
            data=context.user_data.pop('promo_data',{}); context.user_data.pop('promo_step',None)
            ok,err=create_promo(data['code'],data['amount'],data['uses'],days,uid)
            if not ok: await update.message.reply_text(f'❌ {err}'); return
            exp=f'\n⏰ До: {days} дн.' if days else ''
            await update.message.reply_text(f'✅ <code>{data["code"]}</code>\n🪙 {data["amount"]} • 🔢 {data["uses"]}{exp}',parse_mode=ParseMode.HTML,reply_markup=kb_promos_main()); return

    waiting=context.user_data.get('waiting')

    if waiting=='refw_bal':
        context.user_data.pop('waiting',None)
        try: amount=int(text)
        except ValueError: await update.message.reply_text('❌ Число.',reply_markup=kb_menu(uid)); return
        if amount<REF_WITHDRAW_TO_BALANCE_MIN:
            await update.message.reply_text(t(uid,'ref_withdraw_too_low',min=REF_WITHDRAW_TO_BALANCE_MIN,bal=ref_balance(uid)),reply_markup=kb_menu(uid)); return
        rb=ref_balance(uid)
        if amount>rb:
            await update.message.reply_text(t(uid,'ref_withdraw_not_enough',bal=rb),reply_markup=kb_menu(uid)); return
        change_ref_balance(uid,-amount)
        c=db(); c.execute('UPDATE users SET rub_balance=rub_balance+? WHERE user_id=?',(amount,uid)); c.commit()
        wid=ref_withdrawal_create(uid,amount,'balance'); ref_withdrawal_set_status(wid,'paid',by=0,note='auto')
        await update.message.reply_text(t(uid,'ref_withdraw_balance_ok',amount=amount,bal=rub_balance(uid)),parse_mode=ParseMode.HTML,reply_markup=kb_menu(uid))
        await alog(context.application,f'💸 <b>Реф → баланс</b>\n👤 <code>{uid}</code> • {amount} ₽',level=2)
        return
    if waiting=='refw_card_amount':
        context.user_data.pop('waiting',None)
        try: amount=int(text)
        except ValueError: await update.message.reply_text('❌ Число.',reply_markup=kb_menu(uid)); return
        if amount<REF_WITHDRAW_TO_CARD_MIN:
            await update.message.reply_text(t(uid,'ref_withdraw_too_low',min=REF_WITHDRAW_TO_CARD_MIN,bal=ref_balance(uid)),reply_markup=kb_menu(uid)); return
        rb=ref_balance(uid)
        if amount>rb:
            await update.message.reply_text(t(uid,'ref_withdraw_not_enough',bal=rb),reply_markup=kb_menu(uid)); return
        context.user_data['refw_card_amount']=amount; context.user_data['waiting']='refw_card_number'
        await update.message.reply_text(t(uid,'ref_withdraw_card_number',amount=amount),parse_mode=ParseMode.HTML); return
    if waiting=='refw_card_number':
        context.user_data.pop('waiting',None)
        amount=context.user_data.pop('refw_card_amount',0)
        if not amount: await update.message.reply_text('❌ Ошибка суммы.',reply_markup=kb_menu(uid)); return
        card=text.replace(' ','')
        if len(card)<10: await update.message.reply_text('❌ Слишком короткий номер.',reply_markup=kb_menu(uid)); return
        rb=ref_balance(uid)
        if amount>rb: await update.message.reply_text(t(uid,'ref_withdraw_not_enough',bal=rb),reply_markup=kb_menu(uid)); return
        change_ref_balance(uid,-amount); wid=ref_withdrawal_create(uid,amount,'card',card=card)
        await update.message.reply_text(t(uid,'ref_withdraw_card_ok',amount=amount,wid=wid),parse_mode=ParseMode.HTML,reply_markup=kb_menu(uid))
        try:
            await context.bot.send_message(ADMIN_ID,f'💳 <b>Заявка на вывод #{wid}</b>\n\n👤 <code>{uid}</code>\n💰 <b>{amount} ₽</b>\n💳 Карта: <code>{html.escape(card)}</code>',
                parse_mode=ParseMode.HTML,reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton('✅ Выплачено',callback_data=f'adm:refw:paid:{wid}'),
                    InlineKeyboardButton('❌ Отклонить',callback_data=f'adm:refw:decline:{wid}')]]))
        except: pass
        return

    if waiting=='exchange_rub':
        context.user_data.pop('waiting',None)
        try: rub=int(text)
        except ValueError: await update.message.reply_text('❌',reply_markup=kb_menu(uid)); return
        ok,res=exchange_rub_to_coins(uid,rub)
        if not ok:
            msg={'bad_amount':'❌','not_multiple':t(uid,'exchange_must_be_multiple',rate=coin_rate()),'not_enough_rub':t(uid,'not_enough_rub')}.get(res,'❌')
            await update.message.reply_text(msg,reply_markup=kb_menu(uid)); return
        tr=(f'{t(uid,"exchange_done")}\n━━━━━━━━━━━━━━━━━━━━\n\n💵 {t(uid,"exchange_spent")}: <b>{rub} ₽</b>\n🪙 {t(uid,"exchange_got")}: <b>+{res} 🪙</b>\n\n💵 {t(uid,"rubles")}: <b>{rub_balance(uid)} ₽</b>\n🪙 {t(uid,"coins")}: <b>{balance(uid)}</b>')
        await update.message.reply_text(tr,parse_mode=ParseMode.HTML,reply_markup=kb_menu(uid)); return

    if waiting=='promo':
        context.user_data.pop('waiting',None)
        code=text.upper()
        if not code: await update.message.reply_text('❌'); return
        ok,res=activate_promo(code,uid)
        if not ok: await update.message.reply_text('❌',reply_markup=kb_menu(uid)); return
        await update.message.reply_text(f'{t(uid,"promo_ok")}\n\n{t(uid,"promo_credited",n=res)}\n🪙 {t(uid,"coins")}: <b>{balance(uid)}</b>',parse_mode=ParseMode.HTML,reply_markup=kb_menu(uid)); return

    if waiting=='ticket':
        context.user_data.pop('waiting',None)
        if not text and not photo: await update.message.reply_text('❌'); return
        tid=create_ticket(uid,text or None,photo)
        await update.message.reply_text(t(uid,'support_created',tid=tid),parse_mode=ParseMode.HTML,reply_markup=kb_menu(uid))
        try:
            preview=text or '📷'
            await context.bot.send_message(ADMIN_ID,f'🆘 <b>Новый тикет #{tid}</b>\n👤 <code>{uid}</code>\n\n📝 {html.escape(preview[:1500])}',parse_mode=ParseMode.HTML,reply_markup=kb_ticket_admin(tid))
            if photo: await context.bot.send_photo(ADMIN_ID,photo,caption=f'📷 #{tid}')
        except: pass
        return

    if waiting=='image':
        if not text: await update.message.reply_text('❌'); return
        if len(text)>4000: await update.message.reply_text('❌'); return
        context.user_data['waiting']=None
        m=await update.message.reply_text(t(uid,'checking'))
        try: ok,reason=await moderate(text)
        except Exception as e:
            await m.edit_text('❌'); await alog(context.application,f'⚠️ Moderation error\n<code>{html.escape(str(e)[:800])}</code>',level=1); return
        if not ok: await m.edit_text(f'{t(uid,"blocked")}\n\n{html.escape(reason)}',parse_mode=ParseMode.HTML,reply_markup=kb_menu(uid)); return
        original=text; translated=await translate_prompt(text)
        context.user_data['prompt']=original; context.user_data['prompt_api']=translated
        hint=''
        if translated!=original: hint=f'\n\n🌐 <i>Переведено: {html.escape(translated[:300])}</i>'
        await m.edit_text(t(uid,'choose_size')+hint,parse_mode=ParseMode.HTML,reply_markup=kb_sizes(uid)); return

    tid=get_open_ticket(uid)
    if tid:
        if not text and not photo: return
        add_ticket_msg(tid,'user',text or None,photo)
        await update.message.reply_text(t(uid,'ticket_msg_added',tid=tid),reply_markup=kb_menu(uid))
        try:
            preview=text or '📷'
            await context.bot.send_message(ADMIN_ID,f'💬 <b>#{tid}</b> от <code>{uid}</code>:\n\n{html.escape(preview[:1500])}',parse_mode=ParseMode.HTML,reply_markup=kb_ticket_admin(tid))
            if photo: await context.bot.send_photo(ADMIN_ID,photo,caption=f'📷 #{tid}')
        except: pass
        return

    await update.message.reply_text(t(uid,'menu_hint'),reply_markup=kb_menu(uid))

# ═══════════ ADMIN PANEL ═══════════
async def show_user_card(message,uid):
    u=get_user(uid)
    if not u: await message.reply_text('❌'); return
    total,earned=ref_stats(uid); is_adm='👑 да' if is_admin(uid) else 'нет'
    st=roulette_status(uid); rl={'ok':'доступна','already':'уже крутил'}[st['reason']]
    adv=adv_get_by_uid(uid)
    adv_line=f'\n🎯 Инфлюенсер: <b>{adv["code"]}</b> ({adv["percent"]}%)' if adv else ''
    prem_line=f'\n💎 Premium: <b>{premium_days_left(uid)} дн.</b>' if is_premium(uid) else ''
    txt=(f'👤 <b>Пользователь</b>\n━━━━━━━━━━━━━━━━━━━━\n'
        f'🆔 <code>{u["user_id"]}</code>\n📛 {html.escape(u["full_name"] or "—")}\n🔗 @{u["username"] or "—"}\n🌐 {u["lang"] or "ru"}\n'
        f'💵 Рубли: <b>{u["rub_balance"]} ₽</b>\n🎁 Реф-баланс: <b>{u["ref_balance"]} ₽</b>\n🪙 Монеты: <b>{u["balance"]}</b>{prem_line}\n'
        f'👑 Админ: {is_adm}\n📅 Регистрация: {u["created_at"]}\n👀 Последний визит: {u["last_seen"]}\n'
        f'👥 Пригласил: {total} • заработал: {earned} ₽\n🎰 Рулетка ({st["week_key"]}): <b>{rl}</b>{adv_line}\n'
        f'🚫 Бан: {"да — " + html.escape(u["ban_reason"] or "") if u["banned"] else "нет"}')
    await message.reply_text(txt,parse_mode=ParseMode.HTML,reply_markup=kb_user_card(uid))

async def handle_admin_cb(q,context,d):
    if d=='adm:main':
        await q.edit_message_text(admin_panel_text(),parse_mode=ParseMode.HTML,reply_markup=kb_admin()); return
    if d=='adm:botbalance':
        await q.edit_message_text('💳 <b>Собираю балансы…</b>',parse_mode=ParseMode.HTML)
        txt=await collect_balances()
        await q.edit_message_text(txt,parse_mode=ParseMode.HTML,reply_markup=kb_admin()); return
    if d=='adm:stats':
        c=db()
        users=c.execute('SELECT COUNT(*) AS n FROM users').fetchone()['n']
        banned=c.execute('SELECT COUNT(*) AS n FROM users WHERE banned=1').fetchone()['n']
        gens=c.execute('SELECT COUNT(*) AS n FROM history').fetchone()['n']
        ok=c.execute('SELECT COUNT(*) AS n FROM history WHERE status="success"').fetchone()['n']
        err=c.execute('SELECT COUNT(*) AS n FROM history WHERE status="error"').fetchone()['n']
        touts=c.execute('SELECT COUNT(*) AS n FROM history WHERE status="timeout"').fetchone()['n']
        opent=c.execute('SELECT COUNT(*) AS n FROM tickets WHERE status="open"').fetchone()['n']
        tsum=c.execute('SELECT COALESCE(SUM(amount),0) AS s FROM topups').fetchone()['s']
        rsum=c.execute('SELECT COALESCE(SUM(amount),0) AS s FROM ref_earnings').fetchone()['s']
        admins_count=c.execute('SELECT COUNT(*) AS n FROM admins').fetchone()['n']+1
        adv_count=c.execute('SELECT COUNT(*) AS n FROM adv_partners').fetchone()['n']
        prem_count=c.execute('SELECT COUNT(*) AS n FROM premium WHERE expires_at>?',(datetime.now().isoformat(timespec='seconds'),)).fetchone()['n']
        avg,mn,mx,cnt=gen_time_stats()
        tline=''
        if cnt: tline=f'\n⏱ Время генерации:\n   • среднее: <b>{fmt_duration(avg)}</b>\n   • мин: {fmt_duration(mn)} • макс: {fmt_duration(mx)}\n   • замеров: {cnt}\n'
        txt=('📊 <b>Статистика</b>\n━━━━━━━━━━━━━━━━━━━━\n\n'
            f'👥 Пользователей: <b>{users}</b>\n👑 Админов: <b>{admins_count}</b>\n🎯 Инфлюенсеров: <b>{adv_count}</b>\n💎 Premium: <b>{prem_count}</b>\n'
            f'🚫 Забанено: <b>{banned}</b>\n🆘 Открытых тикетов: <b>{opent}</b>\n\n'
            f'💵 Донатов: <b>{tsum} ₽</b>\n💸 Реф-выплат: <b>{rsum} ₽</b>\n\n'
            f'🎨 Генераций: <b>{gens}</b>\n✅ Успешно: <b>{ok}</b>\n❌ Ошибок: <b>{err}</b>\n⏱ Таймаутов: <b>{touts}</b>\n{tline}')
        await q.edit_message_text(txt,parse_mode=ParseMode.HTML,reply_markup=kb_admin()); return
    if d=='adm:tickets':
        rows=list_open_tickets()
        if not rows: await q.edit_message_text('🆘 Нет открытых тикетов.',reply_markup=kb_admin()); return
        lines=['🆘 <b>Открытые тикеты</b>','━━━━━━━━━━━━━━━━━━━━','']
        for r in rows: lines.append(f'<b>#{r["id"]}</b> • 👤 <code>{r["user_id"]}</code> • {r["updated_at"]}')
        await q.edit_message_text('\n'.join(lines)+'\n\nОткрыть: /ticket ID',parse_mode=ParseMode.HTML,reply_markup=kb_admin()); return
    if d=='adm:user':
        context.user_data['admin_user_lookup']=True
        await q.edit_message_text('👥 Отправь ID пользователя:'); return
    if d.startswith('adm:hist:'):
        tail=d.split(':',2)[2]
        if not tail.isdigit(): await q.edit_message_text('❌'); return
        uid=int(tail); rows=user_history(uid,20)
        if not rows: await q.edit_message_text('📜 История пуста.',reply_markup=kb_user_card(uid)); return
        lines=[f'📜 <b>История</b> <code>{uid}</code>','━━━━━━━━━━━━━━━━━━━━','']
        for i,r in enumerate(rows,1):
            icon='✅' if r['status']=='success' else '❌'
            t_extra=f' • ⏱ {fmt_duration(r["elapsed"])}' if r['elapsed'] else ''
            lines.append(f'{i}. {icon} {html.escape(r["prompt"][:60])}\n   <i>{r["size"]} • {r["created_at"]}{t_extra}</i>')
        await q.edit_message_text('\n'.join(lines),parse_mode=ParseMode.HTML,reply_markup=kb_user_card(uid)); return
    if d.startswith('adm:premgive:'):
        tail=d.split(':',2)[2]
        if not tail.isdigit(): await q.edit_message_text('❌'); return
        uid=int(tail)
        new_exp=activate_premium(uid,30)
        await q.edit_message_text(f'✅ Premium выдан <code>{uid}</code> до {new_exp.strftime("%d.%m.%Y %H:%M")}',parse_mode=ParseMode.HTML)
        try: await context.bot.send_message(uid,f'💎 <b>Тебе выдан Premium на 30 дней!</b>\n\nДо: {new_exp.strftime("%d.%m.%Y %H:%M")}\nКулдаун 30 сек, приоритет в очереди.',parse_mode=ParseMode.HTML)
        except: pass
        return
    if d.startswith('adm:userban:'):
        tail=d.split(':',2)[2]
        if not tail.isdigit(): await q.edit_message_text('❌'); return
        uid=int(tail); cur=get_user(uid)
        if not cur: await q.edit_message_text('❌ Пользователь не найден.'); return
        if cur['banned']:
            set_ban(uid,False); await q.edit_message_text(f'✅ <code>{uid}</code> разбанен.',parse_mode=ParseMode.HTML)
            await show_user_card(q.message,uid)
        else:
            context.user_data['admin_ban_reason']=uid
            await q.edit_message_text(f'✍️ Причина бана <code>{uid}</code>:',parse_mode=ParseMode.HTML)
        return
    if d.startswith('adm:setbal:'):
        tail=d.split(':',2)[2]
        if not tail.isdigit(): await q.edit_message_text('❌'); return
        uid=int(tail); context.user_data['admin_setbal']=uid
        await q.edit_message_text(f'💰 Точное значение монет <code>{uid}</code> (сейчас {balance(uid)}):',parse_mode=ParseMode.HTML); return
    if d.startswith('adm:addbal:'):
        tail=d.split(':',2)[2]
        if not tail.isdigit(): await q.edit_message_text('❌'); return
        uid=int(tail); context.user_data['admin_addbal']=uid
        await q.edit_message_text(f'🪙 Сдвиг монет <code>{uid}</code> (сейчас {balance(uid)}):',parse_mode=ParseMode.HTML); return
    if d.startswith('adm:addrub:'):
        tail=d.split(':',2)[2]
        if not tail.isdigit(): await q.edit_message_text('❌'); return
        uid=int(tail); context.user_data['admin_addrub']=uid
        await q.edit_message_text(f'💵 Сумма ₽ <code>{uid}</code> (сейчас {rub_balance(uid)} ₽):\n<i>L1 {REF_L1}% • L2 {REF_L2}% → в реф-баланс</i>',parse_mode=ParseMode.HTML); return
    if d=='adm:broadcast':
        context.user_data['admin_broadcast']=True
        await q.edit_message_text('📢 Текст для рассылки.'); return
    if d=='adm:banlist':
        rows=list_banned()
        if not rows: await q.edit_message_text('🚫 Бан-лист пуст.',reply_markup=kb_admin()); return
        lines=['🚫 <b>Бан-лист</b>','━━━━━━━━━━━━━━━━━━━━','']
        for r in rows:
            lines.append(f'<code>{r["user_id"]}</code> • {html.escape(r["full_name"] or "—")}')
            lines.append(f'   ⏰ {r["banned_at"]}\n   💬 {html.escape(r["ban_reason"] or "—")}')
        await q.edit_message_text('\n'.join(lines),parse_mode=ParseMode.HTML,reply_markup=kb_admin()); return

    if d=='adm:adv':
        await q.edit_message_text(f'🎯 <b>Инфлюенсеры</b>\n━━━━━━━━━━━━━━━━━━━━\n\nВсего: <b>{len(adv_list())}</b>\nДефолтный процент: <b>{ADV_DEFAULT_PERCENT}%</b>',parse_mode=ParseMode.HTML,reply_markup=kb_admin_adv()); return
    if d=='adm:adv:new':
        context.user_data['admin_adv_step']='uid'; context.user_data['admin_adv_data']={}
        await q.edit_message_text('🎯 <b>Назначение</b>\n\n<b>Шаг 1/3.</b> ID пользователя:',parse_mode=ParseMode.HTML); return
    if d=='adm:adv:list':
        rows=adv_list()
        if not rows: await q.edit_message_text('📋 Список пуст.',reply_markup=kb_admin_adv()); return
        lines=['🎯 <b>Инфлюенсеры</b>','━━━━━━━━━━━━━━━━━━━━','']
        for r in rows:
            lines.append(f'👤 <code>{r["user_id"]}</code> • <code>{r["code"]}</code> • {r["percent"]}%')
            lines.append(f'   🔗 <code>{adv_link(r["code"])}</code>')
        await q.edit_message_text('\n'.join(lines),parse_mode=ParseMode.HTML,reply_markup=kb_admin_adv()); return
    if d.startswith('adm:adv:mk:'):
        tail=d.split(':',3)[3]
        if not tail.isdigit(): await q.edit_message_text('❌'); return
        uid=int(tail); context.user_data['admin_adv_step']='code'; context.user_data['admin_adv_data']={'uid':uid}
        await q.edit_message_text(f'🎯 ID: <code>{uid}</code>\n\n🎯 Код:',parse_mode=ParseMode.HTML); return
    if d.startswith('adm:adv:del:'):
        code=d.split(':',3)[3]; adv_delete(code)
        await q.edit_message_text(f'✅ Инфлюенсер <code>{code}</code> удалён.',parse_mode=ParseMode.HTML,reply_markup=kb_admin_adv()); return

    if d=='adm:refw':
        await q.edit_message_text('💸 <b>Выводы реферальных</b>\n━━━━━━━━━━━━━━━━━━━━\n\nЗаявки на вывод на карту.',parse_mode=ParseMode.HTML,reply_markup=kb_admin_refw()); return
    if d=='adm:refw:pending':
        rows=ref_withdrawals_pending()
        if not rows: await q.edit_message_text('📋 Нет ожидающих заявок.',reply_markup=kb_admin_refw()); return
        lines=['💸 <b>Ожидают выплаты</b>','━━━━━━━━━━━━━━━━━━━━','']
        kb=[]
        for r in rows:
            lines.append(f'<b>#{r["id"]}</b> • 👤 <code>{r["user_id"]}</code> • {r["amount"]} ₽')
            lines.append(f'   💳 <code>{html.escape(r["card"] or "—")}</code>')
            kb.append([InlineKeyboardButton(f'#{r["id"]} • {r["amount"]} ₽',callback_data=f'adm:refw:view:{r["id"]}')])
        kb.append([InlineKeyboardButton('◀️ Назад',callback_data='adm:refw')])
        await q.edit_message_text('\n'.join(lines),parse_mode=ParseMode.HTML,reply_markup=InlineKeyboardMarkup(kb)); return
    if d.startswith('adm:refw:view:'):
        wid=int(d.split(':',3)[3]); r=ref_withdrawal_get(wid)
        if not r: await q.edit_message_text('❌'); return
        text=(f'💸 <b>Заявка #{wid}</b>\n━━━━━━━━━━━━━━━━━━━━\n\n👤 <code>{r["user_id"]}</code>\n💰 Сумма: <b>{r["amount"]} ₽</b>\n'
              f'💳 Карта: <code>{html.escape(r["card"] or "—")}</code>\n📅 Создана: {r["created_at"]}\n📊 Статус: <b>{r["status"]}</b>')
        kb=InlineKeyboardMarkup([
            [InlineKeyboardButton('✅ Выплачено',callback_data=f'adm:refw:paid:{wid}'),
             InlineKeyboardButton('❌ Отклонить',callback_data=f'adm:refw:decline:{wid}')],
            [InlineKeyboardButton('◀️ Назад',callback_data='adm:refw:pending')]])
        await q.edit_message_text(text,parse_mode=ParseMode.HTML,reply_markup=kb); return
    if d.startswith('adm:refw:paid:'):
        wid=int(d.split(':',3)[3]); r=ref_withdrawal_get(wid)
        if not r: await q.edit_message_text('❌'); return
        if r['status']!='pending': await q.answer('Уже обработана',show_alert=True); return
        ref_withdrawal_set_status(wid,'paid',by=q.from_user.id)
        await q.edit_message_text(f'✅ Заявка #{wid} выплачена.',parse_mode=ParseMode.HTML,reply_markup=kb_admin_refw())
        try: await context.bot.send_message(r['user_id'],f'✅ <b>Вывод #{wid} выполнен</b>\n\n💰 {r["amount"]} ₽',parse_mode=ParseMode.HTML)
        except: pass
        return
    if d.startswith('adm:refw:decline:'):
        wid=int(d.split(':',3)[3]); r=ref_withdrawal_get(wid)
        if not r: await q.edit_message_text('❌'); return
        if r['status']!='pending': await q.answer('Уже обработана',show_alert=True); return
        ref_withdrawal_set_status(wid,'declined',by=q.from_user.id); change_ref_balance(r['user_id'],r['amount'])
        await q.edit_message_text(f'❌ Заявка #{wid} отклонена. Средства возвращены.',parse_mode=ParseMode.HTML,reply_markup=kb_admin_refw())
        try: await context.bot.send_message(r['user_id'],f'❌ <b>Вывод #{wid} отклонён</b>\n\n💰 {r["amount"]} ₽ вернулись на реф-баланс.',parse_mode=ParseMode.HTML)
        except: pass
        return

    if d=='adm:banners':
        await q.edit_message_text('🖼 <b>Баннеры экранов</b>\n━━━━━━━━━━━━━━━━━━━━\n\n✅ — загружен, ⬜ — нет.\n📁 — файл в репо, ⚡ — закэширован.\n\n<i>Рекомендую 1280×640 или 1024×512.</i>',parse_mode=ParseMode.HTML,reply_markup=kb_admin_banners()); return
    if d.startswith('adm:ban:view:'):
        key=d.split(':',3)[3]; name=BANNER_KEYS.get(key,key)
        await q.edit_message_text(f'🖼 <b>{name}</b>\n\nИсточник: {banner_source(key)}',parse_mode=ParseMode.HTML,reply_markup=kb_banner_actions(key)); return
    if d.startswith('adm:ban:upload:'):
        key=d.split(':',3)[3]; context.user_data['admin_banner_upload']=key
        await q.edit_message_text(f'📤 Пришли картинку для баннера <b>{BANNER_KEYS.get(key,key)}</b>.\n\nРекомендую 1280×640 или 1024×512.',parse_mode=ParseMode.HTML); return
    if d.startswith('adm:ban:del:'):
        key=d.split(':',3)[3]; delete_banner(key)
        await q.edit_message_text(f'❌ Баннер из БД удалён. {banner_source(key)}',parse_mode=ParseMode.HTML,reply_markup=kb_banner_actions(key)); return

    if d=='adm:api':
        await q.edit_message_text('📡 <b>API-источники</b>\n━━━━━━━━━━━━━━━━━━━━\n\nВыбери тип.',parse_mode=ParseMode.HTML,reply_markup=kb_admin_api()); return
    if d.startswith('adm:api:list:'):
        typ=d.split(':',3)[3]; rows=api_list(typ)
        title='🖼 API картинок' if typ=='image' else '🧠 API модераторов'
        if not rows:
            await q.edit_message_text(f'{title}\n\nПока пусто. Используется API из конфига.',parse_mode=ParseMode.HTML,reply_markup=kb_api_list(typ)); return
        lines=[title,'━━━━━━━━━━━━━━━━━━━━','']
        for r in rows:
            icon='✅' if r['active'] else '⚪'
            lines.append(f'{icon} <b>#{r["id"]}</b> • {html.escape(r["name"] or "—")} • p{r["priority"]}')
            lines.append(f'   🌐 <code>{html.escape(r["base_url"])}</code>')
            lines.append(f'   🎨 <code>{html.escape(r["model"])}</code>')
        await q.edit_message_text('\n'.join(lines),parse_mode=ParseMode.HTML,reply_markup=kb_api_list(typ)); return
    if d.startswith('adm:api:view:'):
        tail=d.split(':',3)[3]
        if not tail.isdigit(): await q.edit_message_text('❌'); return
        r=api_get(int(tail))
        if not r: await q.edit_message_text('❌'); return
        txt=(f'📡 <b>API #{r["id"]}</b>\n━━━━━━━━━━━━━━━━━━━━\n\n📛 {html.escape(r["name"] or "—")}\n🌐 <code>{html.escape(r["base_url"])}</code>\n'
             f'🔑 <code>{html.escape(r["api_key"][:20])}…</code>\n🎨 <code>{html.escape(r["model"])}</code>\n🔢 priority: {r["priority"]}\n{"✅ активен" if r["active"] else "⚪ выключен"}')
        await q.edit_message_text(txt,parse_mode=ParseMode.HTML,reply_markup=kb_api_detail(r['id'])); return
    if d.startswith('adm:api:toggle:'):
        aid=int(d.split(':',3)[3]); api_toggle(aid); r=api_get(aid)
        if not r: await q.edit_message_text('❌'); return
        txt=(f'📡 <b>API #{r["id"]}</b>\n━━━━━━━━━━━━━━━━━━━━\n\n📛 {html.escape(r["name"] or "—")}\n🌐 <code>{html.escape(r["base_url"])}</code>\n'
             f'🎨 <code>{html.escape(r["model"])}</code>\n🔢 priority: {r["priority"]}\n{"✅ активен" if r["active"] else "⚪ выключен"}')
        await q.edit_message_text(txt,parse_mode=ParseMode.HTML,reply_markup=kb_api_detail(aid)); return
    if d.startswith('adm:api:del:'):
        aid=int(d.split(':',3)[3]); r=api_get(aid); typ=r['type'] if r else 'image'
        api_del(aid); await q.edit_message_text('🗑 Удалено.',parse_mode=ParseMode.HTML,reply_markup=kb_api_list(typ)); return
    if d.startswith('adm:api:prio:'):
        aid=int(d.split(':',3)[3]); context.user_data['admin_api_prio_id']=aid
        await q.edit_message_text(f'🔢 Отправь новый priority для API #{aid} (число).',parse_mode=ParseMode.HTML); return
    if d.startswith('adm:api:add:'):
        typ=d.split(':',3)[3]; context.user_data['admin_api_type']=typ; context.user_data['admin_api_data']={}; context.user_data['admin_api_step']='name'
        await q.edit_message_text(f'📡 Добавление API ({typ})\n\n<b>Шаг 1/5.</b> Имя:',parse_mode=ParseMode.HTML); return

    if d=='adm:promos':
        context.user_data.pop('promo_step',None); context.user_data.pop('promo_data',None)
        await q.edit_message_text('🎁 <b>Промокоды</b>\n━━━━━━━━━━━━━━━━━━━━\n\nВыбери действие:',parse_mode=ParseMode.HTML,reply_markup=kb_promos_main()); return
    if d=='adm:promo:new':
        context.user_data['promo_step']='code'; context.user_data['promo_data']={}
        await q.edit_message_text('🎁 <b>Создание промокода</b>\n\n<b>Шаг 1/4.</b> Введи код:',parse_mode=ParseMode.HTML,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('◀️ Отмена',callback_data='adm:promos')]])); return
    if d=='adm:promo:list':
        rows=list_promos()
        if not rows: await q.edit_message_text('📋 Нет промокодов.',reply_markup=kb_promos_main()); return
        await q.edit_message_text('📋 <b>Все промокоды</b>\n\nНажми на код, чтобы удалить:',parse_mode=ParseMode.HTML,reply_markup=kb_promo_list()); return
    if d.startswith('adm:promo:del:'):
        code=d.split(':',3)[3]; delete_promo(code)
        await q.edit_message_text(f'✅ <code>{code}</code> удалён.',parse_mode=ParseMode.HTML,reply_markup=kb_promos_main()); return
    if d=='adm:settings':
        await q.edit_message_text('⚙️ <b>Настройки</b>\n━━━━━━━━━━━━━━━━━━━━',parse_mode=ParseMode.HTML,reply_markup=kb_admin_settings()); return
    if d=='adm:premium':
        await q.edit_message_text('💎 <b>Premium настройки</b>\n━━━━━━━━━━━━━━━━━━━━',parse_mode=ParseMode.HTML,reply_markup=kb_admin_premium()); return
    if d=='adm:ratelimit':
        await q.edit_message_text(f'⏳ <b>Rate-limit</b>\n━━━━━━━━━━━━━━━━━━━━\n\n{rate_limit_count()} генераций за {rate_limit_window()} сек.',parse_mode=ParseMode.HTML,reply_markup=kb_admin_ratelimit()); return
    if d=='adm:log':
        cur=int(setting('log_level','2')); cur=(cur+1)%4; set_setting('log_level',cur)
        await q.edit_message_text('⚙️ <b>Настройки</b>',parse_mode=ParseMode.HTML,reply_markup=kb_admin_settings()); return
    if d.startswith('adm:set:'):
        key=d.split(':',2)[2]; context.user_data['admin_input']=key
        await q.edit_message_text(f'⚙️ Новое значение для <b>{key}</b>:',parse_mode=ParseMode.HTML); return

def admin_panel_text():
    return '🛠 <b>Админ-панель</b>\n━━━━━━━━━━━━━━━━━━━━\n\n/admin_help — все команды'

async def do_broadcast(app,update,text):
    rows=db().execute('SELECT user_id FROM users').fetchall()
    total=len(rows); ok=0; fail=0
    m=await update.message.reply_text(f'📢 Рассылка ({total})…')
    for r in rows:
        try:
            await app.bot.send_message(r['user_id'],text,parse_mode=ParseMode.HTML); ok+=1
        except: fail+=1
        await asyncio.sleep(0.05)
    await m.edit_text(f'✅ Доставлено: {ok}\nОшибок: {fail}')

# ═══════════ ADMIN COMMANDS ═══════════
async def cmd_admin(update,context):
    if not is_admin(update.effective_user.id): return
    await update.message.reply_text(admin_panel_text(),parse_mode=ParseMode.HTML,reply_markup=kb_admin())
async def cmd_admin_help(update,context):
    if not is_admin(update.effective_user.id): return
    await update.message.reply_text(ADMIN_HELP,parse_mode=ParseMode.HTML)
async def cmd_botbalance(update,context):
    if not is_admin(update.effective_user.id): return
    m=await update.message.reply_text('💳 <b>Собираю балансы…</b>',parse_mode=ParseMode.HTML)
    txt=await collect_balances()
    await m.edit_text(txt,parse_mode=ParseMode.HTML)
async def cmd_givepremium(update,context):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text('Использование: /givepremium ID [DAYS]'); return
    try: uid=int(context.args[0])
    except ValueError: await update.message.reply_text('❌'); return
    days=30
    if len(context.args)>=2:
        try: days=int(context.args[1])
        except ValueError: await update.message.reply_text('❌ дней — число'); return
    ensure_user_by_id(uid)
    new_exp=activate_premium(uid,days)
    await update.message.reply_text(f'✅ Premium выдан <code>{uid}</code> до {new_exp.strftime("%d.%m.%Y %H:%M")}',parse_mode=ParseMode.HTML)
    try: await context.bot.send_message(uid,f'💎 <b>Premium активирован на {days} дн.</b>\n\nДо: {new_exp.strftime("%d.%m.%Y %H:%M")}',parse_mode=ParseMode.HTML)
    except: pass
async def cmd_unpremium(update,context):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text('Использование: /unpremium ID'); return
    try: uid=int(context.args[0])
    except ValueError: await update.message.reply_text('❌'); return
    c=db(); c.execute('DELETE FROM premium WHERE user_id=?',(uid,)); c.commit()
    await update.message.reply_text(f'✅ Premium у <code>{uid}</code> снят.',parse_mode=ParseMode.HTML)
async def cmd_stats(update,context):
    if not is_admin(update.effective_user.id): return
    c=db()
    users=c.execute('SELECT COUNT(*) AS n FROM users').fetchone()['n']
    gens=c.execute('SELECT COUNT(*) AS n FROM history').fetchone()['n']
    opent=c.execute('SELECT COUNT(*) AS n FROM tickets WHERE status="open"').fetchone()['n']
    tsum=c.execute('SELECT COALESCE(SUM(amount),0) AS s FROM topups').fetchone()['s']
    admins_count=c.execute('SELECT COUNT(*) AS n FROM admins').fetchone()['n']+1
    adv_count=c.execute('SELECT COUNT(*) AS n FROM adv_partners').fetchone()['n']
    prem_count=c.execute('SELECT COUNT(*) AS n FROM premium WHERE expires_at>?',(datetime.now().isoformat(timespec='seconds'),)).fetchone()['n']
    avg,mn,mx,cnt=gen_time_stats()
    tline=f'\n⏱ Средн. генерация: {fmt_duration(avg)} ({cnt})' if cnt else ''
    await update.message.reply_text(
        f'📊 Пользователей: {users}\n👑 Админов: {admins_count}\n🎯 Инфлюенсеров: {adv_count}\n💎 Premium: {prem_count}\n'
        f'🎨 Генераций: {gens}\n🆘 Открытых: {opent}\n💵 Донатов: {tsum} ₽\n⏱ Таймаут: {get_timeout()} сек\n'
        f'📊 Курс: 1 🪙 = {coin_rate()} ₽\n💸 Реф: L1 {REF_L1}% • L2 {REF_L2}%\n'
        f'⏳ Rate: {rate_limit_count()}/{rate_limit_window()}с\n🕒 Кулдаун: {GEN_COOLDOWN}с / Premium {setting("premium_cooldown",str(PREMIUM_COOLDOWN))}с{tline}')
async def cmd_user(update,context):
    if not is_admin(update.effective_user.id) or not context.args:
        await update.message.reply_text('/user ID'); return
    try: uid=int(context.args[0])
    except ValueError: await update.message.reply_text('❌'); return
    await show_user_card(update.message,uid)
async def cmd_ticket(update,context):
    if not is_admin(update.effective_user.id) or not context.args:
        await update.message.reply_text('/ticket ID'); return
    try: tid=int(context.args[0])
    except ValueError: await update.message.reply_text('❌'); return
    t_=get_ticket(tid)
    if not t_: await update.message.reply_text('❌'); return
    msgs=ticket_msgs(tid)
    lines=[f'🆘 <b>#{tid}</b> ({t_["status"]})',f'👤 <code>{t_["user_id"]}</code>','━━━━━━━━━━━━━━━━━━━━','']
    photos=[]
    for m in msgs:
        who='👤' if m['sender']=='user' else '🛠'
        body=m['text'] or ('📷' if m['photo_file_id'] else '')
        lines.append(f'{who} <i>{m["created_at"]}</i>\n{html.escape(body)}')
        if m['photo_file_id']: photos.append((m['photo_file_id'],f'#{tid}'))
    kb=kb_ticket_admin(tid) if t_['status']=='open' else None
    await update.message.reply_text('\n\n'.join(lines),parse_mode=ParseMode.HTML,reply_markup=kb)
    for fid,cap in photos[-10:]:
        try: await update.message.reply_photo(fid,caption=cap)
        except: pass
async def cmd_setbalance(update,context):
    if not is_admin(update.effective_user.id) or len(context.args)!=2:
        await update.message.reply_text('/setbalance ID N'); return
    try: uid=int(context.args[0]); amount=int(context.args[1])
    except ValueError: await update.message.reply_text('❌'); return
    ensure_user_by_id(uid); set_balance_exact(uid,amount)
    await update.message.reply_text(f'✅ <code>{uid}</code> = <b>{amount}</b> 🪙',parse_mode=ParseMode.HTML)
    try: await context.bot.send_message(uid,f'🪙 <b>{amount}</b>',parse_mode=ParseMode.HTML)
    except: pass
async def cmd_addbalance(update,context):
    if not is_admin(update.effective_user.id) or len(context.args)!=2:
        await update.message.reply_text('/addbalance ID N'); return
    try: uid=int(context.args[0]); amount=int(context.args[1])
    except ValueError: await update.message.reply_text('❌'); return
    ensure_user_by_id(uid); change_balance(uid,amount)
    await update.message.reply_text(f'✅ <code>{uid}</code> {amount:+d} → <b>{balance(uid)}</b>',parse_mode=ParseMode.HTML)
async def cmd_setrub(update,context):
    if not is_admin(update.effective_user.id) or len(context.args)!=2:
        await update.message.reply_text('/setrub ID N'); return
    try: uid=int(context.args[0]); amount=int(context.args[1])
    except ValueError: await update.message.reply_text('❌'); return
    ensure_user_by_id(uid); set_rub_exact(uid,amount)
    await update.message.reply_text(f'✅ <code>{uid}</code> = <b>{amount} ₽</b>',parse_mode=ParseMode.HTML)
async def cmd_addrub(update,context):
    if not is_admin(update.effective_user.id) or len(context.args)!=2:
        await update.message.reply_text('/addrub ID N'); return
    try: uid=int(context.args[0]); amount=int(context.args[1])
    except ValueError: await update.message.reply_text('❌'); return
    ensure_user_by_id(uid)
    payouts=topup_rub(uid,amount,method='manual',by_admin=update.effective_user.id)
    msg=f'✅ <code>{uid}</code> +{amount} ₽ → {rub_balance(uid)} ₽'
    for ref,lvl,bonus in payouts:
        msg+=f'\n💸 L{lvl} +{bonus} ₽ → <code>{ref}</code>'
        try: await context.bot.send_message(ref,f'💸 L{lvl} +<b>{bonus} ₽</b> (реф-баланс)',parse_mode=ParseMode.HTML)
        except: pass
    await update.message.reply_text(msg,parse_mode=ParseMode.HTML)
async def cmd_setadmin(update,context):
    if not is_admin(update.effective_user.id) or len(context.args)!=1:
        await update.message.reply_text('/setadmin ID'); return
    try: uid=int(context.args[0])
    except ValueError: await update.message.reply_text('❌'); return
    if uid==ADMIN_ID: await update.message.reply_text('👑'); return
    ensure_user_by_id(uid)
    if is_admin(uid): await update.message.reply_text('ℹ️ Уже админ.'); return
    add_admin(uid,update.effective_user.id)
    await update.message.reply_text(f'👑 <code>{uid}</code> назначен.',parse_mode=ParseMode.HTML)
    try: await context.bot.send_message(uid,'👑 <b>Ты админ.</b>\n/admin',parse_mode=ParseMode.HTML)
    except: pass
async def cmd_unadmin(update,context):
    if not is_admin(update.effective_user.id) or len(context.args)!=1:
        await update.message.reply_text('/unadmin ID'); return
    try: uid=int(context.args[0])
    except ValueError: await update.message.reply_text('❌'); return
    if uid==ADMIN_ID: await update.message.reply_text('❌'); return
    if not is_admin(uid): await update.message.reply_text('ℹ️ Не админ.'); return
    remove_admin(uid)
    await update.message.reply_text(f'✅ <code>{uid}</code> не админ.',parse_mode=ParseMode.HTML)
    try: await context.bot.send_message(uid,'❌ <b>Права сняты.</b>',parse_mode=ParseMode.HTML)
    except: pass
async def cmd_admins(update,context):
    if not is_admin(update.effective_user.id): return
    rows=list_admins()
    lines=['👑 <b>Админы</b>','━━━━━━━━━━━━━━━━━━━━','',f'👑 <code>{ADMIN_ID}</code> — супер-админ']
    for r in rows: lines.append(f'• <code>{r["user_id"]}</code> (by <code>{r["added_by"]}</code>)')
    await update.message.reply_text('\n'.join(lines),parse_mode=ParseMode.HTML)
async def cmd_ban(update,context):
    if not is_admin(update.effective_user.id) or not context.args:
        await update.message.reply_text('/ban ID [причина]'); return
    try: uid=int(context.args[0])
    except ValueError: await update.message.reply_text('❌'); return
    reason=' '.join(context.args[1:]) or '—'
    ensure_user_by_id(uid); set_ban(uid,True,reason,update.effective_user.id)
    await update.message.reply_text(f'⛔ <code>{uid}</code>: {html.escape(reason)}',parse_mode=ParseMode.HTML)
async def cmd_unban(update,context):
    if not is_admin(update.effective_user.id) or len(context.args)!=1:
        await update.message.reply_text('/unban ID'); return
    try: uid=int(context.args[0])
    except ValueError: await update.message.reply_text('❌'); return
    set_ban(uid,False)
    await update.message.reply_text(f'✅ <code>{uid}</code> разбанен.',parse_mode=ParseMode.HTML)
async def cmd_setrate(update,context):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text(f'/setrate N (сейчас {coin_rate()})'); return
    try: v=int(context.args[0])
    except ValueError: await update.message.reply_text('❌'); return
    if v<1: await update.message.reply_text('❌ min 1'); return
    set_setting('coin_rate',v)
    await update.message.reply_text(f'✅ 1 🪙 = {v} ₽',parse_mode=ParseMode.HTML)
async def cmd_setref(update,context):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text(f'/setref N (сейчас {ref_percent()}%)'); return
    try: v=int(context.args[0])
    except ValueError: await update.message.reply_text('❌'); return
    if v<0 or v>100: await update.message.reply_text('❌ 0–100'); return
    set_setting('ref_percent',v)
    await update.message.reply_text(f'✅ {v}%',parse_mode=ParseMode.HTML)
async def cmd_settimeout(update,context):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text(f'/settimeout N (сейчас {get_timeout()})'); return
    try: sec=int(context.args[0])
    except ValueError: await update.message.reply_text('❌'); return
    if sec<30: await update.message.reply_text('❌ min 30'); return
    set_setting('timeout',sec)
    await update.message.reply_text(f'✅ {sec} сек',parse_mode=ParseMode.HTML)
async def cmd_broadcast(update,context):
    if not is_admin(update.effective_user.id): return
    text=' '.join(context.args) if context.args else ''
    if not text:
        context.user_data['admin_broadcast']=True
        await update.message.reply_text('📢 Текст следующим сообщением.'); return
    await do_broadcast(context.application,update,text)
async def cmd_setbanner(update,context):
    uid=update.effective_user.id
    if not is_admin(uid): return
    if not context.args:
        keys_list='\n'.join(f'• <code>{k}</code> — {v}' for k,v in BANNER_KEYS.items())
        await update.message.reply_text(f'🖼 <b>Баннеры</b>\n\nИспользование: <code>/setbanner KEY</code>\n\n<b>Ключи:</b>\n{keys_list}',parse_mode=ParseMode.HTML); return
    key=context.args[0].lower()
    if key not in BANNER_KEYS:
        await update.message.reply_text(f'❌ Ключ <code>{key}</code> не найден.',parse_mode=ParseMode.HTML); return
    context.user_data['admin_banner_upload']=key
    await update.message.reply_text(f'📤 Пришли картинку для баннера <b>{BANNER_KEYS[key]}</b>.',parse_mode=ParseMode.HTML)
async def cmd_banners(update,context):
    if not is_admin(update.effective_user.id): return
    lines=['🖼 <b>Баннеры экранов</b>','━━━━━━━━━━━━━━━━━━━━','']
    for k,n in BANNER_KEYS.items(): lines.append(f'<code>{k}</code> — {n}\n   {banner_source(k)}')
    lines.append(''); lines.append('<i>Управление: /admin → 🖼 Баннеры</i>')
    await update.message.reply_text('\n'.join(lines),parse_mode=ParseMode.HTML)
async def cmd_delbanner(update,context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text('/delbanner KEY'); return
    key=context.args[0].lower()
    if key not in BANNER_KEYS: await update.message.reply_text('❌ Неизвестный ключ.'); return
    delete_banner(key)
    await update.message.reply_text(f'❌ Баннер <b>{BANNER_KEYS[key]}</b> удалён. Источник: {banner_source(key)}',parse_mode=ParseMode.HTML)
async def cmd_apis(update,context):
    if not is_admin(update.effective_user.id): return
    rows=api_list()
    if not rows:
        await update.message.reply_text('📡 API нет — используется конфиг.\n\nУправление: /admin → 📡 API',parse_mode=ParseMode.HTML); return
    lines=['📡 <b>API</b>','━━━━━━━━━━━━━━━━━━━━','']
    for r in rows:
        icon='✅' if r['active'] else '⚪'
        lines.append(f'{icon} <b>#{r["id"]}</b> [{r["type"]}] {html.escape(r["name"] or "—")} • p{r["priority"]}')
        lines.append(f'   🌐 <code>{html.escape(r["base_url"])}</code>')
        lines.append(f'   🎨 <code>{html.escape(r["model"])}</code>')
    await update.message.reply_text('\n'.join(lines),parse_mode=ParseMode.HTML)
async def cmd_setadv(update,context):
    if not is_admin(update.effective_user.id): return
    if len(context.args)<2:
        await update.message.reply_text('Использование: /setadv ID CODE [PERCENT]'); return
    try: uid=int(context.args[0])
    except ValueError: await update.message.reply_text('❌'); return
    code=context.args[1].lower().replace(' ','')
    if not code or len(code)>30: await update.message.reply_text('❌ 1–30 символов.'); return
    if adv_get_by_code(code): await update.message.reply_text('❌ Такой код уже есть.'); return
    pct=ADV_DEFAULT_PERCENT
    if len(context.args)>=3:
        try: pct=int(context.args[2])
        except ValueError: await update.message.reply_text('❌ Процент — число.'); return
        if pct<1 or pct>50: await update.message.reply_text('❌ 1–50%.'); return
    ensure_user_by_id(uid)
    if adv_create(uid,code,pct):
        await update.message.reply_text(f'✅ Инфлюенсер назначен\n\n👤 <code>{uid}</code>\n🎯 Код: <code>{code}</code>\n💸 Процент: <b>{pct}%</b>\n🔗 <code>{adv_link(code)}</code>',parse_mode=ParseMode.HTML)
    else: await update.message.reply_text('❌ Ошибка создания.')
async def cmd_deladv(update,context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text('/deladv CODE'); return
    code=context.args[0].lower(); adv_delete(code)
    await update.message.reply_text(f'✅ <code>{code}</code> удалён.',parse_mode=ParseMode.HTML)
async def cmd_advs(update,context):
    if not is_admin(update.effective_user.id): return
    rows=adv_list()
    if not rows: await update.message.reply_text('🎯 Список пуст.'); return
    lines=['🎯 <b>Инфлюенсеры</b>','━━━━━━━━━━━━━━━━━━━━','']
    for r in rows:
        lines.append(f'👤 <code>{r["user_id"]}</code> • <code>{r["code"]}</code> • {r["percent"]}%')
        lines.append(f'   🔗 <code>{adv_link(r["code"])}</code>')
    await update.message.reply_text('\n'.join(lines),parse_mode=ParseMode.HTML)

# ═══════════ LIFECYCLE ═══════════
async def post_init(app):
    init_db()
    setting('image_cost'); setting('coin_rate'); setting('ref_percent')
    setting('timeout'); setting('rate_limit_count'); setting('rate_limit_window')
    setting('start_balance'); setting('max_concurrent')
    setting('premium_stars'); setting('premium_days'); setting('premium_cooldown'); setting('rush_cost')
    n=int(setting('max_concurrent','1'))
    for _ in range(n): workers.append(asyncio.create_task(worker(app)))
    workers.append(asyncio.create_task(queue_position_updater(app)))
    await upload_banner_files(app)
    inline_prompt_purge()
    banners_have=list_banners()
    banners_files=sum(1 for k in BANNER_KEYS if banner_file(k))
    banners_db=sum(1 for k in BANNER_KEYS if db_has_banner(k))
    banners_cache=sum(1 for k in BANNER_KEYS if banner_cache_get(k))
    apis_img=len(api_list('image')); apis_mod=len(api_list('mod'))
    adv_count=len(adv_list())
    prem_count=db().execute('SELECT COUNT(*) AS n FROM premium WHERE expires_at>?',(datetime.now().isoformat(timespec='seconds'),)).fetchone()['n']
    await alog(app,
        f'🟢 <b>ImagesGPT запущен</b>\n👷 Воркеров: <code>{n}</code>\n🎨 <code>{IMAGE_MODEL}</code>\n'
        f'⏱ Таймаут: <code>{fmt_timeout()}</code>\n🕒 Кулдаун: <code>{GEN_COOLDOWN}с / Premium {setting("premium_cooldown",str(PREMIUM_COOLDOWN))}с</code>\n'
        f'📊 Курс: <code>1 🪙 = {coin_rate()} ₽</code>\n💸 Реф: <code>L1 {REF_L1}% • L2 {REF_L2}%</code>\n'
        f'⏳ Rate-limit: <code>{rate_limit_count()}/{rate_limit_window()}с</code>\n🎯 Инфлюенсеров: <code>{adv_count}</code>\n'
        f'💎 Premium активных: <code>{prem_count}</code>\n🚀 Ускорение: <code>{setting("rush_cost",str(RUSH_COST))} 🪙</code>\n'
        f'🖼 Баннеры: <code>{len(banners_have)}/{len(BANNER_KEYS)}</code> (📁{banners_files} • ✅{banners_db} • ⚡{banners_cache})\n'
        f'📡 API: 🖼{apis_img} 🧠{apis_mod}\n🌐 Режим: <code>{"webhook" if PUBLIC_DOMAIN else "polling"}</code>\n🤖 <code>@{BOT_USERNAME}</code>',
        level=1)

async def post_shutdown(app):
    for w in workers: w.cancel()
    await asyncio.gather(*workers,return_exceptions=True)
    if _db is not None: _db.close()

async def on_error(update,context):
    log.error('Ошибка в хендлере: %s',context.error,exc_info=context.error)
    try:
        await context.application.bot.send_message(ADMIN_ID,f'⚠️ <b>Ошибка</b>\n<code>{html.escape(str(context.error)[:800])}</code>',parse_mode=ParseMode.HTML)
    except: pass

def build_app():
    app=(Application.builder().token(BOT_TOKEN).post_init(post_init).post_shutdown(post_shutdown).build())
    app.add_handler(CommandHandler('start',cmd_start))
    app.add_handler(CommandHandler('help',cmd_help))
    app.add_handler(CommandHandler('premium',cmd_premium))
    app.add_handler(CommandHandler('ref_history',cmd_ref_history))
    app.add_handler(CommandHandler('admin',cmd_admin))
    app.add_handler(CommandHandler('admin_help',cmd_admin_help))
    app.add_handler(CommandHandler('botbalance',cmd_botbalance))
    app.add_handler(CommandHandler('givepremium',cmd_givepremium))
    app.add_handler(CommandHandler('unpremium',cmd_unpremium))
    app.add_handler(CommandHandler('stats',cmd_stats))
    app.add_handler(CommandHandler('user',cmd_user))
    app.add_handler(CommandHandler('ticket',cmd_ticket))
    app.add_handler(CommandHandler('setbalance',cmd_setbalance))
    app.add_handler(CommandHandler('addbalance',cmd_addbalance))
    app.add_handler(CommandHandler('setrub',cmd_setrub))
    app.add_handler(CommandHandler('addrub',cmd_addrub))
    app.add_handler(CommandHandler('setadmin',cmd_setadmin))
    app.add_handler(CommandHandler('unadmin',cmd_unadmin))
    app.add_handler(CommandHandler('admins',cmd_admins))
    app.add_handler(CommandHandler('ban',cmd_ban))
    app.add_handler(CommandHandler('unban',cmd_unban))
    app.add_handler(CommandHandler('setrate',cmd_setrate))
    app.add_handler(CommandHandler('setref',cmd_setref))
    app.add_handler(CommandHandler('settimeout',cmd_settimeout))
    app.add_handler(CommandHandler('broadcast',cmd_broadcast))
    app.add_handler(CommandHandler('setbanner',cmd_setbanner))
    app.add_handler(CommandHandler('banners',cmd_banners))
    app.add_handler(CommandHandler('delbanner',cmd_delbanner))
    app.add_handler(CommandHandler('apis',cmd_apis))
    app.add_handler(CommandHandler('setadv',cmd_setadv))
    app.add_handler(CommandHandler('deladv',cmd_deladv))
    app.add_handler(CommandHandler('advs',cmd_advs))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT,on_successful_payment))
    app.add_handler(InlineQueryHandler(on_inline_query))
    app.add_handler(ChosenInlineResultHandler(on_chosen_inline))
    app.add_handler(CallbackQueryHandler(on_callbacks))
    app.add_handler(MessageHandler((filters.TEXT & ~filters.COMMAND) | filters.PHOTO,on_message))
    app.add_error_handler(on_error)
    return app

def run_once():
    app=build_app()
    if PUBLIC_DOMAIN:
        webhook_url=f'https://{PUBLIC_DOMAIN}{WEBHOOK_PATH}'
        log.info('Webhook: %s',webhook_url)
        app.run_webhook(listen='0.0.0.0',port=PORT,url_path=WEBHOOK_PATH,webhook_url=webhook_url,
            drop_pending_updates=False,allowed_updates=Update.ALL_TYPES)
    else:
        log.info('Polling mode (no RAILWAY_PUBLIC_DOMAIN)')
        app.run_polling(allowed_updates=Update.ALL_TYPES,drop_pending_updates=False)

def main_loop():
    last_error=None; same_error_count=0; MAX_SAME=5
    while True:
        try:
            log.info('Запуск бота…'); run_once(); log.info('Остановлен.'); break
        except KeyboardInterrupt: log.info('Ctrl+C'); break
        except SystemExit: break
        except Exception as e:
            err=f'{type(e).__name__}: {e}'
            log.error('💥 Упал: %s\n%s',err,traceback.format_exc())
            if err==last_error: same_error_count+=1
            else: same_error_count=1; last_error=err
            if same_error_count>=MAX_SAME:
                log.error('❌ %s раз одна и та же ошибка. Стоп.',same_error_count); break
            delay=15 if 'Conflict' in err else 5
            log.info('Перезапуск через %s сек…',delay); time.sleep(delay)

if __name__=='__main__':
    main_loop()