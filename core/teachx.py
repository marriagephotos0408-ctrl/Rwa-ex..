# core/teachx_auth.py
import requests

BASE_URL = "https://rozgarapinew.teachx.in"

# Absolute Mobile App Headers to Bypass Cloudflare/WAF
HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; M2010J19CI Build/RP1A.200720.011)",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json; charset=UTF-8",
    "Client-Service": "Appx",
    "Auth-Key": "appxapi",
    "app-token": "appxapi",
    "Host": "rozgarapinew.teachx.in"
}

def check_user_exist(phone_or_email: str) -> dict:
    url = f"{BASE_URL}/get/check_user_exist"
    clean_phone = phone_or_email[-10:]
    params = {"email_or_phone": clean_phone}
    
    r = requests.get(url, params=params, headers=HEADERS, timeout=12)
    if r.status_code == 403:
        r = requests.post(url, json={"email_or_phone": clean_phone}, headers=HEADERS, timeout=12)
    r.raise_for_status()
    return r.json()

def send_otp(phone: str) -> bool:
    clean_phone = phone[-10:]  # Clean 10-digit number
    
    # Primary POST Attempt with JSON Payload (Bypasses URL Query 403 block)
    post_url = f"{BASE_URL}/post/sendotp"
    payload = {"phone": clean_phone}
    
    try:
        r = requests.post(post_url, json=payload, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            return True
    except Exception:
        pass

    # Fallback GET Attempt with exact App parameters
    get_url = f"{BASE_URL}/get/sendotp"
    r = requests.get(get_url, params={"phone": clean_phone}, headers=HEADERS, timeout=12)
    r.raise_for_status()
    data = r.json()
    return bool(data.get("status") or data.get("success") or True)

def verify_otp_and_login(phone: str, otp: str) -> tuple[str, str]:
    clean_phone = phone[-10:]
    url = f"{BASE_URL}/post/verifyotp"
    payload = {"phone": clean_phone, "otp": otp}
    
    r = requests.post(url, json=payload, headers=HEADERS, timeout=12)
    if r.status_code != 200:
        r = requests.get(f"{BASE_URL}/get/verifyotp", params=payload, headers=HEADERS, timeout=12)
        
    r.raise_for_status()
    data = r.json()
    
    user_data = data.get("data", data)
    token = user_data.get("token") or user_data.get("authorisation") or user_data.get("jwt") or ""
    user_id = str(user_data.get("userid") or user_data.get("id") or user_data.get("user_id") or "")
    
    return token, user_id
