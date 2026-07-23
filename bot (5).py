import asyncio
import logging
import random
import string
import sys
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Message
from aiogram.exceptions import TelegramNetworkError
from supabase import Client, create_client

# ==================== ADVANCED CONFIGURATION & SETTINGS ====================
BOT_TOKEN = "8629987412:AAEFQPaUjZBC8YKoki_7dVU5-hVm5BHF7Jc"

# Multiple Admin IDs Support
ADMIN_IDS = [8740270617, 8459158216]  

SUPPORT_USERNAME = "VlPSuppot"  # Without '@'
PUBLIC_DEMO_CHANNEL_LINK = "https://t.me/D3mo_group"

# Supabase Credentials
SUPABASE_URL = "https://xemwpqqlxmpkrsdzpdwu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhlbXdwcXFseG1wa3JzZHpwZHd1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4Mzk1MTkwNiwiZXhwIjoyMDk5NTI3OTA2fQ._2Smw4MsHqeJkSzSUrBWFWUrQ8UClOmAeYWNf4lGStc"

# Custom Images & Banners
INTRO_IMAGE_URL = "https://i.ibb.co/JbDHr17/x.jpg"
CUSTOM_PLAN_QR = "https://i.ibb.co/8DzYrm42/x.jpg"
DEFAULT_BANNER_URL = "https://i.ibb.co/wNKNQDGy/x.jpg"

# ==================== DYNAMIC PRICING & PLANS CONFIG ====================
# You can easily change prices, durations, or plan titles right here anytime!
PRICING_PLANS = {
    "199": {"price": 199, "days": 30, "label": "Starter Plan - ₹199 / 30 Days", "duration_text": "30 Days"},
    "399": {"price": 399, "days": 180, "label": "Standard Plan - ₹399 / 6 Months", "duration_text": "6 Months"},
    "499": {"price": 499, "days": 9999, "label": "Lifetime VIP Plan - ₹499 / Lifetime", "duration_text": "Lifetime"}
}

# ==================== DYNAMIC CATEGORY BUTTON NAMES ====================
CATEGORIES = {
    "cat_study": "CP,RP😍",
    "cat_material": "DESI LEAKED💧",
    "cat_newone": "MOM SON+PEDO",
    "cat_member": "HIDDEN,TANGO",
    "cat_java": "PAK,JAPANESE",
    "cat_python": "MALLU/TAMIL🤩",
    "cat_all": "🔥 𝖠𝖫𝖫 𝖢𝖮𝖫𝖫𝖤𝖢𝖳𝖨𝖮𝖭 𝖡𝖴𝖸 🔞"
}

# ==================== UNIQUE PHOTOS FOR EACH CATEGORY ====================
CATEGORY_PHOTOS = {
    "cat_study": "https://i.ibb.co/TMsv6GGf/x.jpg",
    "cat_material": "https://i.ibb.co/Cp4Mdfnb/x.jpg",
    "cat_newone": "https://i.ibb.co/wrS6wxh3/x.jpg",
    "cat_member": "https://i.ibb.co/RTWYpzHW/x.jpg",
    "cat_java": "https://i.ibb.co/RGvhX5rt/x.jpg",
    "cat_python": "https://i.ibb.co/Z6632LTn/x.jpg",
    "cat_all": "https://i.ibb.co/6cy5fQjJ/x.jpg"
}
# ===========================================================================

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
router = Router()

class PaymentStates(StatesGroup):
    waiting_for_screenshot = State()
    waiting_for_custom_link = State()
    waiting_for_rejection_reason = State()
    waiting_for_broadcast_msg = State()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def log_user_to_db(user):
    try:
        supabase.table("bot_users").upsert({
            "user_id": user.id,
            "full_name": user.full_name,
            "username": f"@{user.username}" if user.username else "No Username",
        }).execute()
    except Exception as e:
        logging.error(f"Supabase user log error: {e}")

