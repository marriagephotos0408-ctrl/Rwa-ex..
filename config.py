import os

API_ID = int(os.getenv("API_ID", "12345678"))
API_HASH = os.getenv("API_HASH", "your_api_hash_here")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")

BASE_URL = "https://rozgarapinew.teachx.in"

ENDPOINTS = {
    "send_otp": "/get/otp", # आवश्यकतानुसार सही एंडपॉइंट अपडेट करें
    "verify_otp": "/get/verify_otp",
    "exams_list": "/get/examslist",
    "sub_topics": "/get/youtubeclassstudyapi",
    "classes": "/get/youtubeclassbyexamsubtopconceptapiv2",
    "telegram": "/get/telegram"
}

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://rojgarwithankit.co.in",
    "Referer": "https://rojgarwithankit.co.in/"
}
