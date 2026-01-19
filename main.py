from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes,
    filters, CallbackQueryHandler
)
from collections import deque
import json
from datetime import datetime

# ================= CONFIG =================
BOT_TOKEN = "7800203446:AAHJ0e0SRHGVTOLvMiWDPP3sS-GAxKN9Mow"
ADMIN_IDS = {6324902091}
CHANNEL_USERNAME = "peshqadam_maktabi"
CHANNEL_ID = -1001234567890
MAX_CONCURRENT_USERS = 4

# ================= STATES =================
NAME, SURNAME, AGE, REGION, COURSE, PHONE = range(6)
ADD_COURSE, REMOVE_COURSE, ADD_REGION, REMOVE_REGION, CONFIRM_REGION = range(6, 11)
SEARCH_USERS, FILTER_REGION, FILTER_COURSE, ADMIN_MAIN, EXPORT_CHOICE = range(11, 16)

# ================= DATA =================
users = {}
admin_context = {}
user_context = {}
temp_region = {}
active_users = set()
queue_users = deque()

REGIONS = [
    "Toshkent", "Samarqand",
    "Andijon", "Farg'ona", "Namangan"
]

COURSES = [
    "📚 Kitobxonlik",
    "🇬🇧 Ingliz tili",
    "🕌 Arab tili",
    "🎤 Notiqlik",
    "🌱 Baxt sari yo'l",
    "🔁 Yangi hayot sari 21 kun",
    "🎶 Vokal darslari",
    "🎨 Tasviriy san'at",
    "🧠 Oila psixologiyasi",
    "💪 Sog' fikr — sog'lom tana",
    "👗 Libos dizayni",
    "👨‍👩‍👧 Oila akademiyasi"
]

# ================= HELPER FUNCTIONS =================
def get_user_identifier(user):
    if user.username:
        return f"@{user.username}"
    else:
        return f"ID: {user.id}"

def get_region_keyboard():
    kb = []
    for region in REGIONS:
        kb.append([region])
    kb.append(["↩️ Orqaga"])
    return kb

def get_admin_keyboard():
    kb = [
        ["➕ Kurs qo'shish", "🗑 Kurs o'chirish"],
        ["➕ Viloyat qo'shish", "🗑 Viloyat o'chirish"],
        ["📊 Barcha foydalanuvchilar", "🔍 Foydalanuvchi qidirish"],
        ["📥 Eksport", "↩️ Orqaga"]
    ]
    return kb

def get_back_keyboard():
    return [["↩️ Orqaga"]]

def export_to_json():
    data = []
    for uid, user in users.items():
        data.append({
            "Ism": user['name'],
            "Familiya": user['surname'],
            "Yosh": user['age'],
            "Viloyat": user['region'],
            "Kurs": user['course'],
            "Telefon": user['phone'],
            "Identifier": user['identifier']
        })
    return json.dumps(data, ensure_ascii=False, indent=2)

def export_to_txt():
    text = "=" * 80 + "\n"
    text += f"FOYDALANUVCHILAR RO'YXATI - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    text += "=" * 80 + "\n\n"
    for idx, (uid, user) in enumerate(users.items(), 1):
        text += f"{idx}. ISM VA FAMILIYA: {user['name']} {user['surname']}\n"
        text += f"   TELEFON: {user['phone']}\n"
        text += f"   YOSH: {user['age']}\n"
        text += f"   VILOYAT: {user['region']}\n"
        text += f"   KURS: {user['course']}\n"
        text += f"   IDENTIFIER: {user['identifier']}\n"
        text += "-" * 80 + "\n\n"
    text += f"JAMI: {len(users)} ta foydalanuvchi\n"
    return text

def export_to_csv():
    text = "Ism,Familiya,Telefon,Yosh,Viloyat,Kurs,Identifier\n"
    for user in users.values():
        text += f'"{user["name"]}","{user["surname"]}","{user["phone"]}","{user["age"]}","{user["region"]}","{user["course"]}","{user["identifier"]}"\n'
    return text