def get_main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="[ 🔥 𝖡𝗎𝗒 𝖬𝖾𝗆𝖻𝖾𝗋𝗌𝗁𝗂𝗉 ]", callback_data="buy_membership")],
            [InlineKeyboardButton(text="[ 🔍 𝖢𝗁𝖾𝖼𝗄 𝖲𝗍𝖺𝗍𝗎𝗌 ]", callback_data="check_status")],
            [InlineKeyboardButton(text="[ 🔞 𝖯𝗋𝖾𝗆𝗂𝗎𝗆 𝖣𝖾𝗆𝗈 ]", callback_data="demo_preview")],
            [InlineKeyboardButton(text="[ 💬 𝖢𝗈𝗇𝗍𝖺𝖼𝗍 𝖲𝗎𝗉𝗉𝗈𝗋𝗍 ]", callback_data="support")],
        ]
    )

def get_membership_categories_keyboard():
    keys = list(CATEGORIES.keys())
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"🔹 {CATEGORIES[keys[0]]}", callback_data=keys[0]),
                InlineKeyboardButton(text=f"🔹 {CATEGORIES[keys[1]]}", callback_data=keys[1]),
            ],
            [
                InlineKeyboardButton(text=f"🔹 {CATEGORIES[keys[2]]}", callback_data=keys[2]),
                InlineKeyboardButton(text=f"🔹 {CATEGORIES[keys[3]]}", callback_data=keys[3]),
            ],
            [
                InlineKeyboardButton(text=f"🔹 {CATEGORIES[keys[4]]}", callback_data=keys[4]),
                InlineKeyboardButton(text=f"🔹 {CATEGORIES[keys[5]]}", callback_data=keys[5]),
            ],
            [
                InlineKeyboardButton(text=f"🌟 {CATEGORIES[keys[6]]}", callback_data=keys[6]),
            ],
            [InlineKeyboardButton(text="« [ Back to Main Menu ]", callback_data="main_menu")],
        ]
    )

# Universal 3-tier plan layout for all 7 buttons
def get_membership_plans_keyboard(category_code: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"⭐ [ {PRICING_PLANS['199']['label']} ]", callback_data=f"plan_199_{category_code}")],
            [InlineKeyboardButton(text=f"⚡ [ {PRICING_PLANS['399']['label']} ]", callback_data=f"plan_399_{category_code}")],
            [InlineKeyboardButton(text=f"🔥 [ {PRICING_PLANS['499']['label']} ]", callback_data=f"plan_499_{category_code}")],
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

def generate_order_id():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=9))

def escape_markdown_safe(text: str) -> str:
    for char in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
        text = text.replace(char, f"\\{char}")
    return text

async def safe_edit_message(message: Message, text: str, reply_markup: InlineKeyboardMarkup, photo_url: str = None):
    try:
        if photo_url and message.photo:
            await message.edit_media(media=InputMediaPhoto(media=photo_url, caption=text, parse_mode=ParseMode.MARKDOWN), reply_markup=reply_markup)
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

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    log_user_to_db(message.from_user)
    welcome_text = (
        "🔥 **Welcome to Exclusive Premium Videos!**\n\n"
        "⚡ *Tap the buttons below to unlock your access or check your subscription status.*"
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
        "⚡ *Tap the buttons below to unlock your access or check your subscription status.*"
    )
    await safe_edit_message(callback.message, menu_text, get_main_menu_keyboard(), photo_url=INTRO_IMAGE_URL)
    await callback.answer()

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ **Access Denied:** You are not authorized to use admin tools.")
        return
    await message.answer("👑 **Admin Control Hub**\nSelect an operation below:", reply_markup=get_admin_panel_keyboard())

