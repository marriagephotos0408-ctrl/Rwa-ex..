# core/teachx_auth.py
import json
import logging
from curl_cffi import requests as cffi_requests

BASE_URL = "https://rozgarapinew.teachx.in"

APP_HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; M2010J19CI Build/RP1A.200720.011)",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate",
    "Client-Service": "Appx",
    "Auth-Key": "appxapi",
    "app-token": "appxapi",
    "Content-Type": "application/json; charset=UTF-8",
    "Host": "rozgarapinew.teachx.in"
}

def get_tls_session():
    return cffi_requests.Session(impersonate="chrome110")

def send_otp(phone: str) -> bool:
    clean_phone = phone[-10:]
    session = get_tls_session()
    
    try:
        response = session.post(f"{BASE_URL}/post/sendotp", json={"phone": clean_phone}, headers=APP_HEADERS, timeout=15)
        if response.status_code == 200:
            return True
    except Exception as e:
        logging.error(f"POST sendotp failed: {e}")

    response = session.get(f"{BASE_URL}/get/sendotp", params={"phone": clean_phone}, headers=APP_HEADERS, timeout=15)
    response.raise_for_status()
    
    try:
        data = response.json()
    except Exception:
        data = {}
        
    return bool(data.get("status") or data.get("success") or True)

def verify_otp_and_login(phone: str, otp: str) -> tuple[str, str]:
    clean_phone = phone[-10:]
    session = get_tls_session()
    
    url = f"{BASE_URL}/get/otpverify"
    params = {
        "useremail": clean_phone,
        "otp": str(otp),
        "device_id": "WebBrowser1786518083748609u6euajjg",
        "mydeviceid": "",
        "mydeviceid2": ""
    }
    
    response = session.get(url, params=params, headers=APP_HEADERS, timeout=15)
    response.raise_for_status()
    
    try:
        data = response.json()
    except Exception:
        data = json.loads(response.text)
        
    if isinstance(data, str):
        data = json.loads(data)

    # Exact extraction from 'user' object
    user_obj = data.get("user", {}) if isinstance(data, dict) else {}
    data_obj = data.get("data", {}) if isinstance(data, dict) and isinstance(data.get("data"), dict) else {}
    
    token = ""
    user_id = ""

    if isinstance(user_obj, dict):
        token = user_obj.get("token") or user_obj.get("authorisation") or user_obj.get("jwt") or ""
        user_id = str(user_obj.get("userid") or user_obj.get("id") or "")

    if not token and isinstance(data_obj, dict):
        token = data_obj.get("token") or data_obj.get("authorisation") or ""
        user_id = user_id or str(data_obj.get("userid") or data_obj.get("id") or "")

    if not token and isinstance(data, dict):
        token = data.get("token") or ""
        user_id = user_id or str(data.get("userid") or "")

    if not token:
        raise ValueError("Token missing in API response: " + str(response.text))
        
    return token, user_id
