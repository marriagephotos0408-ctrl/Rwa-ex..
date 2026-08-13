# bot.py
import logging
import html
import pyrogram
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import API_ID, API_HASH, BOT_TOKEN
from keep_alive import keep_alive
from core.teachx import (
    get_auth_session,
    send_otp_api,
    verify_otp_api,
    fetch_dynamic_api,
    auto_extract_keys,
    extract_recursive_txt
)

keep_alive()

app = Client("teachx_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# In-memory session store
USER_SESSIONS = {}
LOGIN_STATE = {}

@app.on_message(filters.command("ping"))
async def ping_handler(client: Client, message: Message):
    await message.reply_text("🏓 **Pong! Bot active hai aur properly respond kar raha hai.**")

@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    token_status = "✅ Login Active" if user_id in USER_SESSIONS else "❌ Not Logged In"

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Login with OTP", callback_data="btn_login_otp"), InlineKeyboardButton("🔑 Set Token", callback_data="btn_login_token")],
        [InlineKeyboardButton("📚 Courses / Batches", callback_data="btn_free_courses")],
        [InlineKeyboardButton("ℹ️ Help & Guide", callback_data="btn_help")]
    ])
    
    await message.reply_text(
        f"👋 **TeachX / ClassX Extractor Bot**\n\n"
        f"Status: `{token_status}`\n\n"
        f"**Commands:**\n"
        f"• `/login <Mobile_Number>` - OTP ke dwara login karne ke liye\n"
        f"• `/token <Auth_Token>` - Manually Auth Token set karne ke liye\n"
        f"• `/get <exam_id>` - Subject/Topics extract karne ke liye\n"
        f"• `/ping` - Bot active status check karne ke liye",
        reply_markup=btn
    )

