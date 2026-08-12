# bot.py
import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from keep_alive import keep_alive
from core.teachx_auth import send_otp, verify_otp_and_login, login_with_password
from core.teachx import get_auth_session, get_my_courses

keep_alive()

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

app = Client("teachx_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

USER_SESSIONS = {}

# 1. स्टार्ट करने पर दिखने वाला लॉगिन चॉइस मेनू
def get_login_choice_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📲 OTP Login", callback_data="choice_otp"),
            InlineKeyboardButton("🔑 Password Login", callback_data="choice_pass")
        ]
    ])

# 2. लॉगिन होने के बाद दिखने वाला मेनू
def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 My Courses", callback_data="btn_courses")],
        [InlineKeyboardButton("🔑 Show My Token", callback_data="btn_show_token")],
        [InlineKeyboardButton("ℹ️ Help / Commands", callback_data="btn_help")]
    ])

# /start कमांड
@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    await message.reply_text(
        "👋 **TeachX / ClassX Downloader Bot**\n\n"
        "कृपया चुनें कि आप कैसे लॉगिन करना चाहते हैं:",
        reply_markup=get_login_choice_menu()
    )

# Inline Callback Buttons Handler
@app.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    session_data = USER_SESSIONS.get(user_id)
    
    # ------------------ लॉगिन चॉइस बटन्स ------------------
    if query.data == "choice_otp":
        await query.answer()
        await query.message.reply_text(
            "📲 **OTP Login Selected**\n\n"
            "लॉगिन करने के लिए अपना Phone Number भेजें:\n"
            "`/login 91XXXXXXXXXX`"
        )

    elif query.data == "choice_pass":
        await query.answer()
        await query.message.reply_text(
            "🔑 **Password Login Selected**\n\n"
            "लॉगिन करने के लिए अपना Number और Password भेजें:\n"
            "`/passlogin 91XXXXXXXXXX your_password`"
        )

    # ------------------ मुख्य मेनू बटन्स ------------------
    elif query.data == "btn_courses":
        if not session_data or "token" not in session_data:
            await query.answer("❌ कृपया पहले लॉगिन करें!", show_alert=True)
            return
            
        await query.answer("कोर्सेस लोड हो रहे हैं...")
        token = session_data["token"]
        auth_user_id = session_data.get("auth_user_id", "")
        
        session = get_auth_session(token)
        courses = get_my_courses(session, auth_user_id)
        
        if not courses:
            await query.message.reply_text("❌ कोई Courses नहीं मिले।", reply_markup=get_main_menu())
            return
            
        text = "📚 **Your Courses:**\n\n"
        for idx, c in enumerate(courses, 1):
            c_name = c.get('course_name') or c.get('title') or c.get('name') or 'Course'
            c_id = c.get('id') or c.get('course_id')
            text += f"{idx}. **{c_name}** (ID: `{c_id}`)\n"
            
        await query.message.reply_text(text, reply_markup=get_main_menu())

    elif query.data == "btn_show_token":
        if not session_data or "token" not in session_data:
            await query.answer("❌ लॉगिन डेटा नहीं मिला!", show_alert=True)
            return
            
        await query.answer()
        token = session_data["token"]
        auth_id = session_data.get("auth_user_id", "N/A")
        await query.message.reply_text(
            f"🆔 **User ID:** `{auth_id}`\n🔑 **Token:**\n`{token}`", 
            reply_markup=get_main_menu()
        )

    elif query.data == "btn_help":
        await query.answer()
        await query.message.reply_text(
            "📌 **Commands Guide:**\n\n"
            "• `/start` - लॉगिन ऑप्शन देखने के लिए\n"
            "• `/login <phone>` - OTP भेजने के लिए\n"
            "• `/verify <otp>` - OTP वेरीफाई करने के लिए\n"
            "• `/passlogin <phone> <password>` - सीधे पासवर्ड से लॉगिन",
            reply_markup=get_main_menu()
        )

# OTP Login command
@app.on_message(filters.command("login"))
async def login_cmd(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("❌ कृपया Phone Number दर्ज करें!\nExample: `/login 9876543210`")
        return
        
    phone = args[1].strip()
    USER_SESSIONS[message.from_user.id] = {"phone": phone}
    
    await message.reply_text("📲 OTP भेजा जा रहा है...")
    try:
        if send_otp(phone):
            await message.reply_text("✅ OTP भेज दिया गया है! Verify करने के लिए लिखें:\n`/verify 123456`")
        else:
            await message.reply_text("❌ OTP भेजने में विफल!")
    except Exception as e:
        await message.reply_text(f"❌ OTP Error: {str(e)}")

# Verify OTP command
@app.on_message(filters.command("verify"))
async def verify_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in USER_SESSIONS or "phone" not in USER_SESSIONS[user_id]:
        await message.reply_text("❌ पहले `/login <number>` का प्रयोग करें।")
        return
        
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("❌ OTP दर्ज करें!\nExample: `/verify 123456`")
        return
        
    otp = args[1].strip()
    phone = USER_SESSIONS[user_id]["phone"]
    
    try:
        token, auth_user_id = verify_otp_and_login(phone, otp)
        USER_SESSIONS[user_id]["token"] = token
        USER_SESSIONS[user_id]["auth_user_id"] = auth_user_id
        
        msg = f"🎉 **Login Successful!**\n\n"
        msg += f"🆔 **User ID:** `{auth_user_id}`\n"
        msg += f"🔑 **Auth Token:**\n`{token}`"
        
        await message.reply_text(msg, reply_markup=get_main_menu())
    except Exception as e:
        await message.reply_text(f"❌ Login Failed: {str(e)}")

# Password Login command
@app.on_message(filters.command("passlogin"))
async def passlogin_cmd(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 3:
        await message.reply_text("❌ नंबर और पासवर्ड दर्ज करें!\nExample: `/passlogin 9876543210 mypassword`")
        return
        
    phone = args[1].strip()
    password = args[2].strip()
    
    await message.reply_text("🔄 लॉगिन किया जा रहा है...")
    try:
        token, auth_user_id = login_with_password(phone, password)
        user_id = message.from_user.id
        USER_SESSIONS[user_id] = {"token": token, "auth_user_id": auth_user_id, "phone": phone}
        
        msg = f"🎉 **Login Successful!**\n\n"
        msg += f"🆔 **User ID:** `{auth_user_id}`\n"
        msg += f"🔑 **Auth Token:**\n`{token}`"
        
        await message.reply_text(msg, reply_markup=get_main_menu())
    except Exception as e:
        await message.reply_text(f"❌ Login Failed: {str(e)}")

if __name__ == "__main__":
    app.run()
