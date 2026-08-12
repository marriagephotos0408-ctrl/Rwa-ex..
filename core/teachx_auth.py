# core/teachx_auth.py
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
    
    # Primary POST Attempt
    try:
        response = session.post(f"{BASE_URL}/post/sendotp", json={"phone": clean_phone}, headers=APP_HEADERS, timeout=15)
        if response.status_code == 200:
            return True
    except Exception as e:
        logging.error(f"POST sendotp failed: {e}")

    # Fallback GET Attempt
    response = session.get(f"{BASE_URL}/get/sendotp", params={"phone": clean_phone}, headers=APP_HEADERS, timeout=15)
    response.raise_for_status()
    data = response.json()
    return bool(data.get("status") or data.get("success") or True)

def verify_otp_and_login(phone: str, otp: str) -> tuple[str, str]:
    clean_phone = phone[-10:]
    session = get_tls_session()
    
    # Exact teachx OTP verify endpoint
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
    data = response.json()
    
    user_data = data.get("data", data)
    
    # Extract Token dynamically
    token = (
        user_data.get("token") or 
        user_data.get("authorisation") or 
        user_data.get("jwt") or 
        data.get("token") or ""
    )
    
    # Extract User ID dynamically
    user_id = str(
        user_data.get("userid") or 
        user_data.get("id") or 
        user_data.get("user_id") or 
        data.get("userid") or ""
    )
    
    if not token:
        raise ValueError("Token missing in response! API Output: " + str(data))
        
    return token, user_id
