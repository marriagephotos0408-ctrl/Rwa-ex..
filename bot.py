# bot.py
import os
import json
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from keep_alive import keep_alive
from core.teachx_auth import send_otp, verify_otp_and_login
from core.teachx import (
    get_auth_session, 
    get_my_courses, 
    get_user_profile,
    get_free_exams,
    get_youtube_class_topics,
    get_telegram_course_info
)

keep_alive()

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

app = Client("teachx_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

USER_SESSIONS = {}

def get_login_choice_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📲 OTP Login", callback_data="choice_otp"),
            InlineKeyboardButton("🎫 Token Login", callback_data="choice_token")
        ],
        [InlineKeyboardButton("🆓 Free Courses List", callback_data="btn_free_courses")]
    ])

def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Paid My Courses", callback_data="btn_courses")],
        [InlineKeyboardButton("🆓 Free Courses / Exams", callback_data="btn_free_courses")],
        [InlineKeyboardButton("👤 Profile Info", callback_data="btn_show_token")],
        [InlineKeyboardButton("ℹ️ Help / Commands", callback_data="btn_help")]
    ])

@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    await message.reply_text(
        "👋 **TeachX / ClassX Multi-Feature Bot**\n\n"
        "कृपया नीचे दिए गए विकल्पों में से चुनें:",
        reply_markup=get_login_choice_menu()
    )