@router.message(Command("history"))
async def cmd_history(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ **Access Denied:** Unauthorized.")
        return
    await send_history_view(message)

async def send_history_view(target_message):
    try:
        res = supabase.table("payments").select("*").order("created_at", desc=True).limit(10).execute()
        records = res.data
        if not records:
            await target_message.answer("📂 No payment records found in database.")
            return

        text = "📊 **Recent Payment Records (Supabase):**\n\n"
        for r in records:
            uname = r.get("username") or "No Username"
            chat_id = r.get("user_id")
            text += (
                f"🆔 Chat/User ID: `{chat_id}`\n"
                f"🔗 Username: {uname}\n"
                f"📦 Plan: {r['plan_name']} | Amt: ₹{r['amount']}\n"
                f"🏷️ Order: `{r['order_id']}` | Status: **{r['status'].upper()}**\n"
                f"🕒 Date: {r['created_at'][:19]}\n-------------------\n"
            )
        await target_message.answer(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await target_message.answer(f"❌ Failed to fetch database history: {e}")

@router.callback_query(F.data == "admin_history")
async def process_admin_history_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await send_history_view(callback.message)
    await callback.answer()

@router.callback_query(F.data == "admin_stats")
async def process_admin_stats_cb(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    try:
        users_res = supabase.table("bot_users").select("user_id", count="exact").execute()
        pay_res = supabase.table("payments").select("id", count="exact").execute()
        total_users = users_res.count if hasattr(users_res, "count") else len(users_res.data)
        total_payments = pay_res.count if hasattr(pay_res, "count") else len(pay_res.data)

        stats_text = (
            "📈 **Bot Statistics & Database Overview**\n\n"
            f"👥 **Total Registered Users:** `{total_users}`\n"
            f"💳 **Total Payment Orders:** `{total_payments}`"
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
    await callback.message.answer("📢 **Broadcast Setup**\n\nSend the text or content you want to broadcast to all users:")
    await callback.answer()

@router.message(PaymentStates.waiting_for_broadcast_msg, F.from_user.id.in_(ADMIN_IDS))
async def execute_broadcast(message: Message, state: FSMContext):
    content = message.text or message.caption or ""
    try:
        users_res = supabase.table("bot_users").select("user_id").execute()
        users = users_res.data
        success, failed = 0, 0
        for u in users:
            try:
                await message.bot.send_message(chat_id=u["user_id"], text=f"📢 **Announcement:**\n\n{content}", parse_mode=ParseMode.MARKDOWN)
                success += 1
                await asyncio.sleep(0.05)
            except Exception:
                failed += 1
        await message.answer(f"✅ **Broadcast Completed!**\n\nDelivered: `{success}`\nFailed/Blocked: `{failed}`")
    except Exception as e:
        await message.answer(f"❌ Broadcast error: {e}")
    await state.clear()

@router.callback_query(F.data == "buy_membership")
async def process_buy_membership(callback: CallbackQuery):
    plans_text = (
        "💎 **Select Your VIP Membership Category**\n\n"
        "Choose any category option below to open the corresponding plan checkout:"
    )
    await safe_edit_message(callback.message, plans_text, get_membership_categories_keyboard(), photo_url=DEFAULT_BANNER_URL)
    await callback.answer()

# Handles all 7 category buttons dynamically with its unique respective photo
@router.callback_query(F.data.in_(list(CATEGORIES.keys())))
async def process_selected_category(callback: CallbackQuery, state: FSMContext):
    cat_code = callback.data
    await state.update_data(current_category=cat_code)
    
    category_display_name = CATEGORIES.get(cat_code, "Premium")
    category_photo = CATEGORY_PHOTOS.get(cat_code, DEFAULT_BANNER_URL)

    plan_select_text = (
        f"💎 **Select Your VIP Membership Plan for {category_display_name}**\n\n"
        "Choose a duration and tier that fits your needs best from the options below:"
    )
    await safe_edit_message(callback.message, plan_select_text, get_membership_plans_keyboard(cat_code), photo_url=category_photo)
    await callback.answer()

@router.callback_query(F.data.startswith("plan_"))
async def process_selected_plan(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    amount_str = parts[1]
    cat_code = f"{parts[2]}_{parts[3]}" if len(parts) > 3 else parts[2]
    order_id = generate_order_id()

    plan_info = PRICING_PLANS.get(amount_str, PRICING_PLANS["499"])
    amount = plan_info["price"]
    duration_days = plan_info["days"]
    duration_text = plan_info["duration_text"]
    
    category_clean_name = CATEGORIES.get(cat_code, "VIP Plan")
    full_plan_name = f"{plan_info['label']} - {category_clean_name}"

    await state.update_data(
        current_order_id=order_id,
        current_amount=amount,
        current_duration=duration_days,
        current_plan_name=full_plan_name
    )

    details_text = (
        f"🎁 **Category & Plan:** {full_plan_name}\n"
        f"💰 **Amount:** {amount} INR\n"
        f"⏳ **Access Duration:** {duration_text}\n"
        f"🆔 **Order ID:** `{order_id}`\n"
        "📱 **Pay using any UPI app** (GPay, PhonePe, Paytm)\n"
        "⏱️ *QR code is valid for 15 minutes only*\n\n"
        "📲 **Scan the QR Code above to pay.**\n"
        "👇 Click **'I Have Paid'** after completing the payment transaction."
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 [ I Have Paid ]", callback_data="pay_now")],
            [InlineKeyboardButton(text="« [ Back to Plans ]", callback_data=cat_code)],
        ]
    )
    # Displays the payment QR Code
    await safe_edit_message(callback.message, details_text, keyboard, photo_url=CUSTOM_PLAN_QR)
    await callback.answer()

@router.callback_query(F.data == "pay_now")
async def process_pay_now(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PaymentStates.waiting_for_screenshot)
    prompt_text = (
        "📤 **𝖴𝗉𝗅𝗈𝖺𝖽 𝖯𝖺𝗒𝗆𝖾𝗇𝗍 𝖲𝖼𝗋𝖾𝖾𝗇𝗌𝗁𝗈𝗍**\n\n"
        "Please send the clear screenshot/photo of your payment receipt right here in this chat.\n"
        "⚡ *Will be confirmed by admin in approx 2 minutes after upload!*"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="« [ Back to Main Menu ]", callback_data="main_menu")]]
    )
    await safe_edit_message(callback.message, prompt_text, keyboard)
    await callback.answer()

@router.message(PaymentStates.waiting_for_screenshot, F.photo)
async def receive_screenshot(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    user = message.from_user
    username = f"@{user.username}" if user.username else "No Username"
    data = await state.get_data()
    
    order_id = data.get("current_order_id", generate_order_id())
    amount = data.get("current_amount", 499)
    duration = data.get("current_duration", 30)
    plan_name = data.get("current_plan_name", "VIP Collection Video")

    log_user_to_db(user)

    try:
        supabase.table("payments").insert({
            "user_id": user.id,
            "order_id": order_id,
            "username": username,
            "plan_name": plan_name,
            "amount": amount,
            "duration_days": duration,
            "photo_id": photo_id,
            "status": "pending",
        }).execute()
    except Exception as e:
        logging.error(f"Supabase payment entry error: {e}")

    confirm_text = (
        "⏳ **Payment Screenshot Received!**\n\n"
        "Please wait. Verification usually takes **under 2 minutes** by our admin team. "
        "Your access link will be confirmed and sent here shortly."
    )
    await message.answer(confirm_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="« [ Back to Main Menu ]", callback_data="main_menu")]]))
    await state.clear()

    admin_caption = (
        f"🚨 <b>NEW PAYMENT PENDING VERIFICATION</b> 🚨\n\n"
        f"👤 <b>Name:</b> {user.full_name}\n"
        f"🔗 <b>Username:</b> <code>{username}</code>\n"
        f"🆔 <b>Chat/User ID:</b> <code>{user.id}</code>\n"
        f"📦 <b>Plan Selected:</b> {plan_name}\n"
        f"💰 <b>Amount Transferred:</b> ₹{amount}\n"
        f"🏷️ <b>Order ID:</b> <code>{order_id}</code>\n\n"
        "👉 <i>Review the screenshot below and choose action:</i>"
    )
    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_{user.id}_{order_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{user.id}_{order_id}"),
        ]]
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
            logging.error(f"Failed to send highlighted notification to admin {admin_id}: {e}")

