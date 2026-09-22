import asyncio, base64, html, logging, sqlite3, time, uuid, traceback, random, os
from datetime import datetime, timedelta
import httpx
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, LabeledPrice
)
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters, PreCheckoutQueryHandler
)

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
BOT_TOKEN  = '8979688376:AAG_QM3t0NKOEiieC3_38wvb-ZsmziaXzRE'
ADMIN_ID   = 8130244626
API_KEY    = 'tc_live_6a7075340c595455d423a0471dc7a534d8450dddd9c6de39'
API_BASE   = 'https://tooken.club/v1'
IMAGE_MODEL      = 'gpt-image-2'
MODERATION_MODEL = 'deepseek-v4-flash'
TIMEOUT_DEFAULT  = 600
DB         = 'gptimages.db'
PRIVACY_URL = 'https://telegra.ph/POLITIKA-KONFIDENCIALNOSTI-08-12-99'
OFFER_URL   = 'https://telegra.ph/PUBLICHNAYA-OFERTA-08-12-15'
BOT_USERNAME = 'ImagesGPT_bot'
HISTORY_PAGE_SIZE = 10
CAPTION_MAX = 1000
STAR_RATE = 1.3
STAR_PACKS = [(10,0),(25,0),(50,5),(100,15)]
REF_L1 = 10
REF_L2 = 5
ROULETTE_COOLDOWN_HOURS = 24
ROULETTE_PRIZES = [(0,20),(1,35),(2,25),(3,12),(5,6),(10,2)]

