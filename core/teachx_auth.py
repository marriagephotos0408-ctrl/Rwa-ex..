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

    try:
        response = session.get(f"{BASE_URL}/get/sendotp", params={"phone": clean_phone}, headers=APP_HEADERS, timeout=15)
        response.raise_for_status()
        try:
            data = response.json()
        except Exception:
            data = {}
        return bool(data.get("status") or data.get("success") or True)
    except Exception as e:
        logging.error(f"GET sendotp failed: {e}")
        return False

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

def login_with_password(phone_or_email: str, password: str) -> tuple[str, str]:
    clean_input = phone_or_email.strip()
    if clean_input.isdigit() and len(clean_input) > 10:
        clean_phone = clean_input[-10:]
    else:
        clean_phone = clean_input

    session = get_tls_session()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://rojgarwithankit.co.in",
        "Referer": "https://rojgarwithankit.co.in/",
        "Client-Service": "Appx",
        "Auth-Key": "appxapi",
        "app-token": "appxapi",
        "Host": "rozgarapinew.teachx.in"
    }

    try:
        session.get(
            f"{BASE_URL}/get/check_user_exist", 
            params={"email_or_phone": clean_phone}, 
            headers=headers, 
            timeout=15
        )
    except Exception:
        pass

    login_url = f"{BASE_URL}/post/userLogin?extra_details=0"
    payload = {
        "email_or_phone": clean_phone,
        "password": str(password).strip()
    }
    
    response = session.post(login_url, data=payload, headers=headers, timeout=15)
    
    if response.status_code != 200 and clean_phone.isdigit() and len(clean_phone) == 10:
        payload["email_or_phone"] = f"91{clean_phone}"
        response = session.post(login_url, data=payload, headers=headers, timeout=15)

    if response.status_code != 200:
        raise ValueError(f"HTTP Error {response.status_code}")
        
    try:
        data = response.json()
    except Exception:
        data = json.loads(response.text)
        
    res_data = data.get("data") or data
    token = ""
    user_id = ""
    
    if isinstance(res_data, dict):
        token = res_data.get("token") or res_data.get("authorisation") or res_data.get("authorization") or ""
        user_id = str(res_data.get("userid") or res_data.get("id") or res_data.get("user_id") or "")

    if not token and isinstance(data, dict):
        token = data.get("token") or data.get("authorisation") or ""
        user_id = user_id or str(data.get("userid") or data.get("id") or "")

    if not token:
        err_msg = data.get("message") if isinstance(data, dict) and data.get("message") else "Invalid Credentials"
        raise ValueError(err_msg)
        
    return token, user_id
