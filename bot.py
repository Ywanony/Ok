import asyncio
import logging
import random
import string
import sys
import time

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
)
from aiogram.exceptions import TelegramNetworkError

from supabase import Client, create_client


# ============================================================
# CONFIGURATION
# ============================================================

BOT_TOKEN = "8973762383:AAFUhern9b6r6UxWn78NBiaCidu2VE_7bgw"

ADMIN_IDS = [
    8863002910,
    8459158216,
]

SUPPORT_USERNAME = "VlPSuppot"
PUBLIC_DEMO_CHANNEL_LINK = "https://t.me/AII_vip_groups"

# Supabase Credentials
SUPABASE_URL = "https://rzpowbdtzbeivhxkkern.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ6cG93YmR0emJlaXZoeGtrZXJuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NDg3NjgxNywiZXhwIjoyMTAwNDUyODE3fQ.AJS-KdbAgUPNTZ9cIhT55W2X7x17JhlYgtZ5VnOH0jo"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ============================================================
# IMAGES
# ============================================================

INTRO_IMAGE_URL = "https://i.ibb.co/JbDHr17/x.jpg"
CUSTOM_PLAN_QR = "https://i.ibb.co/8DzYrm42/x.jpg"
DEFAULT_BANNER_URL = "https://i.ibb.co/wNKNQDGy/x.jpg"


# ============================================================
# PRICING PLANNERS & CATEGORIES
# ============================================================

PRICING_PLANS = {
    "49": {
        "price": 49,
        "label": "1 Group Starter Plan - ₹49",
        "group_text": "1 Group"
    },
    "99": {
        "price": 99,
        "label": "3 Groups Plan - ₹99",
        "group_text": "3 Groups"
    },
    "249": {
        "price": 249,
        "label": "10 Groups Plan - ₹249",
        "group_text": "10 Groups"
    }
}

ALL_COLLECTION_PLANS = {
    "350": {
        "price": 350,
        "label": "All Zip 5247+ Files - ₹350",
        "group_text": "5247+ Files"
    },
    "499": {
        "price": 499,
        "label": "All Mega 23 Groups - ₹499",
        "group_text": "23 Groups"
    },
    "749": {
        "price": 749,
        "label": "Mega Links + Zip Both - ₹749",
        "group_text": "Mega Links + Zip"
    }
}

CATEGORIES = {
    "cat_all": "🔥 𝖠𝖫𝖫 𝖢𝖮𝖫𝖫𝖤𝖢𝖳𝖨𝖮𝖭 𝖡𝖴𝖸 🔞",
    "cat_study": "CP,RP😍",
    "cat_material": "DESI LEAKED💧",
    "cat_newone": "MOM SON+PEDO",
    "cat_member": "HIDDEN,TANGO",
    "cat_java": "PAK,JAPANESE",
    "cat_python": "MALLU/TAMIL🤩",
}

CATEGORY_PHOTOS = {
    "cat_all": "https://i.ibb.co/6cy5fQjJ/x.jpg",
    "cat_study": "https://i.ibb.co/TMsv6GGf/x.jpg",
    "cat_material": "https://i.ibb.co/Cp4Mdfnb/x.jpg",
    "cat_newone": "https://i.ibb.co/wrS6wxh3/x.jpg",
    "cat_member": "https://i.ibb.co/RTWYpzHW/x.jpg",
    "cat_java": "https://i.ibb.co/RGvhX5rt/x.jpg",
    "cat_python": "https://i.ibb.co/Z6632LTn/x.jpg",
}


# ============================================================
# ROUTER & STATES
# ============================================================

router = Router()

class PaymentStates(StatesGroup):
    waiting_for_screenshot = State()
    waiting_for_custom_link = State()
    waiting_for_rejection_reason = State()
    waiting_for_broadcast_msg = State()


# ============================================================
# HELPERS
# ============================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def generate_order_id():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=9))

def supabase_request_with_retry(query_func, retries=3, delay=2):
    for attempt in range(retries):
        try:
            return query_func()
        except Exception as e:
            error_text = str(e)
            if any(err in error_text for err in ["11001", "getaddrinfo", "Temporary failure"]):
                logging.warning(f"Database DNS error (Attempt {attempt + 1}/{retries}): {e}")
                if attempt == retries - 1:
                    raise
                time.sleep(delay)
            else:
                raise

