# bot.py
import os
import logging
import html
import pyrogram
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from keep_alive import keep_alive
from core.teachx import (
    get_auth_session,
    fetch_dynamic_api,
    auto_extract_keys,
    extract_recursive_txt
)

keep_alive()

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

app = Client("teachx_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# User Sessions Storage (User ID -> Token)
USER_SESSIONS = {}

@app.on_message(filters.command("ping"))
async def ping_handler(client: Client, message: Message):
    await message.reply_text("🏓 **Pong! Bot active hai aur properly respond kar raha hai.**")

@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    token_status = "✅ Saved Token Available" if user_id in USER_SESSIONS else "❌ No Token Set (Public Mode)"

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 Set/Update Auth Token", callback_data="btn_login_token")],
        [InlineKeyboardButton("📚 Free / Purchased Courses", callback_data="btn_free_courses")],
        [InlineKeyboardButton("ℹ️ Help & Commands", callback_data="btn_help")]
    ])
    
    await message.reply_text(
        f"👋 **TeachX / ClassX Extractor Bot**\n\n"
        f"🔑 **Token Status:** `{token_status}`\n\n"
        f"**Commands:**\n"
        f"• `/token <your_auth_token>` - Auth token save karne ke liye\n"
        f"• `/get <exam_id>` - Subject/Topics aur PDF auto-extract karne ke liye\n"
        f"• `/ping` - Bot status check karne ke liye",
        reply_markup=btn
    )

@app.on_message(filters.command("token"))
async def save_token_cmd(client: Client, message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply_text("❌ Kripya Token bhejain!\n\nUsage: `/token Bearer eyJhbG...`")
        return

    token = args[1].strip()
    USER_SESSIONS[message.from_user.id] = token
    await message.reply_text("✅ **Token Successfully Saved!** Ab aap private / paid courses bhi fetch kar sakte hain.")

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

    raw_subjects = fetch_dynamic_api(session, "/get/youtubeclasstopicapi", {"examid": exam_id, "subjectid": "0", "start": "-1"})

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

    if data == "btn_login_token":
        await query.answer()
        await query.message.reply_text(
            "🔑 **Token Set Karne Ka Tarika:**\n\n"
            "Chhat me likhein: `/token <Apka_Token>`\n\n"
            "Example:\n`/token Bearer eyJhbGciOiJIUzI1Ni...`"
        )

    elif data == "btn_free_courses":
        await query.answer("Fetching Courses...")
        raw_exams = fetch_dynamic_api(session, "/get/examslist")
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
            "📌 **Command Guide:**\n\n"
            "• `/token <Token>` - User Token save karne ke liye\n"
            "• `/get 62` - Subjects, Topics aur Class Links auto-fetch karne ke liye\n"
            "• `/ping` - Server Status check karne ke liye"
        )

    elif data.startswith("dyn_sub_"):
        _, _, exam_id, sub_id = data.split("_")
        await query.answer("Topics load ho rahe hain...")

        raw_topics = fetch_dynamic_api(session, "/get/youtubeclasstopicapi", {"examid": exam_id, "subjectid": sub_id, "start": "-1"})

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

        raw_classes = fetch_dynamic_api(session, "/get/youtubeclassbyexamsubtopconceptapiv2", {
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
        status = await query.message.reply_text("⏳ Server ka Structure scan ho raha hai, kripya prateeksha karein...")

        all_data = fetch_dynamic_api(session, "/get/youtubeclasstopicapi", {"examid": exam_id, "subjectid": "0", "start": "-1"})
        
        stream, filename, v_cnt, p_cnt = extract_recursive_txt(session, all_data, exam_id)
        
        caption = f"✅ **Extraction Complete!**\n\n🆔 Exam ID: `{exam_id}`\n🎥 Videos: {v_cnt}\n📄 PDFs: {p_cnt}"
        await query.message.reply_document(document=stream, file_name=filename, caption=caption)
        await status.delete()

if __name__ == "__main__":
    logging.info("Starting Pyrogram Bot...")
    app.run()