BANNERS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'banners')
BANNER_KEYS = {
    'menu':'Главное меню','balance':'Баланс','topup':'Пополнение','exchange':'Обмен рублей',
    'history':'История','promo':'Промокод','ref':'Партнёрка','support':'Поддержка',
    'help':'Помощь','lang':'Язык',
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
log = logging.getLogger('ImagesGPT')

# ═══════════════════════════════════════════════════════════
#  I18N
# ═══════════════════════════════════════════════════════════
LANGS=('ru','en')
LANGS_NAMES={'ru':'🇷🇺 Русский','en':'🇬🇧 English'}
TR={
'ru':{
'menu_title':'🤖 <b>ImagesGPT</b>','balance':'💰 Баланс','topup':'💳 Пополнить','history':'📜 История',
'promo':'🎁 Промокод','ref':'👥 Пригласить друга','support':'🆘 Поддержка','help':'ℹ️ Помощь',
'lang':'🌐 Язык','roulette':'🎰 Рулетка','create_btn':'🎨 Создать изображение',
'back_menu':'◀️ В меню','back':'◀️ Назад','cancel':'❌ Отмена','rubles':'Рубли','coins':'Монеты',
'rate':'Курс','gen_cost':'Генерация','choose_action':'Выбери действие ниже 👇',
'your_balance':'💰 <b>Баланс</b>\n━━━━━━━━━━━━━━━━━━━━','topup_title':'💳 <b>Пополнение баланса</b>',
'support_btn':'🆘 Написать в поддержку','exchange_btn':'🔄 Обменять на монеты',
'exchange_title':'🔄 <b>Обмен рублей на монеты</b>','exchange_ask':'Напиши, сколько рублей хочешь обменять:',
'exchange_must_be_multiple':'Сумма должна быть кратна {rate} ₽','exchange_done':'✅ <b>Обмен выполнен</b>',
'exchange_spent':'Списано','exchange_got':'Получено','history_empty':'📜 <b>История пуста.</b>',
'history_title':'📜 <b>Последние генерации</b>','history_hint':'<i>Нажми на номер, чтобы открыть.</i>',
'history_not_found':'❌ Запись не найдена','history_failed':'❌ <i>Генерация не завершилась успешно</i>',
'history_img_unavail':'⚠️ <i>Картинка недоступна</i>','ref_title':'👥 <b>Пригласить друга</b>',
'ref_your_link':'🔗 Твоя ссылка:','ref_you_get':'💸 Ты получаешь <b>{percent}%</b> с пополнений друзей.',
'ref_earn_rub':'💵 Заработанное начисляется в рублях.','ref_invited':'👤 Приглашено','ref_earned':'💵 Заработано',
'ref_share':'📤 Поделиться','ref_note':'<i>Бонус начисляется автоматически при пополнении друга.</i>',
'promo_ask':'🎁 <b>Введи промокод:</b>','promo_ok':'🎉 Промокод активирован!',
'promo_credited':'Начислено: <b>+{n}</b> монет','support_title':'🆘 <b>Поддержка</b>',
'support_open_exists':'У тебя есть открытый тикет <b>#{tid}</b>.\nМожешь продолжить или создать новый.',
'support_desc':'Опиши проблему — ответим как можно скорее.\nМожно прикрепить фото.',
'support_new':'✍️ Создать новый тикет','support_my':'📋 Мои тикеты',
'support_continue':'💬 Продолжить тикет #{tid}','support_create_ask':'✍️ <b>Опиши проблему</b> (текст или фото):',
'support_created':'✅ <b>Тикет #{tid} создан.</b>\n\nОтветим в ближайшее время.','support_none':'📋 У тебя пока нет тикетов.',
'support_my_title':'📋 <b>Твои тикеты</b>','help_title':'ℹ️ <b>Помощь</b>',
'help_text':('🎨 <b>Создать изображение</b> — описание → размер → картинка.\n\n'
'💰 <b>Баланс</b> — рубли и монеты, обмен.\n\n💳 <b>Пополнить</b> — через Telegram Stars.\n\n'
'🎰 <b>Рулетка</b> — раз в 24 часа крути монеты.\n\n📜 <b>История</b> — список генераций.\n\n'
'👥 <b>Пригласить друга</b> — {percent}% с пополнений (2 уровня).\n\n🎁 <b>Промокод</b> — бонусный код.\n\n'
'🆘 <b>Поддержка</b> — тикет.'),
'insufficient_coins':'❌ Недостаточно монет.','need_coins':'Нужно: <b>{need} 🪙</b>\nУ тебя: <b>{have} 🪙</b>',
'create_prompt':'🎨 <b>Напиши описание изображения:</b>\n\nМаксимум 4000 символов.',
'checking':'🔎 Проверяю запрос…','blocked':'❌ <b>Запрос отклонён.</b>','choose_size':'📐 <b>Выбери размер:</b>',
'size_1024':'🟦 1024×1024','confirm_title':'🎨 <b>Проверь запрос</b>','confirm_create':'✅ Создать',
'queue_title':'⏳ <b>В очереди</b>','queue_pos':'Позиция','queue_cancel':'❌ Отменить и вернуть монету',
'in_progress':'🎨 <b>Генерирую…</b>\nОбычно 30–90 секунд.\nЛимит: {limit}.','done_title':'✅ <b>Готово!</b>',
'time_label':'⏱ Время','left_coins':'💰 Осталось','timeout':'⏱ Генерация превысила лимит ({limit}). Монета возвращена.',
'error_gen':'❌ Ошибка генерации. Монета возвращена.','terms_title':'📄 <b>Перед началом работы</b>',
'terms_lead':'Ознакомься с документами:','terms_privacy':'🔒 Политика конфиденциальности',
'terms_offer':'📜 Пользовательское соглашение','terms_note':'Для использования бота необходимо принять условия.',
'terms_accept':'✅ Согласен с условиями','terms_reject':'❌ Отклонить','terms_accepted':'✅ Условия приняты.',
'terms_rejected':'❌ Вы отклонили условия.\n\nДоступ закрыт. Если передумаете — /start.',
'terms_first':'❌ Сначала примите условия. Отправьте /start.','banned_access':'⛔ Доступ ограничен.',
'banned_title':'⛔ <b>Доступ к боту ограничен.</b>','banned_reason':'Причина','menu_hint':'Выбери действие в меню 👇',
'lang_title':'🌐 <b>Выбор языка</b>','lang_current':'Текущий язык','lang_switched':'✅ Язык: {lang}',
'rate_limit':'⏱ Слишком часто. Подожди ещё {sec} сек.','not_enough_rub':'❌ Недостаточно рублей.',
'min_exchange':'Минимум для обмена','you_have':'У тебя','ticket_msg_added':'📩 Сообщение добавлено в тикет #{tid}.',
'ticket_closed':'🔒 Тикет #{tid} закрыт.','support_reply':'💬 <b>Ответ поддержки (тикет #{tid}):</b>',
'reply_here':'Ответь сюда, чтобы продолжить.','roulette_title':'🎰 <b>Рулетка</b>',
'roulette_rules':'Раз в 24 часа бесплатно крути барабан.\n\nВозможные призы: 0, 1, 2, 3, 5, 10 монет.',
'roulette_spin':'🎰 Крутить','roulette_spinning':'🎰 <b>Крутим…</b>','roulette_won':'🎉 <b>Ты выиграл {n} 🪙!</b>',
'roulette_empty':'💨 <b>Пусто.</b> Сегодня не повезло.','roulette_cooldown':'⏱ Следующая попытка через <b>{time}</b>',
'roulette_done':'✅ Приходи через 24 часа!',
},
'en':{
'menu_title':'🤖 <b>ImagesGPT</b>','balance':'💰 Balance','topup':'💳 Top up','history':'📜 History',
'promo':'🎁 Promo code','ref':'👥 Invite a friend','support':'🆘 Support','help':'ℹ️ Help',
'lang':'🌐 Language','roulette':'🎰 Roulette','create_btn':'🎨 Create image',
'back_menu':'◀️ Menu','back':'◀️ Back','cancel':'❌ Cancel','rubles':'Rubles','coins':'Coins',
'rate':'Rate','gen_cost':'Generation','choose_action':'Choose an action 👇',
'your_balance':'💰 <b>Balance</b>\n━━━━━━━━━━━━━━━━━━━━','topup_title':'💳 <b>Top up balance</b>',
'support_btn':'🆘 Contact support','exchange_btn':'🔄 Exchange to coins',
'exchange_title':'🔄 <b>Exchange rubles to coins</b>','exchange_ask':'How many rubles?',
'exchange_must_be_multiple':'Must be a multiple of {rate} ₽','exchange_done':'✅ <b>Exchange complete</b>',
'exchange_spent':'Spent','exchange_got':'Received','history_empty':'📜 <b>History is empty.</b>',
'history_title':'📜 <b>Recent generations</b>','history_hint':'<i>Tap a number to open.</i>',
'history_not_found':'❌ Not found','history_failed':'❌ <i>Generation failed</i>',
'history_img_unavail':'⚠️ <i>Image unavailable</i>','ref_title':'👥 <b>Invite a friend</b>',
'ref_your_link':'🔗 Your link:','ref_you_get':'💸 You get <b>{percent}%</b> of friend top-ups.',
'ref_earn_rub':'💵 Earnings credited in rubles.','ref_invited':'👤 Invited','ref_earned':'💵 Earned',
'ref_share':'📤 Share','ref_note':'<i>Bonus credited automatically on friend top-up.</i>',
'promo_ask':'🎁 <b>Enter promo code:</b>','promo_ok':'🎉 Promo activated!',
'promo_credited':'Credited: <b>+{n}</b> coins','support_title':'🆘 <b>Support</b>',
'support_open_exists':'You have an open ticket <b>#{tid}</b>.','support_desc':'Describe your issue — we will reply soon.',
'support_new':'✍️ Create new ticket','support_my':'📋 My tickets','support_continue':'💬 Continue ticket #{tid}',
'support_create_ask':'✍️ <b>Describe the issue</b> (text or photo):','support_created':'✅ <b>Ticket #{tid} created.</b>',
'support_none':'📋 You have no tickets yet.','support_my_title':'📋 <b>Your tickets</b>','help_title':'ℹ️ <b>Help</b>',
'help_text':('🎨 <b>Create image</b> — prompt → size → picture.\n\n💰 <b>Balance</b> — rubles and coins.\n\n'
'💳 <b>Top up</b> — via Telegram Stars.\n\n🎰 <b>Roulette</b> — free coins every 24h.\n\n'
'📜 <b>History</b> — list of generations.\n\n👥 <b>Invite a friend</b> — {percent}% of top-ups (2 levels).\n\n'
'🎁 <b>Promo code</b> — bonus code.\n\n🆘 <b>Support</b> — ticket.'),
'insufficient_coins':'❌ Not enough coins.','need_coins':'Needed: <b>{need} 🪙</b>\nYou have: <b>{have} 🪙</b>',
'create_prompt':'🎨 <b>Write a description:</b>\n\nMax 4000 chars.','checking':'🔎 Checking prompt…',
'blocked':'❌ <b>Request blocked.</b>','choose_size':'📐 <b>Choose size:</b>','size_1024':'🟦 1024×1024',
'confirm_title':'🎨 <b>Confirm request</b>','confirm_create':'✅ Create','queue_title':'⏳ <b>In queue</b>',
'queue_pos':'Position','queue_cancel':'❌ Cancel and refund coin',
'in_progress':'🎨 <b>Generating…</b>\nUsually 30–90 sec.\nLimit: {limit}.','done_title':'✅ <b>Done!</b>',
'time_label':'⏱ Time','left_coins':'💰 Left','timeout':'⏱ Generation exceeded limit ({limit}). Coin refunded.',
'error_gen':'❌ Generation error. Coin refunded.','terms_title':'📄 <b>Before you start</b>',
'terms_lead':'Please review the documents:','terms_privacy':'🔒 Privacy Policy','terms_offer':'📜 Terms of Service',
'terms_note':'You must accept the terms to use the bot.','terms_accept':'✅ I agree to the terms',
'terms_reject':'❌ Decline','terms_accepted':'✅ Terms accepted.',
'terms_rejected':'❌ You declined the terms.\n\nAccess closed. If you change your mind — /start.',
'terms_first':'❌ Please accept the terms first. Send /start.','banned_access':'⛔ Access denied.',
'banned_title':'⛔ <b>Access restricted.</b>','banned_reason':'Reason','menu_hint':'Choose an action in the menu 👇',
'lang_title':'🌐 <b>Language selection</b>','lang_current':'Current language','lang_switched':'✅ Language: {lang}',
'rate_limit':'⏱ Too often. Wait {sec} more sec.','not_enough_rub':'❌ Not enough rubles.',
'min_exchange':'Minimum for exchange','you_have':'You have','ticket_msg_added':'📩 Message added to ticket #{tid}.',
'ticket_closed':'🔒 Ticket #{tid} closed.','support_reply':'💬 <b>Support reply (ticket #{tid}):</b>',
'reply_here':'Reply here to continue.','roulette_title':'🎰 <b>Roulette</b>',
'roulette_rules':'Free spin every 24 hours.\n\nPossible prizes: 0, 1, 2, 3, 5, 10 coins.',
'roulette_spin':'🎰 Spin','roulette_spinning':'🎰 <b>Spinning…</b>','roulette_won':'🎉 <b>You won {n} 🪙!</b>',
'roulette_empty':'💨 <b>Empty.</b> No luck today.','roulette_cooldown':'⏱ Next attempt in <b>{time}</b>',
'roulette_done':'✅ Come back in 24 hours!',
},
}

# ═══════════════════════════════════════════════════════════
#  DB
# ═══════════════════════════════════════════════════════════
_db=None
def db():
    global _db
    if _db is None:
        _db=sqlite3.connect(DB,check_same_thread=False)
        _db.row_factory=sqlite3.Row
    return _db

def init_db():
    c=db()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT,
            balance INTEGER NOT NULL DEFAULT 0, rub_balance INTEGER NOT NULL DEFAULT 0,
            created_at TEXT, last_seen TEXT, terms_accepted INTEGER NOT NULL DEFAULT 0,
            banned INTEGER NOT NULL DEFAULT 0, ban_reason TEXT, banned_at TEXT, banned_by INTEGER,
            referred_by INTEGER, ref_reward_given INTEGER NOT NULL DEFAULT 0, lang TEXT DEFAULT 'ru');
        CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            prompt TEXT, size TEXT, status TEXT, created_at TEXT, file_id TEXT, elapsed REAL);
        CREATE TABLE IF NOT EXISTS tickets(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'open', created_at TEXT, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS ticket_messages(id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_id INTEGER NOT NULL,
            sender TEXT NOT NULL, text TEXT, photo_file_id TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS referrals(id INTEGER PRIMARY KEY AUTOINCREMENT, inviter_id INTEGER,
            invited_id INTEGER, reward_paid INTEGER NOT NULL DEFAULT 0, created_at TEXT);
        CREATE TABLE IF NOT EXISTS promo_codes(code TEXT PRIMARY KEY, amount INTEGER NOT NULL,
            uses_left INTEGER NOT NULL, total_uses INTEGER NOT NULL, expires_at TEXT,
            created_by INTEGER, created_at TEXT);
        CREATE TABLE IF NOT EXISTS promo_uses(id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT,
            user_id INTEGER, created_at TEXT);
        CREATE TABLE IF NOT EXISTS topups(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL, method TEXT, created_at TEXT, by_admin INTEGER);
        CREATE TABLE IF NOT EXISTS ref_earnings(id INTEGER PRIMARY KEY AUTOINCREMENT, referrer_id INTEGER NOT NULL,
            referred_id INTEGER NOT NULL, amount INTEGER NOT NULL, source_topup_id INTEGER, created_at TEXT);
        CREATE TABLE IF NOT EXISTS admins(user_id INTEGER PRIMARY KEY, added_by INTEGER, added_at TEXT);
        CREATE TABLE IF NOT EXISTS banners(key TEXT PRIMARY KEY, file_id TEXT NOT NULL, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS apis(id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, name TEXT,
            base_url TEXT NOT NULL, api_key TEXT NOT NULL, model TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
            priority INTEGER NOT NULL DEFAULT 100, created_at TEXT);
        CREATE TABLE IF NOT EXISTS roulette_spins(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            prize INTEGER NOT NULL, spun_at TEXT);
        CREATE TABLE IF NOT EXISTS stars_payments(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            stars INTEGER, rub INTEGER, charge_id TEXT UNIQUE, created_at TEXT);
    ''')
    for stmt in [
        'ALTER TABLE users ADD COLUMN banned INTEGER NOT NULL DEFAULT 0',
        'ALTER TABLE users ADD COLUMN ban_reason TEXT',
        'ALTER TABLE users ADD COLUMN banned_at TEXT','ALTER TABLE users ADD COLUMN banned_by INTEGER',
        'ALTER TABLE users ADD COLUMN referred_by INTEGER',
        'ALTER TABLE users ADD COLUMN ref_reward_given INTEGER NOT NULL DEFAULT 0',
        'ALTER TABLE users ADD COLUMN rub_balance INTEGER NOT NULL DEFAULT 0',
        'ALTER TABLE users ADD COLUMN lang TEXT DEFAULT "ru"',
        'ALTER TABLE history ADD COLUMN file_id TEXT','ALTER TABLE history ADD COLUMN elapsed REAL',
        'ALTER TABLE ticket_messages ADD COLUMN photo_file_id TEXT',
        'CREATE INDEX IF NOT EXISTS idx_history_user ON history(user_id, id DESC)',
    ]:
        try: c.execute(stmt)
        except sqlite3.OperationalError: pass
    for k,v in {'log_level':'2','max_concurrent':'1','image_cost':'1','start_balance':'1',
        'coin_rate':'2','ref_percent':'10','timeout':str(TIMEOUT_DEFAULT),
        'rate_limit_count':'5','rate_limit_window':'60'}.items():
        c.execute('INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)',(k,v))
    c.commit()

def setting(key,default=None):
    r=db().execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
    return r['value'] if r else default
def set_setting(key,value):
    c=db(); c.execute('INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)',(key,str(value))); c.commit()
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
    try: return max(1,int(setting('rate_limit_count','5')))
    except: return 5
def rate_limit_window():
    try: return max(5,int(setting('rate_limit_window','60')))
    except: return 60

# ═══════════════════════════════════════════════════════════
#  BANNERS (DB + файлы из репозитория)
# ═══════════════════════════════════════════════════════════
def banner_file(key):
    p=os.path.join(BANNERS_DIR,f'{key}.png')
    return p if os.path.isfile(p) else None

def db_has_banner(key):
    return bool(db().execute('SELECT 1 FROM banners WHERE key=?',(key,)).fetchone())

def get_banner(key):
    """Возвращает ('id', file_id) | ('file', path) | None."""
    r=db().execute('SELECT file_id FROM banners WHERE key=?',(key,)).fetchone()
    if r: return ('id', r['file_id'])
    p=banner_file(key)
    if p: return ('file', p)
    return None

def set_banner(key,fid):
    c=db(); c.execute('INSERT OR REPLACE INTO banners(key,file_id,updated_at) VALUES(?,?,?)',
        (key,fid,datetime.now().isoformat(timespec='seconds'))); c.commit()
def delete_banner(key):
    c=db(); c.execute('DELETE FROM banners WHERE key=?',(key,)); c.commit()

def list_banners():
    """Все доступные ключи: из БД + из файлов."""
    have={r['key'] for r in db().execute('SELECT key FROM banners').fetchall()}
    if os.path.isdir(BANNERS_DIR):
        for f in os.listdir(BANNERS_DIR):
            if f.endswith('.png'):
                k=f[:-4]
                if k in BANNER_KEYS: have.add(k)
    return have

def banner_source(key):
    """Возвращает описание источника для админского UI."""
    has_db=db_has_banner(key); has_file=bool(banner_file(key))
    if has_db and has_file: return '✅ БД (перекрывает файл) + 📁 файл в репо'
    if has_db: return '✅ загружен через бота (БД)'
    if has_file: return '📁 файл из репозитория'
    return '⬜ нет'

def _strip_header(bkey,text):
    if not bkey: return text
    if not get_banner(bkey): return text
    lines=text.split('\n')
    if len(lines)>=2 and lines[1].strip() and set(lines[1].strip())<={'━'}:
        return '\n'.join(lines[2:]).lstrip('\n')
    return text

# ═══════════════════════════════════════════════════════════
#  SCREENS
# ═══════════════════════════════════════════════════════════
async def show_screen(q, context, uid, bkey, text, kb):
    msg=q.message
    banner=get_banner(bkey) if bkey else None
    use_photo=bool(banner) and len(text)<=CAPTION_MAX
    was_photo=bool(msg.photo)
    if use_photo:
        text=_strip_header(bkey,text)
        try:
            btype,bval=banner
            if btype=='id':
                media=InputMediaPhoto(media=bval,caption=text,parse_mode=ParseMode.HTML)
            else:
                media=InputMediaPhoto(media=open(bval,'rb'),caption=text,parse_mode=ParseMode.HTML)
            await msg.edit_media(media=media,reply_markup=kb)
            return
        except Exception as e:
            log.warning('edit_media: %s',e)
    if was_photo:
        try: await msg.delete()
        except: pass
        try:
            if use_photo:
                btype,bval=banner
                if btype=='id': await context.bot.send_photo(msg.chat_id,bval,caption=text,parse_mode=ParseMode.HTML,reply_markup=kb)
                else: await context.bot.send_photo(msg.chat_id,open(bval,'rb'),caption=text,parse_mode=ParseMode.HTML,reply_markup=kb)
            else:
                await context.bot.send_message(msg.chat_id,text,parse_mode=ParseMode.HTML,reply_markup=kb)
        except Exception as e:
            log.warning('send fb: %s',e)
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
            else:
                await context.bot.send_message(msg.chat_id,text,parse_mode=ParseMode.HTML,reply_markup=kb)
        except: pass

async def send_screen(update, uid, bkey, text, kb):
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
        except Exception as e:
            log.warning('send_photo: %s',e)
    await chat.send_message(text,parse_mode=ParseMode.HTML,reply_markup=kb)

# ═══════════════════════════════════════════════════════════
#  API
# ═══════════════════════════════════════════════════════════
def api_list(typ=None):
    if typ: return db().execute('SELECT * FROM apis WHERE type=? ORDER BY priority ASC, id ASC',(typ,)).fetchall()
    return db().execute('SELECT * FROM apis ORDER BY type, priority ASC, id ASC').fetchall()
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
    rows=db().execute('SELECT * FROM apis WHERE type=? AND active=1 ORDER BY priority ASC, id ASC',(typ,)).fetchall()
    if rows: return list(rows)
    if typ=='image':
        return [{'id':0,'name':'env','base_url':API_BASE,'api_key':API_KEY,'model':IMAGE_MODEL}]
    return [{'id':0,'name':'env','base_url':API_BASE,'api_key':API_KEY,'model':MODERATION_MODEL}]

# ═══════════════════════════════════════════════════════════
#  STARS
# ═══════════════════════════════════════════════════════════
def stars_payment_exists(cid):
    return bool(db().execute('SELECT 1 FROM stars_payments WHERE charge_id=?',(cid,)).fetchone())
def add_stars_payment(uid,stars,rub,cid):
    c=db(); c.execute('INSERT INTO stars_payments(user_id,stars,rub,charge_id,created_at) VALUES(?,?,?,?,?)',
        (uid,stars,rub,cid,datetime.now().isoformat(timespec='seconds'))); c.commit()

# ═══════════════════════════════════════════════════════════
#  ROULETTE
# ═══════════════════════════════════════════════════════════
def roulette_last(uid):
    return db().execute('SELECT spun_at FROM roulette_spins WHERE user_id=? ORDER BY id DESC LIMIT 1',(uid,)).fetchone()
def roulette_can_spin(uid):
    last=roulette_last(uid)
    if not last: return True,0
    try:
        delta=datetime.now()-datetime.fromisoformat(last['spun_at'])
        cd=timedelta(hours=ROULETTE_COOLDOWN_HOURS)
        if delta>=cd: return True,0
        return False,int((cd-delta).total_seconds())
    except: return True,0
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

# ═══════════════════════════════════════════════════════════
#  RATE LIMIT
# ═══════════════════════════════════════════════════════════
_rate_log={}
def check_rate(uid):
    limit=rate_limit_count(); window=rate_limit_window(); now=time.time()
    times=[x for x in _rate_log.get(uid,[]) if now-x<window]
    if len(times)>=limit:
        wait=int(window-(now-times[0]))+1; _rate_log[uid]=times; return False,wait
    times.append(now); _rate_log[uid]=times; return True,0

# ═══════════════════════════════════════════════════════════
#  ADMINS
# ═══════════════════════════════════════════════════════════
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
    return db().execute('SELECT user_id, added_by, added_at FROM admins ORDER BY added_at').fetchall()

# ═══════════════════════════════════════════════════════════
#  USERS
# ═══════════════════════════════════════════════════════════
def ensure_user(u):
    c=db(); now=datetime.now().isoformat(timespec='seconds')
    r=c.execute('SELECT user_id FROM users WHERE user_id=?',(u.id,)).fetchone()
    if r is None:
        sb=int(setting('start_balance','1'))
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
        sb=int(setting('start_balance','1'))
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
def change_balance(uid,n):
    c=db(); c.execute('UPDATE users SET balance=balance+? WHERE user_id=?',(n,uid)); c.commit()
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
        c.execute('UPDATE users SET banned=1, ban_reason=?, banned_at=?, banned_by=? WHERE user_id=?',
            (reason or '',datetime.now().isoformat(timespec='seconds'),by,uid))
    else:
        c.execute('UPDATE users SET banned=0, ban_reason=NULL, banned_at=NULL, banned_by=NULL WHERE user_id=?',(uid,))
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
    r=db().execute('SELECT AVG(elapsed) AS a, MIN(elapsed) AS mn, MAX(elapsed) AS mx, COUNT(elapsed) AS c FROM history WHERE status="success" AND elapsed IS NOT NULL').fetchone()
    return (r['a'] or 0, r['mn'] or 0, r['mx'] or 0, r['c'] or 0)

# ═══════════════════════════════════════════════════════════
#  RUB / REFS / PROMO
# ═══════════════════════════════════════════════════════════
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
        for lvl,pct in ((1,REF_L1),(2,REF_L2)):
            ref=referred_by_at_level(uid,lvl)
            if not ref: continue
            bonus=int(amount*pct/100)
            if bonus<=0: continue
            c.execute('UPDATE users SET rub_balance=rub_balance+? WHERE user_id=?',(bonus,ref))
            c.execute('INSERT INTO ref_earnings(referrer_id,referred_id,amount,source_topup_id,created_at) VALUES(?,?,?,?,?)',
                (ref,uid,bonus,tid,now)); c.commit()
            payouts.append((ref,lvl,bonus))
    return payouts
def exchange_rub_to_coins(uid,rub):
    rate=coin_rate()
    if rub<=0: return False,'bad_amount'
    if rub%rate!=0: return False,'not_multiple'
    coins=rub//rate
    if rub_balance(uid)<rub: return False,'not_enough_rub'
    c=db(); c.execute('UPDATE users SET rub_balance=rub_balance-?, balance=balance+? WHERE user_id=?',(rub,coins,uid)); c.commit()
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

# ═══════════════════════════════════════════════════════════
#  TICKETS
# ═══════════════════════════════════════════════════════════
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

# ═══════════════════════════════════════════════════════════
#  KEYBOARDS
# ═══════════════════════════════════════════════════════════
def t(uid,key,**kw):
    lang=get_lang(uid); s=TR.get(lang,TR['ru']).get(key) or TR['ru'].get(key) or key
    return s.format(**kw) if kw else s
def get_lang(uid):
    r=db().execute('SELECT lang FROM users WHERE user_id=?',(uid,)).fetchone()
    return r['lang'] if r and r['lang'] in LANGS else 'ru'
def set_lang(uid,lang):
    if lang not in LANGS: return
    c=db(); c.execute('UPDATE users SET lang=? WHERE user_id=?',(lang,uid)); c.commit()

def kb_menu(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(uid,'create_btn'),callback_data='create')],
        [InlineKeyboardButton(t(uid,'balance'),callback_data='balance'),
         InlineKeyboardButton(t(uid,'topup'),callback_data='topup')],
        [InlineKeyboardButton(t(uid,'history'),callback_data='history'),
         InlineKeyboardButton(t(uid,'promo'),callback_data='promo')],
        [InlineKeyboardButton(t(uid,'roulette'),callback_data='roulette'),
         InlineKeyboardButton(t(uid,'ref'),callback_data='ref')],
        [InlineKeyboardButton(t(uid,'support'),callback_data='support'),
         InlineKeyboardButton(t(uid,'help'),callback_data='help')],
        [InlineKeyboardButton(t(uid,'lang'),callback_data='lang')]])
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
def kb_queue_cancel(uid,jid):
    return InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,'queue_cancel'),callback_data=f'q:cancel:{jid}')]])
def kb_roulette(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(uid,'roulette_spin'),callback_data='roulette:spin')],
        [InlineKeyboardButton(t(uid,'back_menu'),callback_data='menu')]])
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
        [InlineKeyboardButton('⚙️ Настройки',callback_data='adm:settings')],
        [InlineKeyboardButton('🔄 Обновить',callback_data='adm:main')]])
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
        [InlineKeyboardButton(f'💰 Цена: {setting("image_cost","1")} 🪙',callback_data='adm:set:image_cost')],
        [InlineKeyboardButton(f'🎁 Старт: {setting("start_balance","1")} 🪙',callback_data='adm:set:start_balance')],
        [InlineKeyboardButton(f'👷 Параллельно: {setting("max_concurrent","1")}',callback_data='adm:set:max_concurrent')],
        [InlineKeyboardButton(f'⏱ Таймаут: {tmo_str}',callback_data='adm:set:timeout')],
        [InlineKeyboardButton(f'📊 Курс: 1 🪙 = {coin_rate()} ₽',callback_data='adm:set:coin_rate')],
        [InlineKeyboardButton(f'💸 Реф: {ref_percent()}%',callback_data='adm:set:ref_percent')],
        [InlineKeyboardButton(f'⏳ Rate-limit: {rate_limit_count()}/{rate_limit_window()}с',callback_data='adm:ratelimit')],
        [InlineKeyboardButton('◀️ Назад',callback_data='adm:main')]])
def kb_admin_ratelimit():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f'🔢 Кол-во: {rate_limit_count()}',callback_data='adm:set:rate_limit_count')],
        [InlineKeyboardButton(f'⏱ Окно: {rate_limit_window()} сек',callback_data='adm:set:rate_limit_window')],
        [InlineKeyboardButton('◀️ Назад',callback_data='adm:settings')]])
def kb_user_card(uid):
    u=get_user(uid); banned=bool(u['banned'])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('💰 Установить монеты',callback_data=f'adm:setbal:{uid}')],
        [InlineKeyboardButton('🪙 Добавить монеты',callback_data=f'adm:addbal:{uid}')],
        [InlineKeyboardButton('💵 Начислить рубли',callback_data=f'adm:addrub:{uid}')],
        [InlineKeyboardButton('🚫 Разбанить' if banned else '⛔ Забанить',callback_data=f'adm:userban:{uid}')],
        [InlineKeyboardButton('📜 История',callback_data=f'adm:hist:{uid}')],
        [InlineKeyboardButton('◀️ Назад',callback_data='adm:main')]])
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

# ═══════════════════════════════════════════════════════════
#  TEXTS
# ═══════════════════════════════════════════════════════════
def main_text(uid):
    return (f'{t(uid,"menu_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n'
        f'💵 {t(uid,"rubles")}: <b>{rub_balance(uid)} ₽</b>\n'
        f'🪙 {t(uid,"coins")}: <b>{balance(uid)}</b>\n\n'
        f'📊 {t(uid,"rate")}: <b>1 🪙 = {coin_rate()} ₽</b>\n'
        f'🎨 {t(uid,"gen_cost")}: <b>{setting("image_cost","1")}</b> 🪙\n\n'
        f'{t(uid,"choose_action")}')
TERMS_TPL=('{title}\n\n{lead}\n\n🔒 <a href="{privacy}">{privacy_t}</a>\n📜 <a href="{offer}">{offer_t}</a>\n\n{note}')
ADMIN_HELP=('🛠 <b>Админ-команды</b>\n━━━━━━━━━━━━━━━━━━━━\n\n'
    '👥 <code>/user ID</code> • <code>/setbalance</code> • <code>/addbalance</code> • <code>/setrub</code> • <code>/addrub</code>\n\n'
    '🚫 <code>/ban ID [прич]</code> • <code>/unban ID</code>\n\n'
    '⚙️ <code>/setcost N</code> • <code>/setrate N</code> • <code>/setref N</code> • <code>/settimeout N</code>\n\n'
    '🖼 <code>/setbanner KEY</code> • <code>/banners</code> • <code>/delbanner KEY</code>\n\n'
    '📡 <code>/apis</code>\n\n'
    '👑 <code>/setadmin ID</code> • <code>/unadmin ID</code> • <code>/admins</code>\n\n'
    '📢 <code>/broadcast ТЕКСТ</code> • <code>/ticket ID</code> • <code>/stats</code> • <code>/admin</code>')

# ═══════════════════════════════════════════════════════════
#  HELPERS / LOGGING
# ═══════════════════════════════════════════════════════════
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
def fmt_seconds_human(sec):
    if sec<60: return f'{sec} сек'
    m,s=divmod(sec,60)
    if m<60: return f'{m} мин'
    h,m=divmod(m,60); return f'{h} ч {m} мин'

# ═══════════════════════════════════════════════════════════
#  API CALLS
# ═══════════════════════════════════════════════════════════
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
    return False,'check_failed'
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
async def send_image(app,chat_id,data):
    items=data.get('data') or []
    if not items: raise RuntimeError('No image')
    item=items[0]; msg=None
    if item.get('b64_json'):
        raw=base64.b64decode(item['b64_json'])
        msg=await app.bot.send_photo(chat_id,raw,filename='imagesgpt.png')
    elif item.get('url'):
        async with httpx.AsyncClient(timeout=60) as c:
            r=await c.get(item['url']); r.raise_for_status(); raw=r.content
        msg=await app.bot.send_photo(chat_id,raw,filename='imagesgpt.png')
    else: raise RuntimeError('No b64/url')
    if msg and msg.photo: return msg.photo[-1].file_id
    return None

# ═══════════════════════════════════════════════════════════
#  QUEUE
# ═══════════════════════════════════════════════════════════
pending_jobs=[]; job_lock=asyncio.Lock(); workers=[]
async def queue_position_updater(app):
    while True:
        try:
            await asyncio.sleep(5)
            async with job_lock:
                snap=[(i,j) for i,j in enumerate(pending_jobs) if not j.get('cancelled')]
            for pos0,j in snap:
                pos=pos0+1
                if j.get('last_pos')==pos or not j.get('msg_id'): continue
                j['last_pos']=pos; uid=j['uid']
                try:
                    await app.bot.edit_message_text(chat_id=j['chat'],message_id=j['msg_id'],
                        text=(f'{t(uid,"queue_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n📐 {j["size"]}\n'
                              f'📝 {html.escape(j["prompt"][:120])}\n\n{t(uid,"queue_pos")}: <b>{pos}</b>'),
                        parse_mode=ParseMode.HTML,reply_markup=kb_queue_cancel(uid,j['job_id']))
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
        uid=job['uid']; chat=job['chat']; timeout_sec=get_timeout(); t0=time.time()
        try:
            await app.bot.send_chat_action(chat,ChatAction.UPLOAD_PHOTO)
            try:
                await app.bot.edit_message_text(chat_id=chat,message_id=job['msg_id'],
                    text=t(uid,'in_progress',limit=fmt_timeout()),parse_mode=ParseMode.HTML)
            except: pass
            await alog(app,f'🎨 <b>Генерация</b>\n👤 <code>{uid}</code>\n📐 <code>{html.escape(job["size"])}</code>\n📝 {html.escape(job["prompt"][:600])}',level=2)
            tt=asyncio.create_task(_keep_typing(app,chat,timeout_sec))
            try: data=await asyncio.wait_for(generate(job['prompt'],job['size'],timeout_sec),timeout_sec)
            finally:
                tt.cancel()
                try: await tt
                except: pass
            el=time.time()-t0; els=fmt_duration(el)
            fid=await send_image(app,chat,data)
            add_history(uid,job['prompt'],job['size'],'success',fid,elapsed=el)
            await app.bot.send_message(chat,
                f'{t(uid,"done_title")}\n━━━━━━━━━━━━━━━━━━━━\n{t(uid,"time_label")}: <b>{els}</b>\n'
                f'{t(uid,"left_coins")}: <b>{balance(uid)}</b> 🪙',
                parse_mode=ParseMode.HTML,reply_markup=kb_menu(uid))
            await alog(app,f'✅ <b>Готово</b> • 👤 <code>{uid}</code> • ⏱ <code>{els}</code> • 🪙 <code>{balance(uid)}</code>',level=2)
        except asyncio.TimeoutError:
            el=time.time()-t0
            change_balance(uid,int(setting('image_cost','1')))
            add_history(uid,job['prompt'],job['size'],'timeout',elapsed=el)
            await app.bot.send_message(chat,t(uid,'timeout',limit=fmt_timeout()),reply_markup=kb_menu(uid))
            await alog(app,f'⏱ Timeout • 👤 <code>{uid}</code> • {fmt_duration(el)}',level=1)
        except Exception as e:
            el=time.time()-t0
            change_balance(uid,int(setting('image_cost','1')))
            add_history(uid,job['prompt'],job['size'],'error',elapsed=el)
            await app.bot.send_message(chat,f'{t(uid,"error_gen")}\n\n<code>{html.escape(str(e)[:400])}</code>',
                parse_mode=ParseMode.HTML,reply_markup=kb_menu(uid))
            await alog(app,f'❌ <b>Ошибка</b> • 👤 <code>{uid}</code> • {fmt_duration(el)}\n<code>{html.escape(str(e)[:800])}</code>',level=1)
async def _keep_typing(app,chat,max_sec):
    el=0
    try:
        while el<max_sec:
            try: await app.bot.send_chat_action(chat,ChatAction.UPLOAD_PHOTO)
            except: pass
            await asyncio.sleep(4); el+=4
    except asyncio.CancelledError: return

# ═══════════════════════════════════════════════════════════
#  PAYMENTS
# ═══════════════════════════════════════════════════════════
async def pre_checkout(update,context):
    q=update.pre_checkout_query
    try:
        parts=q.invoice_payload.split(':')
        if len(parts)>=3 and parts[0]=='stars':
            uid=int(parts[1])
            if uid!=q.from_user.id:
                await q.answer(ok=False,error_message='Неверный получатель'); return
    except:
        await q.answer(ok=False,error_message='Ошибка данных'); return
    await q.answer(ok=True)

async def on_successful_payment(update,context):
    u=update.effective_user; ensure_user(u)
    sp=update.message.successful_payment
    cid=sp.telegram_payment_charge_id
    if stars_payment_exists(cid): return
    stars=sp.total_amount
    rub=int(stars*STAR_RATE)
    add_stars_payment(u.id,stars,rub,cid)
    bonus_coins=0
    try:
        parts=sp.invoice_payload.split(':')
        if len(parts)>=4:
            idx=int(parts[3])
            if 0<=idx<len(STAR_PACKS): bonus_coins=STAR_PACKS[idx][1]
    except: pass
    if bonus_coins: change_balance(u.id,bonus_coins)
    payouts=topup_rub(u.id,rub,method='stars')
    msg=(f'⭐ <b>Оплата получена</b>\n━━━━━━━━━━━━━━━━━━━━\n\n'
         f'⭐ Звёзд: <b>{stars}</b>\n💵 Зачислено: <b>{rub} ₽</b>\n')
    if bonus_coins: msg+=f'🎁 Бонус: <b>+{bonus_coins} 🪙</b>\n'
    msg+=f'💵 Баланс: <b>{rub_balance(u.id)} ₽</b>'
    await update.message.reply_text(msg,parse_mode=ParseMode.HTML,reply_markup=kb_menu(u.id))
    for ref,lvl,bonus in payouts:
        try:
            await context.bot.send_message(ref,f'💸 <b>Реферальный бонус L{lvl}</b>\n\n+<b>{bonus} ₽</b>',parse_mode=ParseMode.HTML)
        except: pass
    await alog(context.application,f'⭐ <b>Stars</b>\n👤 <code>{u.id}</code> • ⭐ {stars} • 💵 {rub} ₽',level=2)

# ═══════════════════════════════════════════════════════════
#  USER HANDLERS
# ═══════════════════════════════════════════════════════════
async def cmd_start(update,context):
    u=update.effective_user; ensure_user(u)
    if context.args:
        arg=context.args[0]
        if arg.startswith('ref_'):
            try: set_referrer(u.id,int(arg[4:]))
            except ValueError: pass
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
    text=f'{t(uid,"help_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n'+t(uid,'help_text',percent=ref_percent())
    await send_screen(update,uid,'help',text,kb_menu(uid))

async def on_callbacks(update,context):
    q=update.callback_query; await q.answer()
    u=q.from_user; ensure_user(u); uid=u.id; d=q.data

    if d.startswith('buy:'):
        try: idx=int(d.split(':',1)[1])
        except: return
        if idx<0 or idx>=len(STAR_PACKS):
            await q.answer('Пакет не найден',show_alert=True); return
        stars,bonus=STAR_PACKS[idx]; rub=int(stars*STAR_RATE)
        title=f'{stars} ⭐'; desc=f'Пополнение {rub} ₽'
        if bonus: desc+=f' + {bonus} 🪙'
        try:
            await context.bot.send_invoice(chat_id=q.message.chat_id,title=title,description=desc,
                payload=f'stars:{uid}:{stars}:{idx}',provider_token='',currency='XTR',
                prices=[LabeledPrice(label=title,amount=stars)])
        except Exception as e:
            await q.message.reply_text(f'❌ Ошибка счёта: {e}')
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
        text=f'{t(uid,"help_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n'+t(uid,'help_text',percent=ref_percent())
        await show_screen(q,context,uid,'help',text,kb_menu(uid)); return

    if d=='roulette':
        can,remain=roulette_can_spin(uid)
        if not can:
            txt=(f'{t(uid,"roulette_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n'
                 f'{t(uid,"roulette_cooldown",time=fmt_seconds_human(remain))}')
            await show_screen(q,context,uid,None,txt,
                InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,'back_menu'),callback_data='menu')]])); return
        txt=(f'{t(uid,"roulette_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n{t(uid,"roulette_rules")}\n\n'
             f'🪙 {t(uid,"coins")}: <b>{balance(uid)}</b>')
        await show_screen(q,context,uid,None,txt,kb_roulette(uid)); return
    if d=='roulette:spin':
        can,remain=roulette_can_spin(uid)
        if not can:
            await q.answer(t(uid,'roulette_cooldown',time=fmt_seconds_human(remain)),show_alert=True); return
        await q.edit_message_text(t(uid,'roulette_spinning'),parse_mode=ParseMode.HTML)
        await asyncio.sleep(1.2)
        prize=roulette_spin(uid)
        if prize>0:
            txt=(f'{t(uid,"roulette_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n{t(uid,"roulette_won",n=prize)}\n\n'
                 f'🪙 {t(uid,"coins")}: <b>{balance(uid)}</b>\n\n{t(uid,"roulette_done")}')
        else:
            txt=(f'{t(uid,"roulette_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n{t(uid,"roulette_empty")}\n\n{t(uid,"roulette_done")}')
        await show_screen(q,context,uid,None,txt,kb_menu(uid)); return

    if d=='lang':
        text=(f'{t(uid,"lang_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n'
              f'{t(uid,"lang_current")}: <b>{LANGS_NAMES.get(get_lang(uid),"")}</b>')
        await show_screen(q,context,uid,'lang',text,kb_lang(uid)); return
    if d.startswith('lang:set:'):
        new_lang=d.split(':',2)[2]; set_lang(uid,new_lang)
        await show_screen(q,context,uid,'menu',
            f'{t(uid,"lang_switched",lang=LANGS_NAMES.get(new_lang,new_lang))}\n\n'+main_text(uid),kb_menu(uid)); return

    if d=='balance':
        text=(f'{t(uid,"your_balance")}\n\n💵 {t(uid,"rubles")}: <b>{rub_balance(uid)} ₽</b>\n'
              f'🪙 {t(uid,"coins")}: <b>{balance(uid)}</b>\n\n'
              f'📊 {t(uid,"rate")}: <b>1 🪙 = {coin_rate()} ₽</b>')
        await show_screen(q,context,uid,'balance',text,kb_balance(uid)); return

    if d=='topup':
        text=(f'{t(uid,"topup_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n'
              f'⭐ 1 ⭐ = {STAR_RATE} ₽\n💵 {t(uid,"rubles")}: <b>{rub_balance(uid)} ₽</b>\n\nВыбери пакет:')
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
            await show_screen(q,context,uid,'exchange',text,
                InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,'back'),callback_data='balance')]])); return
        context.user_data['waiting']='exchange_rub'
        text=(f'{t(uid,"exchange_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n📊 {t(uid,"rate")}: <b>1 🪙 = {rate} ₽</b>\n'
              f'💵 {t(uid,"you_have")}: <b>{rb} ₽</b>\n\n{t(uid,"exchange_ask")}\n'
              f'<i>{t(uid,"exchange_must_be_multiple",rate=rate)}</i>')
        await show_screen(q,context,uid,'exchange',text,
            InlineKeyboardMarkup([[InlineKeyboardButton(t(uid,'cancel'),callback_data='cancel')]])); return

    if d=='history' or d.startswith('hist:p:'):
        page=0
        if d.startswith('hist:p:'):
            try: page=int(d.split(':',2)[2])
            except: page=0
        total=user_history_total(uid)
        if total==0:
            await show_screen(q,context,uid,'history',t(uid,'history_empty'),kb_menu(uid)); return
        ps=HISTORY_PAGE_SIZE
        tp=max(1,(total+ps-1)//ps); page=max(0,min(page,tp-1))
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
        else:
            await context.bot.send_message(q.message.chat_id,caption,parse_mode=ParseMode.HTML)
        return

    if d=='ref':
        total,earned=ref_stats(uid); percent=ref_percent()
        text=(f'{t(uid,"ref_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n'
              f'{t(uid,"ref_your_link")}\n<code>{ref_link(uid)}</code>\n\n'
              f'{t(uid,"ref_you_get",percent=percent)}\nL1 {REF_L1}% • L2 {REF_L2}%\n'
              f'{t(uid,"ref_earn_rub")}\n\n{t(uid,"ref_invited")}: <b>{total}</b>\n'
              f'{t(uid,"ref_earned")}: <b>{earned} ₽</b>\n\n{t(uid,"ref_note")}')
        kb=InlineKeyboardMarkup([
            [InlineKeyboardButton(t(uid,'ref_share'),url=f'https://t.me/share/url?url={ref_link(uid)}&text=ImagesGPT')],
            [InlineKeyboardButton(t(uid,'back_menu'),callback_data='menu')]])
        await show_screen(q,context,uid,'ref',text,kb); return

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
        try:
            await context.bot.send_message(t_['user_id'],t(t_['user_id'],'ticket_closed',tid=tid),
                parse_mode=ParseMode.HTML,reply_markup=kb_menu(t_['user_id']))
        except: pass
        return

    if d.startswith('adm:'):
        if not is_admin(uid): return
        await handle_admin_cb(q,context,d); return

    if d.startswith('q:cancel:'):
        jid=d.split(':',2)[2]; refunded=False
        async with job_lock:
            for i,j in enumerate(pending_jobs):
                if j['job_id']==jid and j['uid']==uid: pending_jobs.pop(i); refunded=True; break
        if refunded:
            change_balance(uid,int(setting('image_cost','1')))
            await show_screen(q,context,uid,'menu',f'❌ {t(uid,"queue_cancel")}\n\n💰 {balance(uid)} 🪙',kb_menu(uid))
        else:
            await show_screen(q,context,uid,'menu','❌',kb_menu(uid))
        return

    if d=='create':
        ok,wait=check_rate(uid)
        if not ok:
            await show_screen(q,context,uid,'menu',t(uid,'rate_limit',sec=wait),kb_menu(uid)); return
        cost=int(setting('image_cost','1'))
        if balance(uid)<cost:
            text=f'{t(uid,"insufficient_coins")}\n\n{t(uid,"need_coins",need=cost,have=balance(uid))}'
            kb=InlineKeyboardMarkup([
                [InlineKeyboardButton(t(uid,'exchange_btn'),callback_data='exchange')],
                [InlineKeyboardButton(t(uid,'back_menu'),callback_data='menu')]])
            await show_screen(q,context,uid,'menu',text,kb); return
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
        tok=str(uuid.uuid4()); context.user_data['pending']={tok:(p,d.split(':',1)[1])}
        cost=int(setting('image_cost','1'))
        text=(f'{t(uid,"confirm_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n📝 {html.escape(p[:500])}\n\n'
              f'📐 {d.split(":",1)[1]}\n💰 {cost} 🪙\n\n')
        await show_screen(q,context,uid,None,text,kb_confirm(uid,tok)); return
    if d.startswith('ok:'):
        tok=d[3:]; item=context.user_data.get('pending',{}).pop(tok,None)
        if not item:
            await show_screen(q,context,uid,'menu','❌',kb_menu(uid)); return
        cost=int(setting('image_cost','1'))
        if balance(uid)<cost:
            await show_screen(q,context,uid,'menu',t(uid,'insufficient_coins'),kb_menu(uid)); return
        change_balance(uid,-cost)
        p,size=item; jid=str(uuid.uuid4())
        async with job_lock:
            pos=len([j for j in pending_jobs if not j.get('cancelled')])+1
            pending_jobs.append({'job_id':jid,'uid':uid,'chat':q.message.chat_id,'prompt':p,'size':size,
                'msg_id':q.message.message_id,'last_pos':pos,'cancelled':False})
        text=(f'{t(uid,"queue_title")}\n━━━━━━━━━━━━━━━━━━━━\n\n📐 {size}\n📝 {html.escape(p[:120])}\n\n'
              f'{t(uid,"queue_pos")}: <b>{pos}</b>')
        await show_screen(q,context,uid,None,text,kb_queue_cancel(uid,jid)); return
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
        await update.message.reply_text(f'✅ Баннер <b>{BANNER_KEYS.get(key,key)}</b> сохранён в БД (перекрывает файл).',
            parse_mode=ParseMode.HTML,reply_markup=kb_banner_actions(key)); return

    if is_admin(uid) and context.user_data.get('admin_api_step'):
        step=context.user_data['admin_api_step']
        typ=context.user_data.get('admin_api_type','image')
        data=context.user_data.get('admin_api_data',{})
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
            await update.message.reply_text(f'✅ Ключ сохранён.\n\n🎨 Модель? (по умолчанию <code>{dm}</code>)\n<i>Отправь «-» для умолчания.</i>',parse_mode=ParseMode.HTML); return
        if step=='model':
            dm='gpt-image-2' if typ=='image' else 'deepseek-v4-flash'
            model=dm if text.strip()=='-' else text.strip()
            data['model']=model; context.user_data['admin_api_data']=data
            context.user_data['admin_api_step']='priority'
            await update.message.reply_text(f'✅ Модель: <code>{html.escape(model)}</code>\n\n🔢 Priority? (по умолчанию 100)\n<i>Отправь «-» для 100.</i>',parse_mode=ParseMode.HTML); return
        if step=='priority':
            pr=100
            if text.strip()!='-':
                try: pr=int(text)
                except ValueError: await update.message.reply_text('❌ Нужно число или «-».'); return
            aid=api_add(typ,data['name'],data['url'],data['key'],data['model'],pr)
            context.user_data.pop('admin_api_step',None); context.user_data.pop('admin_api_data',None); context.user_data.pop('admin_api_type',None)
            await update.message.reply_text(
                f'✅ API <b>#{aid}</b> добавлен ({typ})\n\n📛 {html.escape(data["name"])}\n🌐 <code>{html.escape(data["url"])}</code>\n'
                f'🎨 {html.escape(data["model"])}\n🔢 priority: {pr}',
                parse_mode=ParseMode.HTML,reply_markup=kb_api_list(typ)); return

    if is_admin(uid) and context.user_data.get('admin_reply_ticket'):
        tid=context.user_data.pop('admin_reply_ticket')
        if not text and not photo: await update.message.reply_text('❌'); return
        t_=get_ticket(tid)
        if not t_ or t_['status']!='open': await update.message.reply_text('❌'); return
        add_ticket_msg(tid,'admin',text or None,photo)
        try:
            owner=t_['user_id']; reply=t(owner,'support_reply',tid=tid)
            if photo:
                await context.bot.send_photo(owner,photo,caption=f'{reply}\n\n{html.escape(text or "")}\n\n<i>{t(owner,"reply_here")}</i>',parse_mode=ParseMode.HTML)
            else:
                await context.bot.send_message(owner,f'{reply}\n\n{html.escape(text)}\n\n<i>{t(owner,"reply_here")}</i>',parse_mode=ParseMode.HTML)
            await update.message.reply_text('✅')
        except Exception as e: await update.message.reply_text(f'❌ {e}')
        return

    if is_admin(uid) and context.user_data.get('admin_input'):
        key=context.user_data.pop('admin_input')
        try: iv=int(text)
        except ValueError: await update.message.reply_text('❌'); return
        if key=='timeout' and iv<30: await update.message.reply_text('❌ min 30'); return
        if key in ('coin_rate','rate_limit_count','rate_limit_window') and iv<1: await update.message.reply_text('❌ min 1'); return
        if key=='ref_percent' and (iv<0 or iv>100): await update.message.reply_text('❌ 0-100'); return
        set_setting(key,iv)
        await update.message.reply_text(f'✅ <b>{key}</b> = <code>{iv}</code>',parse_mode=ParseMode.HTML); return

    if is_admin(uid) and context.user_data.get('admin_api_prio_id'):
        aid=context.user_data.pop('admin_api_prio_id')
        try: pr=int(text)
        except ValueError: await update.message.reply_text('❌'); return
        api_set_priority(aid,pr); r=api_get(aid)
        if r:
            await update.message.reply_text(f'✅ API #{aid}: priority={pr}',parse_mode=ParseMode.HTML,
                reply_markup=kb_api_detail(aid))
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
            try: await context.bot.send_message(ref,f'💸 L{lvl} +<b>{bonus} ₽</b>',parse_mode=ParseMode.HTML)
            except: pass
        await update.message.reply_text(msg,parse_mode=ParseMode.HTML)
        try:
            await context.bot.send_message(target,f'💵 <b>+{amount} ₽</b>\n💵 {rub_balance(target)} ₽',
                parse_mode=ParseMode.HTML,reply_markup=kb_menu(target))
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
        try:
            await context.bot.send_message(target,f'{t(target,"banned_title")}\n\n{t(target,"banned_reason")}: {html.escape(reason)}',parse_mode=ParseMode.HTML)
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
            await update.message.reply_text(f'✅ <b>{uses}</b>\n\n⏰ Дней?\n<i>0 или «нет» — без срока.</i>',parse_mode=ParseMode.HTML); return
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
            await update.message.reply_text(f'✅ <code>{data["code"]}</code>\n🪙 {data["amount"]} • 🔢 {data["uses"]}{exp}',
                parse_mode=ParseMode.HTML,reply_markup=kb_promos_main()); return

    waiting=context.user_data.get('waiting')

    if waiting=='exchange_rub':
        context.user_data.pop('waiting',None)
        try: rub=int(text)
        except ValueError: await update.message.reply_text('❌',reply_markup=kb_menu(uid)); return
        ok,res=exchange_rub_to_coins(uid,rub)
        if not ok:
            msg={'bad_amount':'❌','not_multiple':t(uid,'exchange_must_be_multiple',rate=coin_rate()),
                 'not_enough_rub':t(uid,'not_enough_rub')}.get(res,'❌')
            await update.message.reply_text(msg,reply_markup=kb_menu(uid)); return
        tr=(f'{t(uid,"exchange_done")}\n━━━━━━━━━━━━━━━━━━━━\n\n'
            f'💵 {t(uid,"exchange_spent")}: <b>{rub} ₽</b>\n🪙 {t(uid,"exchange_got")}: <b>+{res} 🪙</b>\n\n'
            f'💵 {t(uid,"rubles")}: <b>{rub_balance(uid)} ₽</b>\n🪙 {t(uid,"coins")}: <b>{balance(uid)}</b>')
        await update.message.reply_text(tr,parse_mode=ParseMode.HTML,reply_markup=kb_menu(uid)); return

    if waiting=='promo':
        context.user_data.pop('waiting',None)
        code=text.upper()
        if not code: await update.message.reply_text('❌'); return
        ok,res=activate_promo(code,uid)
        if not ok: await update.message.reply_text('❌',reply_markup=kb_menu(uid)); return
        await update.message.reply_text(f'{t(uid,"promo_ok")}\n\n{t(uid,"promo_credited",n=res)}\n🪙 {t(uid,"coins")}: <b>{balance(uid)}</b>',
            parse_mode=ParseMode.HTML,reply_markup=kb_menu(uid)); return

    if waiting=='ticket':
        context.user_data.pop('waiting',None)
        if not text and not photo: await update.message.reply_text('❌'); return
        tid=create_ticket(uid,text or None,photo)
        await update.message.reply_text(t(uid,'support_created',tid=tid),parse_mode=ParseMode.HTML,reply_markup=kb_menu(uid))
        try:
            preview=text or '📷'
            await context.bot.send_message(ADMIN_ID,f'🆘 <b>Новый тикет #{tid}</b>\n👤 <code>{uid}</code>\n\n📝 {html.escape(preview[:1500])}',
                parse_mode=ParseMode.HTML,reply_markup=kb_ticket_admin(tid))
            if photo: await context.bot.send_photo(ADMIN_ID,photo,caption=f'📷 #{tid}')
        except: pass
        return

    if waiting=='image':
        if not text: await update.message.reply_text('❌'); return
        if len(text)>4000: await update.message.reply_text('❌'); return
        cost=int(setting('image_cost','1'))
        if balance(uid)<cost: await update.message.reply_text(t(uid,'insufficient_coins'),reply_markup=kb_menu(uid)); return
        context.user_data['waiting']=None
        m=await update.message.reply_text(t(uid,'checking'))
        try: ok,reason=await moderate(text)
        except Exception as e:
            await m.edit_text('❌'); await alog(context.application,f'⚠️ Moderation error\n<code>{html.escape(str(e)[:800])}</code>',level=1); return
        if not ok: await m.edit_text(f'{t(uid,"blocked")}\n\n{html.escape(reason)}',parse_mode=ParseMode.HTML,reply_markup=kb_menu(uid)); return
        context.user_data['prompt']=text
        await m.edit_text(t(uid,'choose_size'),parse_mode=ParseMode.HTML,reply_markup=kb_sizes(uid)); return

    tid=get_open_ticket(uid)
    if tid:
        if not text and not photo: return
        add_ticket_msg(tid,'user',text or None,photo)
        await update.message.reply_text(t(uid,'ticket_msg_added',tid=tid),reply_markup=kb_menu(uid))
        try:
            preview=text or '📷'
            await context.bot.send_message(ADMIN_ID,f'💬 <b>#{tid}</b> от <code>{uid}</code>:\n\n{html.escape(preview[:1500])}',
                parse_mode=ParseMode.HTML,reply_markup=kb_ticket_admin(tid))
            if photo: await context.bot.send_photo(ADMIN_ID,photo,caption=f'📷 #{tid}')
        except: pass
        return

    await update.message.reply_text(t(uid,'menu_hint'),reply_markup=kb_menu(uid))

# ═══════════════════════════════════════════════════════════
#  ADMIN PANEL
# ═══════════════════════════════════════════════════════════
async def show_user_card(message,uid):
    u=get_user(uid)
    if not u: await message.reply_text('❌'); return
    total,earned=ref_stats(uid); is_adm='👑 да' if is_admin(uid) else 'нет'
    txt=(f'👤 <b>Пользователь</b>\n━━━━━━━━━━━━━━━━━━━━\n'
        f'🆔 <code>{u["user_id"]}</code>\n📛 {html.escape(u["full_name"] or "—")}\n'
        f'🔗 @{u["username"] or "—"}\n🌐 {u["lang"] or "ru"}\n'
        f'💵 Рубли: <b>{u["rub_balance"]} ₽</b>\n🪙 Монеты: <b>{u["balance"]}</b>\n'
        f'👑 Админ: {is_adm}\n📅 Регистрация: {u["created_at"]}\n👀 Последний визит: {u["last_seen"]}\n'
        f'👥 Пригласил: {total} • заработал: {earned} ₽\n'
        f'🚫 Бан: {"да — " + html.escape(u["ban_reason"] or "") if u["banned"] else "нет"}')
    await message.reply_text(txt,parse_mode=ParseMode.HTML,reply_markup=kb_user_card(uid))

async def handle_admin_cb(q,context,d):
    if d=='adm:main':
        await q.edit_message_text(admin_panel_text(),parse_mode=ParseMode.HTML,reply_markup=kb_admin()); return
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
        avg,mn,mx,cnt=gen_time_stats()
        tline=''
        if cnt:
            tline=(f'\n⏱ Время генерации:\n   • среднее: <b>{fmt_duration(avg)}</b>\n'
                   f'   • мин: {fmt_duration(mn)} • макс: {fmt_duration(mx)}\n   • замеров: {cnt}\n')
        txt=('📊 <b>Статистика</b>\n━━━━━━━━━━━━━━━━━━━━\n\n'
            f'👥 Пользователей: <b>{users}</b>\n👑 Админов: <b>{admins_count}</b>\n'
            f'🚫 Забанено: <b>{banned}</b>\n🆘 Открытых тикетов: <b>{opent}</b>\n\n'
            f'💵 Пополнений: <b>{tsum} ₽</b>\n💸 Реф-выплат: <b>{rsum} ₽</b>\n\n'
            f'🎨 Генераций: <b>{gens}</b>\n✅ Успешно: <b>{ok}</b>\n❌ Ошибок: <b>{err}</b>\n'
            f'⏱ Таймаутов: <b>{touts}</b>\n{tline}')
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
        await q.edit_message_text(f'💵 Сумма ₽ <code>{uid}</code> (сейчас {rub_balance(uid)} ₽):\n<i>L1 {REF_L1}% • L2 {REF_L2}% реферерам.</i>',parse_mode=ParseMode.HTML); return
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

    if d=='adm:banners':
        await q.edit_message_text('🖼 <b>Баннеры экранов</b>\n━━━━━━━━━━━━━━━━━━━━\n\n✅ — загружен, ⬜ — нет.\n📁 — есть файл в репо, ✅ — загружен через бота.\n\n<i>Рекомендую 1280×640 или 1024×512.</i>',
            parse_mode=ParseMode.HTML,reply_markup=kb_admin_banners()); return
    if d.startswith('adm:ban:view:'):
        key=d.split(':',3)[3]; name=BANNER_KEYS.get(key,key)
        await q.edit_message_text(f'🖼 <b>{name}</b>\n\nИсточник: {banner_source(key)}',
            parse_mode=ParseMode.HTML,reply_markup=kb_banner_actions(key)); return
    if d.startswith('adm:ban:upload:'):
        key=d.split(':',3)[3]; context.user_data['admin_banner_upload']=key
        await q.edit_message_text(f'📤 Пришли картинку для баннера <b>{BANNER_KEYS.get(key,key)}</b>.\n\nРекомендую 1280×640 или 1024×512.',parse_mode=ParseMode.HTML); return
    if d.startswith('adm:ban:del:'):
        key=d.split(':',3)[3]; delete_banner(key)
        await q.edit_message_text(f'❌ Баннер из БД удалён. {banner_source(key)}',
            parse_mode=ParseMode.HTML,reply_markup=kb_banner_actions(key)); return

    if d=='adm:api':
        await q.edit_message_text('📡 <b>API-источники</b>\n━━━━━━━━━━━━━━━━━━━━\n\nВыбери тип.',
            parse_mode=ParseMode.HTML,reply_markup=kb_admin_api()); return
    if d.startswith('adm:api:list:'):
        typ=d.split(':',3)[3]; rows=api_list(typ)
        title='🖼 API картинок' if typ=='image' else '🧠 API модераторов'
        if not rows:
            await q.edit_message_text(f'{title}\n\nПока пусто. Используется API из конфига.',
                parse_mode=ParseMode.HTML,reply_markup=kb_api_list(typ)); return
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
        txt=(f'📡 <b>API #{r["id"]}</b>\n━━━━━━━━━━━━━━━━━━━━\n\n'
             f'📛 {html.escape(r["name"] or "—")}\n🌐 <code>{html.escape(r["base_url"])}</code>\n'
             f'🔑 <code>{html.escape(r["api_key"][:20])}…</code>\n🎨 <code>{html.escape(r["model"])}</code>\n'
             f'🔢 priority: {r["priority"]}\n{"✅ активен" if r["active"] else "⚪ выключен"}')
        await q.edit_message_text(txt,parse_mode=ParseMode.HTML,reply_markup=kb_api_detail(r['id'])); return
    if d.startswith('adm:api:toggle:'):
        aid=int(d.split(':',3)[3]); api_toggle(aid); r=api_get(aid)
        if not r: await q.edit_message_text('❌'); return
        txt=(f'📡 <b>API #{r["id"]}</b>\n━━━━━━━━━━━━━━━━━━━━\n\n'
             f'📛 {html.escape(r["name"] or "—")}\n🌐 <code>{html.escape(r["base_url"])}</code>\n'
             f'🎨 <code>{html.escape(r["model"])}</code>\n🔢 priority: {r["priority"]}\n{"✅ активен" if r["active"] else "⚪ выключен"}')
        await q.edit_message_text(txt,parse_mode=ParseMode.HTML,reply_markup=kb_api_detail(aid)); return
    if d.startswith('adm:api:del:'):
        aid=int(d.split(':',3)[3]); r=api_get(aid); typ=r['type'] if r else 'image'
        api_del(aid)
        await q.edit_message_text('🗑 Удалено.',parse_mode=ParseMode.HTML,reply_markup=kb_api_list(typ)); return
    if d.startswith('adm:api:prio:'):
        aid=int(d.split(':',3)[3])
        context.user_data['admin_api_prio_id']=aid
        await q.edit_message_text(f'🔢 Отправь новый priority для API #{aid} (число).\n<i>Меньше — выше приоритет.</i>',parse_mode=ParseMode.HTML); return
    if d.startswith('adm:api:add:'):
        typ=d.split(':',3)[3]
        context.user_data['admin_api_type']=typ
        context.user_data['admin_api_data']={}
        context.user_data['admin_api_step']='name'
        await q.edit_message_text(f'📡 Добавление API ({typ})\n\n<b>Шаг 1/5.</b> Имя (для админа):',parse_mode=ParseMode.HTML); return

    if d=='adm:promos':
        context.user_data.pop('promo_step',None); context.user_data.pop('promo_data',None)
        await q.edit_message_text('🎁 <b>Промокоды</b>\n━━━━━━━━━━━━━━━━━━━━\n\nВыбери действие:',
            parse_mode=ParseMode.HTML,reply_markup=kb_promos_main()); return
    if d=='adm:promo:new':
        context.user_data['promo_step']='code'; context.user_data['promo_data']={}
        await q.edit_message_text('🎁 <b>Создание промокода</b>\n\n<b>Шаг 1/4.</b> Введи код:',
            parse_mode=ParseMode.HTML,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('◀️ Отмена',callback_data='adm:promos')]])); return
    if d=='adm:promo:list':
        rows=list_promos()
        if not rows: await q.edit_message_text('📋 Нет промокодов.',reply_markup=kb_promos_main()); return
        await q.edit_message_text('📋 <b>Все промокоды</b>\n\nНажми на код, чтобы удалить:',parse_mode=ParseMode.HTML,reply_markup=kb_promo_list()); return
    if d.startswith('adm:promo:del:'):
        code=d.split(':',3)[3]; delete_promo(code)
        await q.edit_message_text(f'✅ <code>{code}</code> удалён.',parse_mode=ParseMode.HTML,reply_markup=kb_promos_main()); return
    if d=='adm:settings':
        await q.edit_message_text('⚙️ <b>Настройки</b>\n━━━━━━━━━━━━━━━━━━━━',parse_mode=ParseMode.HTML,reply_markup=kb_admin_settings()); return
    if d=='adm:ratelimit':
        await q.edit_message_text(f'⏳ <b>Rate-limit</b>\n━━━━━━━━━━━━━━━━━━━━\n\n{rate_limit_count()} генераций за {rate_limit_window()} сек.',
            parse_mode=ParseMode.HTML,reply_markup=kb_admin_ratelimit()); return
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

# ═══════════════════════════════════════════════════════════
#  ADMIN COMMANDS
# ═══════════════════════════════════════════════════════════
async def cmd_admin(update,context):
    if not is_admin(update.effective_user.id): return
    await update.message.reply_text(admin_panel_text(),parse_mode=ParseMode.HTML,reply_markup=kb_admin())
async def cmd_admin_help(update,context):
    if not is_admin(update.effective_user.id): return
    await update.message.reply_text(ADMIN_HELP,parse_mode=ParseMode.HTML)
async def cmd_stats(update,context):
    if not is_admin(update.effective_user.id): return
    c=db()
    users=c.execute('SELECT COUNT(*) AS n FROM users').fetchone()['n']
    gens=c.execute('SELECT COUNT(*) AS n FROM history').fetchone()['n']
    opent=c.execute('SELECT COUNT(*) AS n FROM tickets WHERE status="open"').fetchone()['n']
    tsum=c.execute('SELECT COALESCE(SUM(amount),0) AS s FROM topups').fetchone()['s']
    admins_count=c.execute('SELECT COUNT(*) AS n FROM admins').fetchone()['n']+1
    avg,mn,mx,cnt=gen_time_stats()
    tline=f'\n⏱ Средн. генерация: {fmt_duration(avg)} ({cnt})' if cnt else ''
    await update.message.reply_text(
        f'📊 Пользователей: {users}\n👑 Админов: {admins_count}\n🎨 Генераций: {gens}\n'
        f'🆘 Открытых: {opent}\n💵 Пополнений: {tsum} ₽\n⏱ Таймаут: {get_timeout()} сек\n'
        f'📊 Курс: 1 🪙 = {coin_rate()} ₽\n💸 Реф: L1 {REF_L1}% • L2 {REF_L2}%'
        f'\n⏳ Rate: {rate_limit_count()}/{rate_limit_window()}с{tline}')
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
        try: await context.bot.send_message(ref,f'💸 L{lvl} +<b>{bonus} ₽</b>',parse_mode=ParseMode.HTML)
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
async def cmd_setcost(update,context):
    if not is_admin(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text(f'/setcost N (сейчас {setting("image_cost","1")})'); return
    try: v=int(context.args[0])
    except ValueError: await update.message.reply_text('❌'); return
    set_setting('image_cost',v)
    await update.message.reply_text(f'✅ {v} 🪙',parse_mode=ParseMode.HTML)
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
        await update.message.reply_text(f'🖼 <b>Баннеры</b>\n\nИспользование: <code>/setbanner KEY</code>\n\n<b>Ключи:</b>\n{keys_list}\n\n<i>Файлы по умолчанию: помести banners/KEY.png в репозиторий.</i>',parse_mode=ParseMode.HTML); return
    key=context.args[0].lower()
    if key not in BANNER_KEYS:
        await update.message.reply_text(f'❌ Ключ <code>{key}</code> не найден.',parse_mode=ParseMode.HTML); return
    context.user_data['admin_banner_upload']=key
    await update.message.reply_text(f'📤 Пришли картинку для баннера <b>{BANNER_KEYS[key]}</b>.\n<i>Сохраню в БД, перекрывая файл из репо.</i>',parse_mode=ParseMode.HTML)
async def cmd_banners(update,context):
    if not is_admin(update.effective_user.id): return
    lines=['🖼 <b>Баннеры экранов</b>','━━━━━━━━━━━━━━━━━━━━','']
    for k,n in BANNER_KEYS.items():
        src=banner_source(k)
        lines.append(f'<code>{k}</code> — {n}\n   {src}')
    lines.append(''); lines.append('<i>Управление: /admin → 🖼 Баннеры</i>')
    await update.message.reply_text('\n'.join(lines),parse_mode=ParseMode.HTML)
async def cmd_delbanner(update,context):
    if not is_admin(update.effective_user.id): return
    if not context.args: await update.message.reply_text('/delbanner KEY'); return
    key=context.args[0].lower()
    if key not in BANNER_KEYS: await update.message.reply_text('❌ Неизвестный ключ.'); return
    delete_banner(key)
    await update.message.reply_text(f'❌ Баннер <b>{BANNER_KEYS[key]}</b> удалён из БД. Источник: {banner_source(key)}',parse_mode=ParseMode.HTML)
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

# ═══════════════════════════════════════════════════════════
#  LIFECYCLE
# ═══════════════════════════════════════════════════════════
async def post_init(app):
    init_db()
    n=int(setting('max_concurrent','1'))
    for _ in range(n): workers.append(asyncio.create_task(worker(app)))
    workers.append(asyncio.create_task(queue_position_updater(app)))
    banners_have=list_banners()
    banners_files=sum(1 for k in BANNER_KEYS if banner_file(k))
    banners_db=sum(1 for k in BANNER_KEYS if db_has_banner(k))
    apis_img=len(api_list('image')); apis_mod=len(api_list('mod'))
    await alog(app,
        f'🟢 <b>ImagesGPT запущен</b>\n👷 Воркеров: <code>{n}</code>\n'
        f'🎨 <code>{IMAGE_MODEL}</code>\n⏱ Таймаут: <code>{fmt_timeout()}</code>\n'
        f'📊 Курс: <code>1 🪙 = {coin_rate()} ₽</code>\n💸 Реф: <code>L1 {REF_L1}% • L2 {REF_L2}%</code>\n'
        f'⏳ Rate-limit: <code>{rate_limit_count()}/{rate_limit_window()}с</code>\n'
        f'🖼 Баннеры: доступно <code>{len(banners_have)}/{len(BANNER_KEYS)}</code> (📁{banners_files} • ✅{banners_db})\n'
        f'📡 API: 🖼{apis_img} 🧠{apis_mod}',level=1)
async def post_shutdown(app):
    for w in workers: w.cancel()
    await asyncio.gather(*workers,return_exceptions=True)
    if _db is not None: _db.close()
async def on_error(update,context):
    log.error('Ошибка в хендлере: %s',context.error,exc_info=context.error)
    try:
        await context.application.bot.send_message(ADMIN_ID,
            f'⚠️ <b>Ошибка</b>\n<code>{html.escape(str(context.error)[:800])}</code>',parse_mode=ParseMode.HTML)
    except: pass

def build_app():
    app=(Application.builder().token(BOT_TOKEN).post_init(post_init).post_shutdown(post_shutdown).build())
    app.add_handler(CommandHandler('start',cmd_start))
    app.add_handler(CommandHandler('help',cmd_help))
    app.add_handler(CommandHandler('admin',cmd_admin))
    app.add_handler(CommandHandler('admin_help',cmd_admin_help))
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
    app.add_handler(CommandHandler('setcost',cmd_setcost))
    app.add_handler(CommandHandler('setrate',cmd_setrate))
    app.add_handler(CommandHandler('setref',cmd_setref))
    app.add_handler(CommandHandler('settimeout',cmd_settimeout))
    app.add_handler(CommandHandler('broadcast',cmd_broadcast))
    app.add_handler(CommandHandler('setbanner',cmd_setbanner))
    app.add_handler(CommandHandler('banners',cmd_banners))
    app.add_handler(CommandHandler('delbanner',cmd_delbanner))
    app.add_handler(CommandHandler('apis',cmd_apis))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT,on_successful_payment))
    app.add_handler(CallbackQueryHandler(on_callbacks))
    app.add_handler(MessageHandler((filters.TEXT & ~filters.COMMAND) | filters.PHOTO,on_message))
    app.add_error_handler(on_error)
    return app

def run_once():
    app=build_app()
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