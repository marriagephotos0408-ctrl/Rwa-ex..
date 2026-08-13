# config.py
import os

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

BASE_URL = "https://rozgarapinew.teachx.in"

ENDPOINTS = {
    "send_otp": "/get/sendotp",
    "verify_otp": "/get/otpverify",
    "exams_list": "/get/examslist",
    "liked_items": "/get/get_user_liked_items",
    "sub_topics": "/get/youtubeclasstopicapi",
    "classes": "/get/youtubeclassbyexamsubtopconceptapiv2"
}

DEFAULT_HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; M2010J19CI Build/RP1A.200720.011)",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://rojgarwithankit.co.in",
    "Referer": "https://rojgarwithankit.co.in/",
    "Client-Service": "Appx",
    "Auth-Key": "appxapi",
    "app-token": "appxapi",
    "Host": "rozgarapinew.teachx.in"
}