def log_user_to_db(user):
    try:
        supabase_request_with_retry(
            lambda: supabase.table("bot_users").upsert({
                "user_id": user.id,
                "full_name": user.full_name,
                "username": f"@{user.username}" if user.username else "No Username",
            }).execute()
        )
    except Exception as e:
        logging.error(f"Supabase user log error: {e}")

async def safe_edit_message(message: Message, text: str, reply_markup: InlineKeyboardMarkup, photo_url: str = None):
    try:
        if photo_url and message.photo:
            await message.edit_media(
                media=InputMediaPhoto(media=photo_url, caption=text, parse_mode=ParseMode.MARKDOWN),
                reply_markup=reply_markup
            )
        elif photo_url:
            await message.delete()
            await message.answer_photo(photo=photo_url, caption=text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        elif message.photo:
            await message.delete()
            await message.answer(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await message.edit_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logging.info(f"Fallback answer triggered: {e}")
        if photo_url:
            await message.answer_photo(photo=photo_url, caption=text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await message.answer(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)


# ============================================================
# KEYBOARDS
# ============================================================

def get_main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=" 🔥 𝖡𝗎𝗒 𝖬𝖾𝗆𝖻𝖾𝗋𝗌𝗁𝗂𝗉 ", callback_data="buy_membership")],
            [InlineKeyboardButton(text=" 🔍 𝖢𝗁𝖾𝖼𝗄 𝖲𝗍𝖺𝗍𝗎𝗌 ", callback_data="check_status")],
            [InlineKeyboardButton(text=" 🔞 𝖯𝗋𝖾𝗆𝗂𝗎𝗆 𝖣𝖾𝗆𝗈 ", callback_data="demo_preview")],
            [InlineKeyboardButton(text=" 💬 𝖢𝗈𝗇𝗍𝖺𝖼𝗍 𝖲𝗎𝗉𝗉𝗈𝗋𝗍 ", callback_data="support")],
        ]
    )

def get_membership_categories_keyboard():
    keys = list(CATEGORIES.keys())
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🌟 {CATEGORIES[keys[0]]}", callback_data=keys[0])],
            [
                InlineKeyboardButton(text=f"🔹 {CATEGORIES[keys[1]]}", callback_data=keys[1]),
                InlineKeyboardButton(text=f"🔹 {CATEGORIES[keys[2]]}", callback_data=keys[2]),
            ],
            [
                InlineKeyboardButton(text=f"🔹 {CATEGORIES[keys[3]]}", callback_data=keys[3]),
                InlineKeyboardButton(text=f"🔹 {CATEGORIES[keys[4]]}", callback_data=keys[4]),
            ],
            [
                InlineKeyboardButton(text=f"🔹 {CATEGORIES[keys[5]]}", callback_data=keys[5]),
                InlineKeyboardButton(text=f"🔹 {CATEGORIES[keys[6]]}", callback_data=keys[6]),
            ],
            [InlineKeyboardButton(text="« [ Back to Main Menu ]", callback_data="main_menu")],
        ]
    )

def get_membership_plans_keyboard(category_code: str):
    if category_code == "cat_all":
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"⭐ [ {ALL_COLLECTION_PLANS['350']['label']} ]", callback_data=f"plan_350_{category_code}")],
                [InlineKeyboardButton(text=f"⚡ [ {ALL_COLLECTION_PLANS['499']['label']} ]", callback_data=f"plan_499_{category_code}")],
                [InlineKeyboardButton(text=f"🔥 [ {ALL_COLLECTION_PLANS['749']['label']} ]", callback_data=f"plan_749_{category_code}")],
                [InlineKeyboardButton(text="« [ Back to Categories ]", callback_data="buy_membership")],
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"⭐ [ {PRICING_PLANS['49']['label']} ]", callback_data=f"plan_49_{category_code}")],
            [InlineKeyboardButton(text=f"⚡ [ {PRICING_PLANS['99']['label']} ]", callback_data=f"plan_99_{category_code}")],
            [InlineKeyboardButton(text=f"🔥 [ {PRICING_PLANS['249']['label']} ]", callback_data=f"plan_249_{category_code}")],
            [InlineKeyboardButton(text="« [ Back to Categories ]", callback_data="buy_membership")],
        ]
    )

