# bot.py
from keep_alive import keep_alive

keep_alive()  # सर्वर स्टार्ट करेगा ताकि Render को Port मिल जाए

# बाकी का Telegram Bot Code..

import os
import json
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from core.teachx import (
    get_auth_session,
    get_subjects_by_exam,
    get_topics_by_subject,
    get_concept_classes,
    extract_full_exam_txt
)

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

app = Client("teachx_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Command to handle /get <exam_id>
@app.on_message(filters.command(["get", "exam"]))
async def get_exam_handler(client: Client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply_text("❌ Exam ID दर्ज करें!\n\nउदा: `/get 62`")
        return

    exam_id = args[1].strip()
    session = get_auth_session()
    
    msg = await message.reply_text("🔄 Subjects लोड किए जा रहे हैं...")
    subjects = get_subjects_by_exam(session, exam_id)

    if not subjects:
        await msg.edit_text("❌ इस Exam ID के लिए कोई Subjects नहीं मिले।")
        return

    buttons = []
    for sub in subjects[:10]: # Inline Limit
        s_id = str(sub.get("id") or sub.get("subjectid") or "0")
        s_name = sub.get("name") or sub.get("subject_name") or f"Subject {s_id}"
        buttons.append([InlineKeyboardButton(f"📘 {s_name}", callback_data=f"sub_{exam_id}_{s_id}")])

    buttons.append([InlineKeyboardButton("📥 Download Full TXT File", callback_data=f"dl_{exam_id}")])

    await msg.edit_text(
        f"🎯 **Exam ID:** `{exam_id}`\n\n"
        f"नीचे दिए गए **Subjects** में से चुनें या पूरी फ़ाइल डाउनलोड करें:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Callback Handler for Dynamic Buttons
@app.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    data = query.data
    session = get_auth_session()

    # 1. Subject Clicked -> Show Topics
    if data.startswith("sub_"):
        _, exam_id, sub_id = data.split("_")
        await query.answer("Topics फ़ैच हो रहे हैं...")

        topics = get_topics_by_subject(session, exam_id, sub_id)
        if not topics:
            await query.message.reply_text("❌ कोई Topics नहीं मिले।")
            return

        buttons = []
        for top in topics[:10]:
            t_id = str(top.get("id") or top.get("topicid") or "0")
            t_name = top.get("topic_name") or top.get("title") or f"Topic {t_id}"
            buttons.append([InlineKeyboardButton(f"📁 {t_name}", callback_data=f"cls_{exam_id}_{sub_id}_{t_id}")])

        await query.message.reply_text(
            f"📌 **Subject Selected!**\nअब कोई **Topic** चुनें:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # 2. Topic Clicked -> Show Classes & PDFs
    elif data.startswith("cls_"):
        _, exam_id, sub_id, top_id = data.split("_")
        await query.answer("Classes लोड की जा रही हैं...")

        classes = get_concept_classes(session, exam_id, sub_id, top_id)
        if not classes:
            await query.message.reply_text("❌ इस Topic में कोई Classes नहीं मिलीं।")
            return

        text = f"🎥 **Classes & PDFs ({len(classes)}):**\n\n"
        buttons = []

        for idx, cls in enumerate(classes[:8], 1):
            title = cls.get("title") or cls.get("topic_name") or f"Lecture {idx}"
            v_url = cls.get("url") or cls.get("youtube_url") or cls.get("link") or ""
            p_url = cls.get("pdf_url") or cls.get("pdf") or cls.get("attachment") or ""

            text += f"**{idx}. {title}**\n"
            
            row = []
            if v_url:
                row.append(InlineKeyboardButton(f"🎥 Class {idx}", url=v_url))
            if p_url:
                row.append(InlineKeyboardButton(f"📄 PDF {idx}", url=p_url))
            if row:
                buttons.append(row)

        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons) if buttons else None)

    # 3. Download Full Course TXT
    elif data.startswith("dl_"):
        exam_id = data.split("_")[1]
        await query.answer()
        status_msg = await query.message.reply_text("🔄 पूरे कोर्स की TXT फ़ाइल तैयार हो रही है, कृपया प्रतीक्षा करें...")

        try:
            stream, filename, v_cnt, p_cnt = extract_full_exam_txt(session, exam_id)
            caption = (
                f"✅ **Extract Successful!**\n\n"
                f"🆔 **Exam ID:** `{exam_id}`\n"
                f"🎥 **Total Videos:** {v_cnt}\n"
                f"📄 **Total PDFs:** {p_cnt}"
            )
            await query.message.reply_document(document=stream, file_name=filename, caption=caption)
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit_text(f"❌ Extraction Error: {str(e)}")

if __name__ == "__main__":
    app.run()
