# core/teachx_auth.py
import logging
from curl_cffi import requests as cffi_requests

BASE_URL = "https://rozgarapinew.teachx.in"

# Full Android AppX Spoof Headers
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
    """Creates a TLS Impersonated session to bypass Cloudflare WAF on Cloud Servers."""
    return cffi_requests.Session(impersonate="chrome110")

def send_otp(phone: str) -> bool:
    clean_phone = phone[-10:]  # Pure 10-digit clean phone
    session = get_tls_session()
    
    # 1. Try Primary POST Endpoint
    post_url = f"{BASE_URL}/post/sendotp"
    payload = {"phone": clean_phone}
    
    try:
        response = session.post(post_url, json=payload, headers=APP_HEADERS, timeout=15)
        if response.status_code == 200:
            return True
    except Exception as e:
        logging.error(f"POST sendotp failed: {e}")

    # 2. Fallback GET Endpoint with Query Params
    get_url = f"{BASE_URL}/get/sendotp"
    params = {"phone": clean_phone}
    
    response = session.get(get_url, params=params, headers=APP_HEADERS, timeout=15)
    response.raise_for_status()
    
    data = response.json()
    return bool(data.get("status") or data.get("success") or True)

def verify_otp_and_login(phone: str, otp: str) -> tuple[str, str]:
    clean_phone = phone[-10:]
    session = get_tls_session()
    
    url = f"{BASE_URL}/post/verifyotp"
    payload = {"phone": clean_phone, "otp": otp}
    
    response = session.post(url, json=payload, headers=APP_HEADERS, timeout=15)
    if response.status_code != 200:
        response = session.get(f"{BASE_URL}/get/verifyotp", params={"phone": clean_phone, "otp": otp}, headers=APP_HEADERS, timeout=15)
        
    response.raise_for_status()
    data = response.json()
    
    user_data = data.get("data", data)
    
    # Dynamic Token Extraction
    token = (
        user_data.get("token") or 
        user_data.get("authorisation") or 
        user_data.get("jwt") or 
        data.get("token") or ""
    )
    
    # Dynamic User ID Extraction
    user_id = str(
        user_data.get("userid") or 
        user_data.get("id") or 
        user_data.get("user_id") or 
        data.get("userid") or ""
    )
    
    if not token:
        raise ValueError("Token missing in response! Response: " + str(data))
        
    return token, user_id