async def check_user_limit(uid: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if len(active_users) < MAX_CONCURRENT_USERS:
        active_users.add(uid)
        return True
    queue_users.append(uid)
    return False

async def remove_active_user(uid: int, context: ContextTypes.DEFAULT_TYPE):
    if uid in active_users:
        active_users.discard(uid)
    if queue_users:
        next_uid = queue_users.popleft()
        active_users.add(next_uid)
        try:
            await context.bot.send_message(
                next_uid,
                "<b>✅ Endi siz ro'yxatdan o'tishingiz mumkin!</b>",
                parse_mode="HTML"
            )
        except:
            pass

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in ADMIN_IDS:
        kb = get_admin_keyboard()
        await update.message.reply_text(
            "<b>🔧 Admin Paneli</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return ADMIN_MAIN
    kb = [["📝 Ro'yxatdan o'tish"], ["↩️ Orqaga"]]
    await update.message.reply_text(
        "<b>👋 Assalomu alaykum!</b>\n\n"
        "Kurslarga ro'yxatdan o'tish uchun tugmani bosing\n\nRo'yxatdan o'tish tugmasin bosing.",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in ADMIN_IDS:
        await remove_active_user(user_id, context)
        kb = get_admin_keyboard()
        await update.message.reply_text(
            "<b>🔧 Admin Paneli</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return ADMIN_MAIN
    kb = [["📝 Ro'yxatdan o'tish"], ["↩️ Orqaga"]]
    await update.message.reply_text(
        "<b>👋 Bosh menyu</b>",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )
    return ConversationHandler.END

# ================= CHANNEL CHECK =================
async def check_channel_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except:
        pass
    return False

# ================= REGISTRATION =================
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    can_access = await check_user_limit(user_id, context)
    if not can_access:
        await update.message.reply_text(
            "<b>⏳ Hozir juda ko'p odamlar ro'yxatdan o'tmoqda!</b>\n\n"
            f"<b>Siz navbatda {len(queue_users)} o'rinni kutyapsiz.</b>\n"
            "Iltimos, biroz kutib turing...",
            parse_mode="HTML"
        )
        return ConversationHandler.END
    is_subscribed = await check_channel_subscription(update, context)
    if not is_subscribed:
        kb = [[InlineKeyboardButton(f"📢 {CHANNEL_USERNAME} ga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME}")]]
        await update.message.reply_text(
            "<b>⚠️ Avval kanalga obuna bo'ling!</b>\n\n"
            "Kursga ro'yxatdan o'tish uchun @peshqadam_maktabi kanalga obuna bo'lishingiz kerak.\n\n",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="HTML"
        )
        await remove_active_user(user_id, context)
        return ConversationHandler.END
    await update.message.reply_text(
        "<b>✍️ Ismingizni kiriting:</b>",
        reply_markup=ReplyKeyboardMarkup(get_back_keyboard(), resize_keyboard=True),
        parse_mode="HTML"
    )
    return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "↩️ Orqaga":
        await remove_active_user(update.effective_user.id, context)
        return await go_back(update, context)
    context.user_data["name"] = update.message.text
    await update.message.reply_text(
        "<b>✍️ Familiyangizni kiriting:</b>",
        reply_markup=ReplyKeyboardMarkup(get_back_keyboard(), resize_keyboard=True),
        parse_mode="HTML"
    )
    return SURNAME

async def surname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "↩️ Orqaga":
        await remove_active_user(update.effective_user.id, context)
        return await go_back(update, context)
    context.user_data["surname"] = update.message.text
    await update.message.reply_text(
        "<b>🎂 Yoshingizni kiriting:</b>",
        reply_markup=ReplyKeyboardMarkup(get_back_keyboard(), resize_keyboard=True),
        parse_mode="HTML"
    )
    return AGE

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "↩️ Orqaga":
        await remove_active_user(update.effective_user.id, context)
        return await go_back(update, context)
    context.user_data["age"] = update.message.text
    kb = get_region_keyboard()
    await update.message.reply_text(
        "<b>📍 Viloyatingizni tanlang:</b>",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )
    return REGION

async def region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "↩️ Orqaga":
        await remove_active_user(update.effective_user.id, context)
        return await go_back(update, context)
    context.user_data["region"] = update.message.text
    kb = [COURSES[i:i+2] for i in range(0, len(COURSES), 2)]
    kb.append(["↩️ Orqaga"])
    await update.message.reply_text(
        "<b>📚 Kursni tanlang:</b>",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )
    return COURSE

async def course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "↩️ Orqaga":
        await remove_active_user(update.effective_user.id, context)
        return await go_back(update, context)
    context.user_data["course"] = update.message.text
    kb = [[KeyboardButton("📞 Telefon raqamni yuborish", request_contact=True)], ["↩️ Orqaga"]]
    await update.message.reply_text(
        "<b>📲 Telefon raqamingizni yuboring:</b>",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "↩️ Orqaga":
        await remove_active_user(update.effective_user.id, context)
        return await go_back(update, context)
    uid = update.effective_user.id
    contact = update.message.contact
    identifier = get_user_identifier(update.effective_user)
    users[uid] = {
        "name": context.user_data["name"],
        "surname": context.user_data["surname"],
        "age": context.user_data["age"],
        "region": context.user_data["region"],
        "course": context.user_data["course"],
        "phone": contact.phone_number,
        "user_id": uid,
        "identifier": identifier
    }
    kb = [["👤 Shaxsiy ma'lumotlar"], ["↩️ Orqaga"]]
    await update.message.reply_text(
        "<b>✅ Ro'yxatdan muvaffaqiyatli o'tdingiz!</b>",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )
    for admin in ADMIN_IDS:
        await context.bot.send_message(
            admin,
            f"<b>🆕 Yangi foydalanuvchi ro'yxatdan o'tdi:</b>\n\n"
            f"<b>👤 Ism:</b> {users[uid]['name']}\n"
            f"<b>👤 Familiya:</b> {users[uid]['surname']}\n"
            f"<b>🎂 Yosh:</b> {users[uid]['age']}\n"
            f"<b>📍 Viloyat:</b> {users[uid]['region']}\n"
            f"<b>📚 Kurs:</b> {users[uid]['course']}\n"
            f"<b>🔗 Identifier:</b> {users[uid]['identifier']}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📩 Javob berish", callback_data=f"admin_{uid}")]
            ]),
            parse_mode="HTML"
        )
    await remove_active_user(uid, context)
    return ConversationHandler.END

# ================= USER MENU =================
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = users.get(update.effective_user.id)
    if not u:
        await update.message.reply_text("Avval ro'yxatdan o'ting!", parse_mode="HTML")
        return
    kb = [["↩️ Orqaga"]]
    await update.message.reply_text(
        f"<b>👤 Shaxsiy ma'lumotlar:</b>\n\n"
        f"<b>Ism:</b> {u['name']}\n"
        f"<b>Familiya:</b> {u['surname']}\n"
        f"<b>Yosh:</b> {u['age']}\n"
        f"<b>Viloyat:</b> {u['region']}\n"
        f"<b>Kurs:</b> {u['course']}\n"
        f"<b>Telefon:</b> {u['phone']}\n"
        f"<b>Identifier:</b> {u['identifier']}",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )

async def contact_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["↩️ Orqaga"]]
    await update.message.reply_text(
        "<b>✍️ Adminga xabar yozing:</b>",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )

async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in users or uid in ADMIN_IDS:
        return
    if update.message.text == "↩️ Orqaga":
        kb = [["👤 Shaxsiy ma'lumotlar"]]
        await update.message.reply_text(
            "<b>👋 Bosh menyu</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return
    for admin in ADMIN_IDS:
        user_context[uid] = admin
        user_info = users[uid]
        await context.bot.send_message(
            admin,
            f"<b>📩 Foydalanuvchi:</b> {user_info['name']} {user_info['surname']}\n"
            f"<b>📞 Telefon:</b> {user_info['phone']}\n"
            f"<b>🔗 Identifier:</b> {user_info['identifier']}\n\n"
            f"<b>💬 Xabar:</b>\n{update.message.text}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📩 Javob berish", callback_data=f"admin_{uid}")]
            ]),
            parse_mode="HTML"
        )

# ================= CALLBACK =================
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = int(query.data.split("_")[1])
    admin_context[query.from_user.id] = uid
    user_context[uid] = query.from_user.id
    kb = [["↩️ Orqaga"]]
    await query.message.reply_text(
        "<b>✍️ Javob yozing:</b>",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )

# ================= ADMIN MESSAGE =================
async def admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    aid = update.effective_user.id
    if update.message.text == "↩️ Orqaga":
        kb = get_admin_keyboard()
        await update.message.reply_text(
            "<b>🔧 Admin Paneli</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return ADMIN_MAIN
    if aid not in ADMIN_IDS or aid not in admin_context:
        return
    uid = admin_context[aid]
    await context.bot.send_message(
        uid,
        f"<b>📩 Admin:</b>\n\n{update.message.text}",
        parse_mode="HTML"
    )

# ================= EXPORT FUNCTIONS =================
async def export_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if not users:
        kb = get_admin_keyboard()
        await update.message.reply_text(
            "<b>❌ Hozircha foydalanuvchi yo'q!</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return ADMIN_MAIN
    kb = [["📄 TXT", "📊 CSV"], ["📋 JSON", "↩️ Orqaga"]]
    await update.message.reply_text(
        f"<b>📥 Eksport formati tanlang:</b>\n\n"
        f"<b>Jami foydalanuvchi:</b> {len(users)}",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )
    return EXPORT_CHOICE

async def export_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    admin_id = update.effective_user.id
    if choice == "↩️ Orqaga":
        kb = get_admin_keyboard()
        await update.message.reply_text(
            "<b>🔧 Admin Paneli</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return ADMIN_MAIN
    try:
        if choice == "📄 TXT":
            content = export_to_txt()
            filename = f"foydalanuvchilar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        elif choice == "📊 CSV":
            content = export_to_csv()
            filename = f"foydalanuvchilar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        elif choice == "📋 JSON":
            content = export_to_json()
            filename = f"foydalanuvchilar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            kb = get_admin_keyboard()
            await update.message.reply_text(
                "<b>❌ Noto'g'ri format!</b>",
                reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
                parse_mode="HTML"
            )
            return ADMIN_MAIN
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        with open(filename, 'rb') as f:
            await context.bot.send_document(
                chat_id=admin_id,
                document=f,
                filename=filename,
                caption=f"<b>✅ Eksport tayyor!</b>\n\n"
                        f"<b>Jami:</b> {len(users)} ta foydalanuvchi",
                parse_mode="HTML"
            )
        kb = get_admin_keyboard()
        await update.message.reply_text(
            "<b>✅ Fayl yuborildi!</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return ADMIN_MAIN
    except Exception as e:
        kb = get_admin_keyboard()
        await update.message.reply_text(
            f"<b>❌ Xato: {str(e)}</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return ADMIN_MAIN

# ================= SEARCH USERS =================
async def search_users_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    kb = [["Viloyat bo'yicha", "Kurs bo'yicha"], ["↩️ Orqaga"]]
    await update.message.reply_text(
        "<b>🔍 Qidiruv turi tanlang:</b>",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )
    return SEARCH_USERS

async def search_filter_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice == "↩️ Orqaga":
        kb = get_admin_keyboard()
        await update.message.reply_text(
            "<b>🔧 Admin Paneli</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return ADMIN_MAIN
    if choice == "Viloyat bo'yicha":
        kb = [[r, "↩️ Orqaga"] for r in REGIONS]
        await update.message.reply_text(
            "<b>📍 Viloyatni tanlang:</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return FILTER_REGION
    elif choice == "Kurs bo'yicha":
        kb = [COURSES[i:i+2] for i in range(0, len(COURSES), 2)]
        kb.append(["↩️ Orqaga"])
        await update.message.reply_text(
            "<b>📚 Kursni tanlang:</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return FILTER_COURSE

async def filter_by_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    region = update.message.text
    if region == "↩️ Orqaga":
        kb = [["Viloyat bo'yicha", "Kurs bo'yicha"], ["↩️ Orqaga"]]
        await update.message.reply_text(
            "<b>🔍 Qidiruv turi tanlang:</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return SEARCH_USERS
    filtered = [u for u in users.values() if u['region'] == region]
    if not filtered:
        kb = [["↩️ Orqaga"]]
        await update.message.reply_text(
            f"<b>❌ {region} viloyatida foydalanuvchi yo'q</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return FILTER_REGION
    text = f"<b>📋 {region} viloyatidagi foydalanuvchilar: {len(filtered)}</b>\n\n"
    for u in filtered:
        text += f"👤 <b>{u['name']} {u['surname']}</b>\n"
        text += f"📞 {u['phone']}\n"
        text += f"📚 {u['course']}\n"
        text += f"🔗 {u['identifier']}\n\n"
    kb = [["↩️ Orqaga"]]
    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )
    return FILTER_REGION

async def filter_by_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    course = update.message.text
    if course == "↩️ Orqaga":
        kb = [["Viloyat bo'yicha", "Kurs bo'yicha"], ["↩️ Orqaga"]]
        await update.message.reply_text(
            "<b>🔍 Qidiruv turi tanlang:</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return SEARCH_USERS
    filtered = [u for u in users.values() if u['course'] == course]
    if not filtered:
        kb = [["↩️ Orqaga"]]
        await update.message.reply_text(
            f"<b>❌ Bu kursga foydalanuvchi yo'q</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return FILTER_COURSE
    text = f"<b>📋 {course} kursidagi foydalanuvchilar: {len(filtered)}</b>\n\n"
    for u in filtered:
        text += f"👤 <b>{u['name']} {u['surname']}</b>\n"
        text += f"📞 {u['phone']}\n"
        text += f"📍 {u['region']}\n"
        text += f"🔗 {u['identifier']}\n\n"
    kb = [["↩️ Orqaga"]]
    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )
    return FILTER_COURSE

# ================= COURSE MANAGEMENT =================
async def add_course_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    kb = [["↩️ Orqaga"]]
    await update.message.reply_text(
        "<b>📚 Yangi kurs nomini kiriting:</b>",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )
    return ADD_COURSE

async def add_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "↩️ Orqaga":
        kb = get_admin_keyboard()
        await update.message.reply_text(
            "<b>🔧 Admin Paneli</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return ADMIN_MAIN
    course_name = update.message.text
    COURSES.append(course_name)
    kb = get_admin_keyboard()
    await update.message.reply_text(
        f"<b>✅ Kurs qo'shildi:</b> {course_name}",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )
    return ADMIN_MAIN

async def remove_course_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if not COURSES:
        kb = get_admin_keyboard()
        await update.message.reply_text(
            "<b>Kurslar ro'yxati bo'sh!</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return ADMIN_MAIN
    kb = [[c, "↩️ Orqaga"] for c in COURSES]
    await update.message.reply_text(
        "<b>🗑 O'chiriladigan kursni tanlang:</b>",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )
    return REMOVE_COURSE

async def remove_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "↩️ Orqaga":
        kb = get_admin_keyboard()
        await update.message.reply_text(
            "<b>🔧 Admin Paneli</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return ADMIN_MAIN
    course_name = update.message.text
    if course_name in COURSES:
        COURSES.remove(course_name)
        kb = get_admin_keyboard()
        await update.message.reply_text(
            f"<b>✅ Kurs o'chirildi:</b> {course_name}",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
    else:
        kb = get_admin_keyboard()
        await update.message.reply_text(
            "<b>❌ Kurs topilmadi!</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
    return ADMIN_MAIN

# ================= REGION MANAGEMENT =================
async def add_region_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    kb = [["↩️ Orqaga"]]
    await update.message.reply_text(
        "<b>📍 Yangi viloyat nomini kiriting:</b>",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )
    return ADD_REGION

async def add_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "↩️ Orqaga":
        kb = get_admin_keyboard()
        await update.message.reply_text(
            "<b>🔧 Admin Paneli</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return ADMIN_MAIN
    admin_id = update.effective_user.id
    region_name = update.message.text
    temp_region[admin_id] = region_name
    kb = [[
        InlineKeyboardButton("✅ Ha, qo'shish", callback_data=f"confirm_region_{admin_id}"),
        InlineKeyboardButton("❌ Yo'q, bekor qilish", callback_data=f"cancel_region_{admin_id}")
    ]]
    await update.message.reply_text(
        f"<b>📍 Viloyatni qo'shishni tasdiqlang:</b>\n\n<b>{region_name}</b>",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="HTML"
    )
    return CONFIRM_REGION

async def remove_region_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if not REGIONS:
        kb = get_admin_keyboard()
        await update.message.reply_text(
            "<b>Viloyatlar ro'yxati bo'sh!</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return ADMIN_MAIN
    kb = [[r, "↩️ Orqaga"] for r in REGIONS]
    await update.message.reply_text(
        "<b>🗑 O'chiriladigan viloyatni tanlang:</b>",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )
    return REMOVE_REGION

async def remove_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "↩️ Orqaga":
        kb = get_admin_keyboard()
        await update.message.reply_text(
            "<b>🔧 Admin Paneli</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return ADMIN_MAIN
    region_name = update.message.text
    if region_name in REGIONS:
        REGIONS.remove(region_name)
        kb = get_admin_keyboard()
        await update.message.reply_text(
            f"<b>✅ Viloyat o'chirildi:</b> {region_name}",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
    else:
        kb = get_admin_keyboard()
        await update.message.reply_text(
            "<b>❌ Viloyat topilmadi!</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
    return ADMIN_MAIN

# ================= CONFIRMATION CALLBACKS =================
async def confirm_region_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    admin_id = int(query.data.split("_")[2])
    if admin_id in temp_region:
        region_name = temp_region[admin_id]
        REGIONS.append(region_name)
        await query.edit_message_text(
            f"<b>✅ Viloyat qo'shildi:</b> {region_name}",
            parse_mode="HTML"
        )
        kb = get_admin_keyboard()
        await context.bot.send_message(
            admin_id,
            "<b>🔧 Admin Paneli</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        del temp_region[admin_id]
    await query.answer("✅ Viloyat qo'shildi!")

async def cancel_region_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    admin_id = int(query.data.split("_")[2])
    await query.edit_message_text(
        "<b>❌ Bekor qilindi</b>",
        parse_mode="HTML"
    )
    if admin_id in temp_region:
        del temp_region[admin_id]
    await query.answer("❌ Bekor qilindi!")

# ================= VIEW ALL USERS =================
async def view_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if not users:
        kb = get_admin_keyboard()
        await update.message.reply_text(
            "<b>Hozircha foydalanuvchi yo'q</b>",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        return
    text = f"<b>📋 Ro'yxatdagi foydalanuvchilar: {len(users)}</b>\n\n"
    for uid, data in users.items():
        text += f"👤 <b>{data['name']} {data['surname']}</b>\n"
        text += f"📞 {data['phone']}\n"
        text += f"📍 {data['region']}\n"
        text += f"📚 {data['course']}\n"
        text += f"🔗 {data['identifier']}\n\n"
    kb = [["↩️ Orqaga"]]
    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode="HTML"
    )

# ================= MAIN =================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    reg_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝"), register)],
        states={
            NAME: [MessageHandler(filters.TEXT, name)],
            SURNAME: [MessageHandler(filters.TEXT, surname)],
            AGE: [MessageHandler(filters.TEXT, age)],
            REGION: [MessageHandler(filters.TEXT, region)],
            COURSE: [MessageHandler(filters.TEXT, course)],
            PHONE: [MessageHandler(filters.CONTACT, phone)],
        },
        fallbacks=[]
    )

    course_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Kurs"), add_course_start)],
        states={
            ADD_COURSE: [MessageHandler(filters.TEXT, add_course)],
        },
        fallbacks=[]
    )

    remove_course_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🗑 Kurs"), remove_course_start)],
        states={
            REMOVE_COURSE: [MessageHandler(filters.TEXT, remove_course)],
        },
        fallbacks=[]
    )

    region_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Viloyat"), add_region_start)],
        states={
            ADD_REGION: [MessageHandler(filters.TEXT, add_region)],
            CONFIRM_REGION: [
                CallbackQueryHandler(confirm_region_callback, pattern="^confirm_region_"),
                CallbackQueryHandler(cancel_region_callback, pattern="^cancel_region_")
            ]
        },
        fallbacks=[]
    )

    remove_region_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🗑 Viloyat"), remove_region_start)],
        states={
            REMOVE_REGION: [MessageHandler(filters.TEXT, remove_region)],
        },
        fallbacks=[]
    )

    search_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔍"), search_users_start)],
        states={
            SEARCH_USERS: [MessageHandler(filters.TEXT, search_filter_choice)],
            FILTER_REGION: [MessageHandler(filters.TEXT, filter_by_region)],
            FILTER_COURSE: [MessageHandler(filters.TEXT, filter_by_course)],
        },
        fallbacks=[]
    )

    export_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📥"), export_start)],
        states={
            EXPORT_CHOICE: [MessageHandler(filters.TEXT, export_format)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(reg_conv)
    app.add_handler(course_conv)
    app.add_handler(remove_course_conv)
    app.add_handler(region_conv)
    app.add_handler(remove_region_conv)
    app.add_handler(search_conv)
    app.add_handler(export_conv)

    app.add_handler(MessageHandler(filters.Regex("^👤"), show_profile))
    app.add_handler(MessageHandler(filters.Regex("^📩 Admin"), contact_admin))
    app.add_handler(MessageHandler(filters.Regex("^📊"), view_all_users))
    app.add_handler(CallbackQueryHandler(callback, pattern="^admin_"))

    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_IDS), admin_message))
    app.add_handler(MessageHandler(filters.TEXT, user_message))

    app.run_polling()

if __name__ == "__main__":
    main()