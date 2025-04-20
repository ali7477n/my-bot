import telebot
from telebot import TeleBot, types
import json
import os

API_TOKEN = '7790079521:AAERlMDLnL-KjMLhOqxkE25rCTp7pdY2Db0'
ADMIN_ID = 7045418513

bot = telebot.TeleBot(API_TOKEN, parse_mode='HTML')

account_files = {
    '۲۰ گیگ': 'data/۲۰گیگ.txt',
    '۴۰ گیگ': 'data/۴۰گیگ.txt',
    '۶۰ گیگ': 'data/۶۰گیگ.txt',
    '۸۰ گیگ': 'data/۸۰گیگ.txt',
    '۱۰۰ گیگ': 'data/۱۰۰گیگ.txt'
}

pending_file = 'pending_requests.json'
ACCOUNTS_DIR = "data"

# اطمینان از وجود فایل فیش‌ها
if not os.path.exists(pending_file):
    with open(pending_file, 'w', encoding='utf-8') as f:
        json.dump({}, f)  # استفاده از دیکشنری خالی به جای لیست

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # تعریف markup اینجا
    markup.add(types.KeyboardButton("💳 خرید اکانت"))
    markup.add(types.KeyboardButton("🔄 تمدید اکانت"))
    bot.send_message(message.chat.id, "سلام 👋\nلطفاً یکی از گزینه‌های زیر را انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "💳 خرید اکانت")
def buy_account(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for plan in account_files:
        markup.add(types.KeyboardButton(plan))

    markup.add(types.KeyboardButton("🔙 برگشت به منوی اصلی"))  # دکمه برگشت به منوی اصلی
    bot.send_message(message.chat.id, "لطفاً یکی از پلن‌های زیر را برای خرید انتخاب کن:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🔄 تمدید اکانت")
def handle_renew_account(message):
    bot.send_message(message.chat.id, "لطفاً لینک اکانت خود را ارسال کنید.")
    bot.register_next_step_handler(message, get_account_link)

def get_account_link(message):
    user_link = message.text
    bot.send_message(message.chat.id, "لطفاً عکس فیش واریزی را ارسال کنید.")
    bot.register_next_step_handler(message, lambda msg: get_payment_proof(msg, user_link))

def get_payment_proof(message, user_link):
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, "❌ لطفاً فقط عکس فیش پرداخت را ارسال کنید.")
        bot.register_next_step_handler(message, lambda msg: get_payment_proof(msg, user_link))
        return

    # ارسال اطلاعات به ادمین
    caption = f"🧾 درخواست تمدید:\n\nلینک اکانت: {user_link}\n\n👤 @{message.from_user.username}\n📷 عکس فیش پرداخت"
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption)

    bot.send_message(message.chat.id, "✅ فیش شما ثبت شد. پس از بررسی توسط ادمین، اکانت شما تمدید خواهد شد.")

@bot.message_handler(func=lambda message: message.text == "🔙 برگشت به منوی اصلی")
def back_to_main_menu(message):
    start(message)  # برگشت به منوی اصلی

@bot.message_handler(func=lambda message: message.text in account_files)
def handle_plan_selection(message):
    plan = message.text
    bot.send_message(message.chat.id, f"✅ پلن {plan} انتخاب شد.\nلطفاً فیش پرداخت خود را فقط به صورت عکس ارسال کنید.")
    bot.register_next_step_handler(message, lambda msg: check_photo(msg, plan))

def check_photo(message, plan):
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, "❌ لطفاً فقط عکس فیش پرداخت را ارسال کنید.")
        bot.register_next_step_handler(message, lambda msg: check_photo(msg, plan))
        return
    save_request(message, plan)

def save_request(message, plan):
    try:
        with open(pending_file, 'r', encoding='utf-8') as f:
            requests = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # در صورتی که فایل وجود نداشته باشد، آن را به عنوان دیکشنری خالی شروع می‌کنیم
        requests = {}

    # ذخیره درخواست جدید
    requests[str(message.chat.id)] = {
        'user_id': message.chat.id,
        'username': message.from_user.username or '',
        'plan': plan,
        'proof': message.photo[-1].file_id
    }

    # ذخیره تغییرات در فایل
    with open(pending_file, 'w', encoding='utf-8') as f:
        json.dump(requests, f, ensure_ascii=False, indent=2)

    caption = f"🧾 درخواست جدید:\n👤 @{message.from_user.username or 'ندارد'}\n📦 پلن: {plan}"
    markup = approve_markup(message.chat.id, plan)
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup)

    bot.send_message(message.chat.id, "✅ فیش شما ثبت شد. پس از بررسی توسط ادمین، اکانت برایتان ارسال خواهد شد.")

# لود درخواست‌های در صف
def load_pending_requests():
    if os.path.exists(pending_file):
        with open(pending_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# ذخیره درخواست‌ها
def save_pending_requests(data):
    with open(pending_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# دریافت و حذف اولین اکانت از فایل پلن
def get_account_for_plan(plan_name):
    file_path = account_files.get(plan_name)
    if not file_path or not os.path.exists(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        return None

    account = lines[0].strip()  # اولین اکانت
    remaining = lines[1:]

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(remaining)  # باقی‌مانده رو ذخیره می‌کنیم

    return account

def approve_markup(user_id, plan):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            text=f"✅ تایید پرداخت - {plan}",
            callback_data=f"confirm_{user_id}"
        )
    )
    return markup

# هندل تأیید ادمین
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def handle_confirm(call):
    user_id = int(call.data.split("_")[1])
    pending = load_pending_requests()

    if str(user_id) not in pending:
        bot.answer_callback_query(call.id, "درخواستی برای این کاربر یافت نشد.")
        return

    plan = pending[str(user_id)]
    account = get_account_for_plan(plan['plan'])

    if not account:
        bot.send_message(call.message.chat.id, f"❌ اکانتی برای پلن «{plan['plan']}» یافت نشد.")
        return

    # ارسال اکانت به کاربر
    bot.send_message(user_id, f"✅ پرداخت شما تایید شد!\nاکانت شما:\n{account}")

    # پیام اطلاع‌رسانی به ادمین
    bot.send_message(call.message.chat.id, f"""🎉 اکانت ارسال شد!

👤 مشتری: {user_id}
📦 پلن: {plan['plan']}
""")

    # حذف از لیست درخواست‌ها
    del pending[str(user_id)]
    save_pending_requests(pending)

    # حذف دکمه‌ها از پیام قبلی
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    bot.answer_callback_query(call.id, "تایید شد و اکانت ارسال گردید ✅")

bot.infinity_polling()