@router.message(PaymentStates.waiting_for_screenshot)
async def invalid_screenshot_type(message: Message):
    await message.answer("⚠️ Please send a valid **image/screenshot** of your payment receipt.")

@router.callback_query(F.data == "check_status")
async def process_check_status(callback: CallbackQuery):
    user_id = callback.from_user.id
    try:
        res = (
            supabase.table("payments")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if res.data:
            status = res.data[0]["status"].upper()
            order = res.data[0]["order_id"]
            plan = res.data[0]["plan_name"]
            status_msg = f"🔍 **Subscription Status**\n\nPlan: {plan}\nOrder ID: `{order}`\nStatus: **{status}**"
        else:
            status_msg = "🔍 **Subscription Status**\n\n❌ You do not have an active VIP subscription yet."
    except Exception:
        status_msg = "🔍 **Subscription Status**\n\n❌ Could not fetch data from database."

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 [ 🛍️ Buy / Upgrade Membership ]", callback_data="buy_membership")],
            [InlineKeyboardButton(text="« [ Back to Main Menu ]", callback_data="main_menu")],
        ]
    )
    await safe_edit_message(callback.message, status_msg, keyboard, photo_url=INTRO_IMAGE_URL)
    await callback.answer()

@router.callback_query(F.data == "demo_preview")
async def process_demo(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Tap Here to View Demo Channel", url=PUBLIC_DEMO_CHANNEL_LINK)],
            [InlineKeyboardButton(text="« [ Back to Main Menu ]", callback_data="main_menu")],
        ]
    )
    await safe_edit_message(
        callback.message,
        "🚀 **Premium Demo Channel**\n\nClick the button below to join/preview our public demo channel content:",
        keyboard,
        photo_url=DEFAULT_BANNER_URL
    )
    await callback.answer()