@app.on_callback_query()
async def callback_handler(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    session_data = USER_SESSIONS.get(user_id, {})
    token = session_data.get("token", "")
    
    if query.data == "choice_otp":
        await query.answer()
        await query.message.reply_text(
            "📲 **OTP Login Selected**\n\n"
            "लॉगिन करने के लिए अपना Phone Number भेजें:\n"
            "`/login 91XXXXXXXXXX`"
        )

    elif query.data == "choice_token":
        await query.answer()
        await query.message.reply_text(
            "🎫 **Token Login Selected**\n\n"
            "लॉगिन करने के लिए अपना Auth Token भेजें:\n"
            "`/tokenlogin YOUR_AUTH_TOKEN`"
        )

    elif query.data == "btn_courses":
        if not token:
            await query.answer("❌ कृपया पहले OTP या Token से लॉगिन करें!", show_alert=True)
            return
            
        await query.answer("कोर्सेस लोड हो रहे हैं...")
        auth_user_id = session_data.get("auth_user_id", "")
        
        session = get_auth_session(token)
        courses = get_my_courses(session, auth_user_id)
        
        if not courses:
            await query.message.reply_text("❌ कोई Paid Courses नहीं मिले।", reply_markup=get_main_menu())
            return
            
        text = f"📚 **Your Paid Courses ({len(courses)}):**\n\n"
        for idx, c in enumerate(courses, 1):
            c_name = c.get('course_name') or c.get('title') or c.get('name') or 'Course'
            c_id = c.get('id') or c.get('course_id')
            text += f"{idx}. **{c_name}**\n🆔 Course ID: `{c_id}`\n\n"
            
        await query.message.reply_text(text, reply_markup=get_main_menu())

    elif query.data == "btn_free_courses":
        await query.answer("फ्री एग्जाम्स लिस्ट लोड हो रही है...")
        session = get_auth_session(token)
        free_exams = get_free_exams(session)
        
        if not free_exams:
            await query.message.reply_text("❌ कोई Free Courses डेटा नहीं मिला।", reply_markup=get_main_menu())
            return

        text = f"🆓 **Free Exams / Courses List ({len(free_exams)}):**\n\n"
        for idx, exam in enumerate(free_exams[:15], 1):
            exam_name = exam.get('exam_name') or exam.get('title') or exam.get('name') or 'Exam'
            exam_id = exam.get('id') or exam.get('examid') or exam.get('exam_id')
            text += f"{idx}. **{exam_name}**\n🆔 Exam ID: `{exam_id}`\n\n"

        text += "💡 **टॉपिक्स देखने के लिए लिखे:**\n`/freetopics 62 1187`"
        await query.message.reply_text(text, reply_markup=get_main_menu())

    elif query.data == "btn_show_token":
        if not token:
            await query.answer("❌ लॉगिन डेटा नहीं मिला!", show_alert=True)
            return
            
        await query.answer()
        auth_id = session_data.get("auth_user_id", "N/A")
        name = session_data.get("name", "N/A")
        email = session_data.get("email", "N/A")
        
        msg = f"👤 **User Details:**\n"
        msg += f"• **Name:** {name}\n"
        msg += f"• **Contact/Email:** {email}\n"
        msg += f"• **User ID:** `{auth_id}`\n\n"
        msg += f"🔑 **Auth Token:**\n`{token}`"
        
        await query.message.reply_text(msg, reply_markup=get_main_menu())

    elif query.data == "btn_help":
        await query.answer()
        await query.message.reply_text(
            "📌 **Commands Guide:**\n\n"
            "• `/start` - स्टार्ट मेन्यू देखने के लिए\n"
            "• `/login <phone>` - OTP भेजने के लिए\n"
            "• `/verify <otp>` - OTP वेरीफाई करने के लिए\n"
            "• `/tokenlogin <token>` - टोकन से लॉगिन करने के लिए\n"
            "• `/freecourses` - फ्री एग्जाम्स देखने के लिए\n"
            "• `/freetopics <exam_id> [subject_id]` - फ्री वीडियो देखने के लिए\n"
            "• `/telegram <course_id>` - टेलीग्राम ग्रुप देखने के लिए",
            reply_markup=get_main_menu()
        )

# --- OTP Commands (Re-added) ---
@app.on_message(filters.command("login"))
async def login_cmd(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("❌ फोन नंबर दर्ज करें!\nExample: `/login 9876543210`")
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
        await message.reply_text(f"❌ Error: {str(e)}")

@app.on_message(filters.command("verify"))
async def verify_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in USER_SESSIONS or "phone" not in USER_SESSIONS[user_id]:
        await message.reply_text("❌ पहले `/login <number>` करें।")
        return
        
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("❌ OTP दर्ज करें!\nExample: `/verify 123456`")
        return
        
    otp = args[1].strip()
    phone = USER_SESSIONS[user_id]["phone"]
    
    try:
        token, auth_user_id = verify_otp_and_login(phone, otp)
        session = get_auth_session(token)
        profile = get_user_profile(session, token, auth_user_id)
        
        USER_SESSIONS[user_id] = {
            "token": token, 
            "auth_user_id": auth_user_id or profile["id"],
            "name": profile["name"],
            "email": profile["email"]
        }
        
        msg = f"🎉 **OTP Login Successful!**\n\n"
        msg += f"👤 **Name:** {profile['name']}\n"
        msg += f"🆔 **User ID:** `{auth_user_id or profile['id']}`\n\n"
        msg += f"🔑 **Auth Token:**\n`{token}`"
        
        await message.reply_text(msg, reply_markup=get_main_menu())
    except Exception as e:
        await message.reply_text(f"❌ Verify Failed: {str(e)}")

# --- Token and Free Commands ---
@app.on_message(filters.command("tokenlogin"))
async def tokenlogin_cmd(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("❌ अपना Token दर्ज करें!\nExample:\n`/tokenlogin YOUR_TOKEN`")
        return
        
    token = args[1].strip()
    
    await message.reply_text("🔄 Token जांच रहे हैं...")
    try:
        session = get_auth_session(token)
        profile = get_user_profile(session, token)
        final_user_id = profile["id"]
        
        courses = get_my_courses(session, final_user_id)
        
        user_id = message.from_user.id
        USER_SESSIONS[user_id] = {
            "token": token, 
            "auth_user_id": final_user_id,
            "name": profile["name"],
            "email": profile["email"]
        }
        
        msg = f"🎉 **Login Successful!**\n\n"
        msg += f"👤 **Name:** {profile['name']}\n"
        msg += f"📧 **Contact:** {profile['email']}\n"
        msg += f"🆔 **User ID:** `{final_user_id}`\n\n"
        msg += f"📚 **Paid Courses:** {len(courses)}"
        
        await message.reply_text(msg, reply_markup=get_main_menu())
    except Exception as e:
        await message.reply_text(f"❌ Token Error: {str(e)}")

@app.on_message(filters.command("freetopics"))
async def freetopics_cmd(client: Client, message: Message):
    args = message.text.split()
    exam_id = args[1].strip() if len(args) > 1 else "62"
    subject_id = args[2].strip() if len(args) > 2 else "1187"

    await message.reply_text("🔄 टॉपिक्स फ़ैच हो रहे हैं...")
    session = get_auth_session()
    topics = get_youtube_class_topics(session, exam_id, subject_id)

    if not topics:
        await message.reply_text("❌ कोई फ्री टॉपिक्स नहीं मिले।")
        return

    text = f"🎥 **Free Topics ({len(topics)}):**\n\n"
    for idx, t in enumerate(topics[:10], 1):
        t_title = t.get('topic_name') or t.get('title') or t.get('name') or 'Topic'
        t_url = t.get('url') or t.get('youtube_url') or t.get('link') or 'N/A'
        text += f"{idx}. **{t_title}**\n🔗 `{t_url}`\n\n"

    await message.reply_text(text)

@app.on_message(filters.command("telegram"))
async def telegram_cmd(client: Client, message: Message):
    args = message.text.split()
    course_id = args[1].strip() if len(args) > 1 else "62"
    
    session = get_auth_session()
    data = get_telegram_course_info(session, course_id)
    
    await message.reply_text(f"📢 **Telegram Data:**\n```json\n{json.dumps(data, indent=2)}\n```")

if __name__ == "__main__":
    app.run()