@app.on_message(filters.command("login"))
async def login_cmd(client: Client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text("❌ Kripya Mobile Number likhein!\n\nUsage: `/login 9876543210`")
        return

    phone = args[1].strip()
    msg = await message.reply_text("⏳ Sending OTP...")
    
    res = send_otp_api(phone)
    if res and res.get("status") == "true":
        LOGIN_STATE[message.from_user.id] = {"phone": phone}
        await msg.edit_text(f"✅ OTP successfully sent to `{phone}`!\n\nAb likhein: `/otp <YOUR_OTP>`")
    else:
        await msg.edit_text("❌ OTP bhejne me viphaltha huyi. Mobile number jaanchen.")

@app.on_message(filters.command("otp"))
async def otp_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in LOGIN_STATE:
        await message.reply_text("❌ Pehle `/login <Mobile_Number>` se OTP bhejain.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text("❌ Kripya OTP code likhein!\n\nUsage: `/otp 1234`")
        return

    otp = args[1].strip()
    phone = LOGIN_STATE[user_id]["phone"]
    
    msg = await message.reply_text("⏳ Verifying OTP...")
    res = verify_otp_api(phone, otp)

    if res and res.get("status") == "true":
        token = res.get("token") or res.get("data", {}).get("token", "")
        USER_SESSIONS[user_id] = token
        del LOGIN_STATE[user_id]
        await msg.edit_text("🎉 **Login Successful!** Token saved. Ab aap apne paid courses bhi extract kar sakte hain.")
    else:
        await msg.edit_text("❌ OTP Galat hai ya expire ho chuka hai. Dobara koshish karein.")

@app.on_message(filters.command("token"))
async def save_token_cmd(client: Client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text("❌ Kripya Token bhejain!\n\nUsage: `/token Bearer eyJhbG...`")
        return

    token = args[1].strip()
    USER_SESSIONS[message.from_user.id] = token
    await message.reply_text("✅ **Token Saved Successfully!**")

@app.on_message(filters.command(["get", "exam"]))
async def dynamic_get_handler(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("❌ Exam ID darj karein!\nUdaharana: `/get 62`")
        return

    exam_id = args[1].strip()
    user_id = message.from_user.id
    token = USER_SESSIONS.get(user_id, "")
    session = get_auth_session(token)

    msg = await message.reply_text("🔄 Server se Data Fetch kiya ja raha hai...")

    raw_subjects = fetch_dynamic_api(session, "sub_topics", {"examid": exam_id, "subjectid": "0", "start": "-1"})

    if not raw_subjects:
        await msg.edit_text("❌ Is Exam ID ke liye koi data nahi mila.")
        return

    buttons = []
    for item in raw_subjects[:12]:
        parsed = auto_extract_keys(item)
        s_id = parsed["id"] or "0"
        s_title = parsed["title"]
        buttons.append([InlineKeyboardButton(f"📁 {s_title[:30]}", callback_data=f"dyn_sub_{exam_id}_{s_id}")])

    buttons.append([InlineKeyboardButton("📥 Download Full TXT File", callback_data=f"dyn_dl_{exam_id}")])

    await msg.edit_text(
        f"🎯 **Exam ID:** `{exam_id}`\n\nNiche diye gaye Subjects me se chunen ya TXT download karein:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_callback_query()
async def dynamic_cb_handler(client: Client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    token = USER_SESSIONS.get(user_id, "")
    session = get_auth_session(token)

    if data == "btn_login_otp":
        await query.answer()
        await query.message.reply_text("📱 **OTP Login:**\n\nLikhien: `/login <YOUR_MOBILE>`")

    elif data == "btn_login_token":
        await query.answer()
        await query.message.reply_text("🔑 **Manual Token:**\n\nLikhein: `/token <YOUR_TOKEN>`")

    elif data == "btn_free_courses":
        await query.answer("Fetching Courses...")
        raw_exams = fetch_dynamic_api(session, "exams_list")
        if not raw_exams:
            await query.message.reply_text("❌ Data load nahi ho saka.")
            return

        text = f"<b>🆓 Courses / Exams List ({len(raw_exams[:15])}):</b>\n\n"
        for idx, item in enumerate(raw_exams[:15], 1):
            parsed = auto_extract_keys(item)
            clean_title = html.escape(parsed['title'])
            text += f"{idx}. <b>{clean_title}</b>\n🆔 Exam ID: <code>{parsed['id']}</code>\n\n"

        text += "💡 <b>Data dekhne ke liye likhein:</b> <code>/get &lt;exam_id&gt;</code>"
        
        await query.message.reply_text(text, parse_mode=enums.ParseMode.HTML)

    elif data == "btn_help":
        await query.answer()
        await query.message.reply_text(
            "📌 **Help Guide:**\n\n"
            "1. `/login <Mobile>` ➔ Send OTP for Paid Batches\n"
            "2. `/otp <Code>` ➔ Complete Login\n"
            "3. `/get <exam_id>` ➔ Explore Course Structure & TXT File"
        )

    elif data.startswith("dyn_sub_"):
        _, _, exam_id, sub_id = data.split("_")
        await query.answer("Topics load ho rahe hain...")

        raw_topics = fetch_dynamic_api(session, "sub_topics", {"examid": exam_id, "subjectid": sub_id, "start": "-1"})

        buttons = []
        for item in raw_topics[:12]:
            parsed = auto_extract_keys(item)
            t_id = parsed["id"] or "0"
            t_title = parsed["title"]
            buttons.append([InlineKeyboardButton(f"🔹 {t_title[:30]}", callback_data=f"dyn_cls_{exam_id}_{sub_id}_{t_id}")])

        await query.message.reply_text("📌 **Topics List:**", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("dyn_cls_"):
        _, _, exam_id, sub_id, top_id = data.split("_")
        await query.answer("Classes Extract ho rahi hain...")

        raw_classes = fetch_dynamic_api(session, "classes", {
            "examid": exam_id, "subjectid": sub_id, "topicid": top_id, "start": "0"
        })

        if not raw_classes:
            await query.message.reply_text("❌ Is Topic me koi Content nahi mila.")
            return

        text = f"🎥 <b>Classes & PDFs ({len(raw_classes)}):</b>\n\n"
        buttons = []

        for idx, item in enumerate(raw_classes[:8], 1):
            parsed = auto_extract_keys(item)
            clean_title = html.escape(parsed['title'])
            text += f"<b>{idx}. {clean_title}</b>\n"
            
            row = []
            if parsed['video']:
                row.append(InlineKeyboardButton(f"🎥 Video {idx}", url=parsed['video']))
            if parsed['pdf']:
                row.append(InlineKeyboardButton(f"📄 PDF {idx}", url=parsed['pdf']))
            if row:
                buttons.append(row)

        await query.message.reply_text(
            text, 
            reply_markup=InlineKeyboardMarkup(buttons) if buttons else None,
            parse_mode=enums.ParseMode.HTML
        )

    elif data.startswith("dyn_dl_"):
        exam_id = data.split("_")[2]
        await query.answer()
        status = await query.message.reply_text("⏳ Server Structure scan ho raha hai, prateeksha karein...")

        all_data = fetch_dynamic_api(session, "sub_topics", {"examid": exam_id, "subjectid": "0", "start": "-1"})
        
        stream, filename, v_cnt, p_cnt = extract_recursive_txt(session, all_data, exam_id)
        
        caption = f"✅ **Extraction Complete!**\n\n🆔 Exam ID: `{exam_id}`\n🎥 Videos: {v_cnt}\n📄 PDFs: {p_cnt}"
        await query.message.reply_document(document=stream, file_name=filename, caption=caption)
        await status.delete()

if __name__ == "__main__":
    logging.info("Starting Pyrogram Bot...")
    app.run()
