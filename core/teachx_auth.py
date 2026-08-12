# core/teachx_auth.py
import requests

BASE_URL = "https://rozgarapinew.teachx.in"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://appx-play.akamai.net.in",
    "Referer": "https://appx-play.akamai.net.in/"
}

def check_user_exist(phone_or_email: str) -> dict:
    url = f"{BASE_URL}/get/check_user_exist"
    params = {"email_or_phone": phone_or_email}
    r = requests.get(url, params=params, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def send_otp(phone: str) -> bool:
    url = f"{BASE_URL}/get/sendotp"
    params = {"phone": phone}
    r = requests.get(url, params=params, headers=HEADERS)
    r.raise_for_status()
    data = r.json()
    return bool(data.get("status") or data.get("success") or True)

def verify_otp_and_login(phone: str, otp: str) -> tuple[str, str]:
    url = f"{BASE_URL}/post/verifyotp"
    payload = {"phone": phone, "otp": otp}
    
    r = requests.post(url, json=payload, headers=HEADERS)
    if r.status_code != 200:
        r = requests.get(f"{BASE_URL}/get/verifyotp", params=payload, headers=HEADERS)
        
    r.raise_for_status()
    data = r.json()
    
    user_data = data.get("data", data)
    token = user_data.get("token") or user_data.get("authorisation") or user_data.get("jwt") or ""
    user_id = str(user_data.get("userid") or user_data.get("id") or user_data.get("user_id") or "")
    
    return token, user_id
