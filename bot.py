# bot.py
import os
import requests
from pyrogram import Client, filters
from pyrogram.types import Message

from keep_alive import keep_alive
from core.teachx_auth import send_otp, verify_otp_and_login
from core.teachx import get_my_courses
from core.utils import safe_filename

# Start Flask Web Server for 24/7 Uptime
keep_alive()

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

app = Client("teachx_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

USER_SESSIONS = {}

@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    await message.reply_text(
        "👋 **TeachX / ClassX Downloader Bot**\n\n"
        "Login करने के लिए अपना Phone Number भेजें:\n"
        "`/login 91XXXXXXXXXX`"
    )

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
        await message.reply_text("🎉 **Login Successful!**\n\nCourses देखने के लिए `/courses` लिखें।")
    except Exception as e:
        await message.reply_text(f"❌ Login Failed: {str(e)}")

@app.on_message(filters.command("courses"))
async def courses_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    session_data = USER_SESSIONS.get(user_id)
    
    if not session_data or "token" not in session_data:
        await message.reply_text("❌ पहले Login करें!")
        return
        
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {session_data['token']}"})
    
    try:
        courses = get_my_courses(s, session_data["auth_user_id"])
        if not courses:
            await message.reply_text("❌ कोई Courses नहीं मिले।")
            return
            
        text = "📚 **Your Courses:**\n\n"
        for idx, c in enumerate(courses, 1):
            c_name = c.get('course_name') or c.get('title') or 'Course'
            c_id = c.get('id') or c.get('course_id')
            text += f"{idx}. **{c_name}** (ID: `{c_id}`)\n"
        
        await message.reply_text(text)
    except Exception as e:
        await message.reply_text(f"❌ Error fetching courses: {str(e)}")

if __name__ == "__main__":
    app.run()