@router.callback_query(F.data.startswith("approve_"))
async def admin_approve_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized!", show_alert=True)
        return

    parts = callback.data.split("_")
    target_user_id = int(parts[1])
    order_id = parts[2]

    await state.set_state(PaymentStates.waiting_for_custom_link)
    await state.update_data(target_user_id=target_user_id, order_id=order_id)

    await callback.message.answer(
        f"🔗 **Send the fresh single-use invite link for Order `{order_id}` (User `{target_user_id}`):**"
    )
    await callback.answer()

@router.message(PaymentStates.waiting_for_custom_link, F.from_user.id.in_(ADMIN_IDS))
async def process_custom_link_input(message: Message, state: FSMContext):
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    order_id = data.get("order_id")
    invite_link = message.text.strip()

    try:
        supabase.table("payments").update({"status": "approved", "admin_reason": invite_link}).eq("order_id", order_id).execute()

        await message.bot.send_message(
            chat_id=target_user_id,
            text=(
                "🎉 **Payment Approved!**\n\nWelcome aboard. Here is your private channel access link:\n"
                f"{invite_link}\n\n"
                "⚠️ *Note: This invite link is single-use and will expire once joined!*"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
        await message.answer(f"✅ Approved and link sent to user `{target_user_id}`!")
    except Exception as e:
        await message.answer(f"❌ Failed to process approval: {e}")

    await state.clear()

@router.callback_query(F.data.startswith("reject_"))
async def admin_reject_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Unauthorized!", show_alert=True)
        return

    parts = callback.data.split("_")
    target_user_id = int(parts[1])
    order_id = parts[2]

    await state.set_state(PaymentStates.waiting_for_rejection_reason)
    await state.update_data(target_user_id=target_user_id, order_id=order_id)

    await callback.message.answer(f"❌ **Type the reason for rejecting Order `{order_id}`:**")
    await callback.answer()

@router.message(PaymentStates.waiting_for_rejection_reason, F.from_user.id.in_(ADMIN_IDS))
async def process_rejection_reason_input(message: Message, state: FSMContext):
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    order_id = data.get("order_id")
    reason = message.text.strip()

    try:
        supabase.table("payments").update({"status": "rejected", "admin_reason": reason}).eq("order_id", order_id).execute()

        await message.bot.send_message(
            chat_id=target_user_id,
            text=(
                "❌ **Payment Verification Rejected!**\n\n"
                f"📌 **Reason provided by admin:** {reason}\n\n"
                "Please re-check your transfer or contact support if you think this is a mistake."
            ),
            parse_mode=ParseMode.MARKDOWN,
        )
        await message.answer(f"✅ Rejection reason recorded and sent to user `{target_user_id}`.")
    except Exception as e:
        await message.answer(f"❌ Failed to process rejection: {e}")

    await state.clear()

@router.callback_query(F.data == "support")
async def process_support(callback: CallbackQuery):
    support_text = (
        "💬 **Customer Support**\n\n"
        "If you are facing any issues with payments or activation, please contact our support admin directly using the button below:"
    )
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
        except TelegramNetworkError as net_err:
            logging.warning(f"Network error: {net_err}. Reconnecting...")
            await asyncio.sleep(3)
        except Exception as err:
            logging.error(f"Polling exception: {err}. Restarting...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped safely.")