def get_admin_panel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 View History", callback_data="admin_history"),
                InlineKeyboardButton(text="📈 Stats & Users", callback_data="admin_stats"),
            ],
            [InlineKeyboardButton(text="📢 Broadcast Message", callback_data="admin_broadcast_start")],
        ]
    )


# ============================================================
# USER HANDLERS
# ============================================================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    log_user_to_db(message.from_user)
    welcome_text = (
        "🔥 **Welcome to Exclusive Premium Videos!**\n\n"
        "⚡ *Tap the buttons below to unlock your access "
        "or check your subscription status.*"
    )
    await message.answer_photo(
        photo=INTRO_IMAGE_URL,
        caption=welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

@router.callback_query(F.data == "main_menu")
async def process_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    menu_text = (
        "🔥 **Welcome to Exclusive Premium Videos!**\n\n"
        "⚡ *Tap the buttons below to unlock your access "
        "or check your subscription status.*"
    )
    await safe_edit_message(callback.message, menu_text, get_main_menu_keyboard(), photo_url=INTRO_IMAGE_URL)
    await callback.answer()

@router.callback_query(F.data == "buy_membership")
async def process_buy_membership(callback: CallbackQuery):
    plans_text = (
        "💎 **𝗦𝗮𝗹𝗲𝗰𝘁 𝘄𝗵𝗶𝗰𝗵 𝗰𝗮𝘁𝗲𝗴𝗼𝗿𝘆 𝘆𝗼𝘂 𝘄𝗮𝗻𝘁.**\n\n"
        "Choose any category option below to open the corresponding plan checkout:"
    )
    await safe_edit_message(callback.message, plans_text, get_membership_categories_keyboard(), photo_url=DEFAULT_BANNER_URL)
    await callback.answer()

@router.callback_query(F.data.in_(list(CATEGORIES.keys())))
async def process_selected_category(callback: CallbackQuery, state: FSMContext):
    cat_code = callback.data
    await state.update_data(current_category=cat_code)
    category_display_name = CATEGORIES.get(cat_code, "Premium")
    category_photo = CATEGORY_PHOTOS.get(cat_code, DEFAULT_BANNER_URL)
    
    plan_select_text = (
        f"💎 **𝗦𝗮𝗹𝗲𝗰𝘁 𝘆𝗼𝘂𝗿 𝗩𝗜𝗣 𝗺𝗲𝗺𝗯𝗲𝗿𝘀𝗵𝗶𝗽 𝗽𝗹𝗮𝗻 𝗳𝗼𝗿 {category_display_name}**\n\n"
        "Choose a plan from the options below:"
    )
    await safe_edit_message(callback.message, plan_select_text, get_membership_plans_keyboard(cat_code), photo_url=category_photo)
    await callback.answer()

@router.callback_query(F.data.startswith("plan_"))
async def process_selected_plan(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    amount_str = parts[1]
    cat_code = f"{parts[2]}_{parts[3]}" if len(parts) > 3 else parts[2]
    order_id = generate_order_id()

    if cat_code == "cat_all":
        plan_info = ALL_COLLECTION_PLANS.get(amount_str, ALL_COLLECTION_PLANS["350"])
    else:
        plan_info = PRICING_PLANS.get(amount_str, PRICING_PLANS["49"])

    amount = plan_info["price"]
    group_text = plan_info["group_text"]
    category_clean_name = CATEGORIES.get(cat_code, "VIP Plan")
    full_plan_name = f"{plan_info['label']} - {category_clean_name}"

    await state.update_data(
        current_order_id=order_id,
        current_amount=amount,
        current_plan_name=full_plan_name
    )

    details_text = (
        f"🎁 **𝗖𝗮𝘁𝗲𝗴𝗼𝗿𝘆 & 𝗣𝗹𝗮𝗻:** {full_plan_name}\n"
        f"💰 **𝗔𝗺𝗼𝘂𝗻𝘁:** ₹{amount} INR\n"
        f"👥 **𝗚𝗿𝗼𝘂𝗽𝘀:** {group_text}\n"
        f"🆔 **𝗢𝗿𝗱𝗲𝗿 𝗜𝗱:** `{order_id}`\n\n"
        "📱 **Pay using any UPI app** (GPay, PhonePe, Paytm)\n\n"
        "⏱️ *𝖰𝖱 𝖼𝗈𝖽𝖾 𝗂𝗌 𝗏𝖺𝗅𝗂𝖽 𝖿𝗈𝗋 10 𝗆𝗂𝗇𝗎𝗍𝖾𝗌 𝗈𝗇𝗅𝗒*\n\n"
        "📲 **Scan the QR Code above to pay.**\n"
        "👇 Click **'I Have Paid'** after completing payment."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 I Have Paid ", callback_data="pay_now")],
            [InlineKeyboardButton(text="« Back to Plans ", callback_data=cat_code)],
        ]
    )
    await safe_edit_message(callback.message, details_text, keyboard, photo_url=CUSTOM_PLAN_QR)
    await callback.answer()

# FIX: Set waiting for screenshot state when user clicks 'I Have Paid'
@router.callback_query(F.data == "pay_now")
async def process_pay_now(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PaymentStates.waiting_for_screenshot)
    await callback.message.answer(
        "📸 **Please send the payment screenshot now.**\n\n"
        "After confirm payment, you'll get link here in 2 minutes.",
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer()

@router.message(PaymentStates.waiting_for_screenshot, F.photo)
async def receive_screenshot(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    user = message.from_user
    username = f"@{user.username}" if user.username else "No Username"
    data = await state.get_data()

    order_id = data.get("current_order_id", generate_order_id())
    amount = data.get("current_amount", 49)
    duration = data.get("current_duration", 30)
    plan_name = data.get("current_plan_name", "VIP Collection")

    log_user_to_db(user)

    try:
        supabase_request_with_retry(
            lambda: supabase.table("payments").insert({
                "user_id": user.id,
                "order_id": order_id,
                "username": username,
                "plan_name": plan_name,
                "amount": amount,
                "duration_days": duration,
                "photo_id": photo_id,
                "status": "pending",
            }).execute()
        )
    except Exception as e:
        logging.error(f"Supabase payment entry error: {e}")

    await message.answer(
        "⏳ **Payment Screenshot Received!**\n\n"
        "Please wait. Verification will be done by our admin team.\n"
        "Your access link will be sent here shortly.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="« [ Back to Main Menu ]", callback_data="main_menu")]]
        ),
        parse_mode=ParseMode.MARKDOWN
    )
    await state.clear()

    admin_caption = (
        "🚨 <b>NEW PAYMENT PENDING VERIFICATION</b> 🚨\n\n"
        f"👤 <b>Name:</b> {user.full_name}\n"
        f"🔗 <b>Username:</b> <code>{username}</code>\n"
        f"🆔 <b>Chat/User ID:</b> <code>{user.id}</code>\n"
        f"📦 <b>Plan Selected:</b> {plan_name}\n"
        f"💰 <b>Amount Transferred:</b> ₹{amount}\n"
        f"🏷️ <b>Order ID:</b> <code>{order_id}</code>\n\n"
        "👉 <i>Review screenshot and choose action:</i>"
    )

    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_{user.id}_{order_id}"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{user.id}_{order_id}"),
            ]
        ]
    )

    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_photo(
                chat_id=admin_id,
                photo=photo_id,
                caption=admin_caption,
                reply_markup=admin_keyboard,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logging.error(f"Failed to notify admin {admin_id}: {e}")

@router.message(PaymentStates.waiting_for_screenshot)
async def invalid_screenshot_type(message: Message):
    await message.answer("⚠️ Please send a valid **image/screenshot** of your payment receipt.", parse_mode=ParseMode.MARKDOWN)

@router.callback_query(F.data == "check_status")
async def process_check_status(callback: CallbackQuery):
    user_id = callback.from_user.id
    try:
        res = supabase_request_with_retry(
            lambda: supabase.table("payments").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
        )
        if res.data:
            record = res.data[0]
            status_msg = (
                "🔍 **Subscription Status**\n\n"
                f"Plan: {record['plan_name']}\n"
                f"Order ID: `{record['order_id']}`\n"
                f"Status: **{str(record['status']).upper()}**"
            )
        else:
            status_msg = "🔍 **Subscription Status**\n\n❌ You do not have an active subscription yet."
    except Exception:
        status_msg = "🔍 **Subscription Status**\n\n❌ Could not fetch data from database."

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="  🛍️ Buy Membership ", callback_data="buy_membership")],
            [InlineKeyboardButton(text="«  Back to Main Menu ", callback_data="main_menu")],
        ]
    )
    await safe_edit_message(callback.message, status_msg, keyboard, photo_url=INTRO_IMAGE_URL)
    await callback.answer()

