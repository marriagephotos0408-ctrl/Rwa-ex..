# bot.py
import os
import logging
from pyrogram import Client, filters
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

USER_SESSIONS = {}

@app.on_message(filters.command("ping"))
async def ping_handler(client: Client, message: Message):
    await message.reply_text("🏓 **Pong! Bot active hai aur properly respond kar raha hai.**")

@app.on_message(filters.command("start"))
async def start_cmd(client: Client, message: Message):
    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 Free Courses / Exams", callback_data="btn_free_courses")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="btn_help")]
    ])
    await message.reply_text(
        "👋 **TeachX / ClassX Extractor Bot**\n\n"
        "कमांड्स:\n"
        "• `/get <exam_id>` - किसी भी एग्जाम के Subjects & Topics निकालने के लिए\n"
        "• `/ping` - बोट का स्टेटस चेक करने के लिए",
        reply_markup=btn
    )

@app.on_message(filters.command(["get", "exam"]))
async def dynamic_get_handler(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("❌ Exam ID दर्ज करें!\nउदा: `/get 62`")
        return

    exam_id = args[1].strip()
    session = get_auth_session()

    msg = await message.reply_text("🔄 Server से Data Fetch किया जा रहा है...")

    raw_subjects = fetch_dynamic_api(session, "/get/youtubeclasstopicapi", {"examid": exam_id, "subjectid": "0", "start": "-1"})

    if not raw_subjects:
        await msg.edit_text("❌ इस Exam ID के लिए कोई डेटा नहीं मिला।")
        return

    buttons = []
    for item in raw_subjects[:12]:
        parsed = auto_extract_keys(item)
        s_id = parsed["id"] or "0"
        s_title = parsed["title"]
        buttons.append([InlineKeyboardButton(f"📁 {s_title}", callback_data=f"dyn_sub_{exam_id}_{s_id}")])

    buttons.append([InlineKeyboardButton("📥 Download Full TXT File", callback_data=f"dyn_dl_{exam_id}")])

    await msg.edit_text(
        f"🎯 **Exam ID:** `{exam_id}`\n\nनीचे दिए गए Subjects में से चुनें या TXT डाउनलोड करें:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_callback_query()
async def dynamic_cb_handler(client: Client, query: CallbackQuery):
    data = query.data
    session = get_auth_session()

    if data == "btn_free_courses":
        await query.answer("Fetching...")
        raw_exams = fetch_dynamic_api(session, "/get/examslist")
        if not raw_exams:
            await query.message.reply_text("❌ डेटा लोड नहीं हो सका।")
            return

        text = f"🆓 **Free Exams List ({len(raw_exams[:15])}):**\n\n"
        for idx, item in enumerate(raw_exams[:15], 1):
            parsed = auto_extract_keys(item)
            text += f"{idx}. **{parsed['title']}**\n🆔 Exam ID: `{parsed['id']}`\n\n"

        text += "💡 **डेटा देखने के लिए लिखें:** `/get <exam_id>`"
        await query.message.reply_text(text)

    elif data == "btn_help":
        await query.answer()
        await query.message.reply_text(
            "📌 **कमांड गाइड:**\n\n"
            "• `/get 62` - Subjects, Topics और Class Links देखने के लिए\n"
            "• `/ping` - सर्वर स्टेटस चेक करने के लिए"
        )

    elif data.startswith("dyn_sub_"):
        _, _, exam_id, sub_id = data.split("_")
        await query.answer("Topics लोड हो रहे हैं...")

        raw_topics = fetch_dynamic_api(session, "/get/youtubeclasstopicapi", {"examid": exam_id, "subjectid": sub_id, "start": "-1"})

        buttons = []
        for item in raw_topics[:12]:
            parsed = auto_extract_keys(item)
            t_id = parsed["id"] or "0"
            t_title = parsed["title"]
            buttons.append([InlineKeyboardButton(f"🔹 {t_title}", callback_data=f"dyn_cls_{exam_id}_{sub_id}_{t_id}")])

        await query.message.reply_text("📌 **Topics List:**", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("dyn_cls_"):
        _, _, exam_id, sub_id, top_id = data.split("_")
        await query.answer("Classes Extract हो रही हैं...")

        raw_classes = fetch_dynamic_api(session, "/get/youtubeclassbyexamsubtopconceptapiv2", {
            "examid": exam_id, "subjectid": sub_id, "topicid": top_id, "start": "0"
        })

        if not raw_classes:
            await query.message.reply_text("❌ इस Topic में कोई Classes नहीं मिलीं।")
            return

        text = f"🎥 **Classes & PDFs ({len(raw_classes)}):**\n\n"
        buttons = []

        for idx, item in enumerate(raw_classes[:8], 1):
            parsed = auto_extract_keys(item)
            text += f"**{idx}. {parsed['title']}**\n"
            
            row = []
            if parsed['video']:
                row.append(InlineKeyboardButton(f"🎥 Video {idx}", url=parsed['video']))
            if parsed['pdf']:
                row.append(InlineKeyboardButton(f"📄 PDF {idx}", url=parsed['pdf']))
            if row:
                buttons.append(row)

        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons) if buttons else None)

    elif data.startswith("dyn_dl_"):
        exam_id = data.split("_")[2]
        await query.answer()
        status = await query.message.reply_text("⏳ सर्वर का Structure स्कैन हो रहा है, कृपया प्रतीक्षा करें...")

        all_data = fetch_dynamic_api(session, "/get/youtubeclasstopicapi", {"examid": exam_id, "subjectid": "0", "start": "-1"})
        
        stream, filename, v_cnt, p_cnt = extract_recursive_txt(session, all_data, exam_id)
        
        caption = f"✅ **Extraction Complete!**\n\n🆔 Exam ID: `{exam_id}`\n🎥 Videos: {v_cnt}\n📄 PDFs: {p_cnt}"
        await query.message.reply_document(document=stream, file_name=filename, caption=caption)
        await status.delete()

if __name__ == "__main__":
    logging.info("Starting Pyrogram Bot...")
    app.run()