@router.callback_query(F.data == "demo_preview")
async def process_demo(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Tap Here to View Demo Preview", url=PUBLIC_DEMO_CHANNEL_LINK)],
            [InlineKeyboardButton(text="«  Back to Main Menu ", callback_data="main_menu")],
        ]
    )
    await safe_edit_message(
        callback.message,
        "🚀 **Premium Demo Channel**\n\nClick below to join our public demo channel:",
        keyboard,
        photo_url=DEFAULT_BANNER_URL
    )
    await callback.answer()

@router.callback_query(F.data == "support")
async def process_support(callback: CallbackQuery):
    support_text = "💬 **Customer Support**\n\nContact support admin directly:"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Contact Support Admin", url=f"https://t.me/{SUPPORT_USERNAME}")],
            [InlineKeyboardButton(text="« [ Back to Main Menu ]", callback_data="main_menu")],
        ]
    )
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(support_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
    await callback.answer()


# ============================================================
# ADMIN ACTIONS
# ============================================================

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ **Access Denied.**")
        return
    await message.answer("👑 **Admin Control Hub**\nSelect an operation:", reply_markup=get_admin_panel_keyboard())

@router.message(Command("history"))
async def cmd_history(message: Message):
    if not is_admin(message.from_user.id):
        return
    await send_history_view(message)

async def send_history_view(target_message):
    try:
        res = supabase_request_with_retry(
            lambda: supabase.table("payments").select("*").order("created_at", desc=True).limit(10).execute()
        )
        if not res.data:
            await target_message.answer("📂 No payment records found.")
            return

        text = "📊 **Recent Payment Records:**\n\n"
        for r in res.data:
            text += (
                f"🆔 Chat/User ID: `{r.get('user_id')}`\n"
                f"🔗 Username: {r.get('username')}\n"
                f"📦 Plan: {r.get('plan_name')} | Amt: ₹{r.get('amount')}\n"
                f"🏷️ Order: `{r.get('order_id')}` | Status: **{str(r.get('status')).upper()}**\n"
                "-------------------\n"
            )
        await target_message.answer(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await target_message.answer(f"❌ Error fetching history: {e}")

@router.callback_query(F.data == "admin_history")
async def process_admin_history_cb(callback: CallbackQuery):
    if is_admin(callback.from_user.id):
        await send_history_view(callback.message)
    await callback.answer()

@router.callback_query(F.data == "admin_stats")
async def process_admin_stats_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    try:
        users_res = supabase_request_with_retry(lambda: supabase.table("bot_users").select("user_id", count="exact").execute())
        pay_res = supabase_request_with_retry(lambda: supabase.table("payments").select("id", count="exact").execute())

        total_users = users_res.count if hasattr(users_res, "count") else len(users_res.data)
        total_payments = pay_res.count if hasattr(pay_res, "count") else len(pay_res.data)

        stats_text = (
            "📈 **Bot Statistics & Database Overview**\n\n"
            f"👥 **Total Users:** `{total_users}`\n"
            f"💳 **Total Orders:** `{total_payments}`"
        )
        await callback.message.answer(stats_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await callback.message.answer(f"❌ Error pulling stats: {e}")
    await callback.answer()

@router.callback_query(F.data == "admin_broadcast_start")
async def process_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(PaymentStates.waiting_for_broadcast_msg)
    await callback.message.answer("📢 **Broadcast Setup**\nSend the message content to broadcast:")
    await callback.answer()

@router.message(PaymentStates.waiting_for_broadcast_msg, F.from_user.id.in_(ADMIN_IDS))
async def execute_broadcast(message: Message, state: FSMContext):
    content = message.text or message.caption or ""
    try:
        users_res = supabase_request_with_retry(lambda: supabase.table("bot_users").select("user_id").execute())
        success, failed = 0, 0
        for user in users_res.data:
            try:
                await message.bot.send_message(chat_id=user["user_id"], text=f"📢 **Announcement:**\n\n{content}", parse_mode=ParseMode.MARKDOWN)
                success += 1
                await asyncio.sleep(0.05)
            except Exception:
                failed += 1
        await message.answer(f"✅ **Broadcast Completed!**\nDelivered: `{success}`\nFailed: `{failed}`")
    except Exception as e:
        await message.answer(f"❌ Broadcast error: {e}")
    await state.clear()

@router.callback_query(F.data.startswith("approve_"))
async def admin_approve_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    parts = callback.data.split("_")
    await state.set_state(PaymentStates.waiting_for_custom_link)
    await state.update_data(target_user_id=int(parts[1]), order_id=parts[2])
    await callback.message.answer(f"🔗 Send the invite link for Order `{parts[2]}` (User `{parts[1]}`):")
    await callback.answer()

@router.message(PaymentStates.waiting_for_custom_link, F.from_user.id.in_(ADMIN_IDS))
async def process_custom_link_input(message: Message, state: FSMContext):
    data = await state.get_data()
    target_user_id, order_id = data.get("target_user_id"), data.get("order_id")
    invite_link = (message.text or "").strip()

    if not target_user_id or not order_id:
        await message.answer("❌ Session error. Try again.")
        await state.clear()
        return

    try:
        supabase_request_with_retry(
            lambda: supabase.table("payments").update({"status": "approved", "admin_reason": invite_link}).eq("order_id", order_id).execute()
        )
        await message.bot.send_message(
            chat_id=target_user_id,
            text=f"🎉 **Payment Approved!**\n\nPrivate link:\n{invite_link}",
            parse_mode=ParseMode.MARKDOWN
        )
        await message.answer(f"✅ Approved and link sent to `{target_user_id}`!")
    except Exception as e:
        await message.answer(f"❌ Error during approval: {e}")
    await state.clear()

@router.callback_query(F.data.startswith("reject_"))
async def admin_reject_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    parts = callback.data.split("_")
    await state.set_state(PaymentStates.waiting_for_rejection_reason)
    await state.update_data(target_user_id=int(parts[1]), order_id=parts[2])
    await callback.message.answer(f"❌ Type reason for rejecting Order `{parts[2]}`:")
    await callback.answer()

@router.message(PaymentStates.waiting_for_rejection_reason, F.from_user.id.in_(ADMIN_IDS))
async def process_rejection_reason_input(message: Message, state: FSMContext):
    data = await state.get_data()
    target_user_id, order_id = data.get("target_user_id"), data.get("order_id")
    reason = (message.text or "").strip()

    try:
        supabase_request_with_retry(
            lambda: supabase.table("payments").update({"status": "rejected", "admin_reason": reason}).eq("order_id", order_id).execute()
        )
        await message.bot.send_message(
            chat_id=target_user_id,
            text=f"❌ **Payment Rejected!**\n\n📌 **Reason:** {reason}",
            parse_mode=ParseMode.MARKDOWN
        )
        await message.answer(f"✅ Rejection sent to user `{target_user_id}`.")
    except Exception as e:
        await message.answer(f"❌ Error rejecting order: {e}")
    await state.clear()


# ============================================================
# MAIN ENTRYPOINT
# ============================================================

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)

    while True:
        try:
            logging.info("Starting polling...")
            await dp.start_polling(bot)
        except TelegramNetworkError as e:
            logging.warning(f"Network error: {e}. Reconnecting...")
            await asyncio.sleep(3)
        except Exception as e:
            logging.error(f"Polling exception: {e}. Restarting...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped safely.")
