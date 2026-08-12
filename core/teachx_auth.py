import logging
from curl_cffi import requests as cffi_requests

BASE_URL = "https://rozgarapinew.teachx.in"

def login_with_password(phone_or_email: str, password: str):
    """
    User/Password Login for TeachX/ClassX API
    """
    session = cffi_requests.Session(impersonate="chrome110")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://rojgarwithankit.co.in",
        "Referer": "https://rojgarwithankit.co.in/",
        "Client-Service": "Appx",
        "Auth-Key": "appxapi",
        "app-token": "appxapi",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    session.headers.update(headers)
    
    # 1. Step 1: Check User Exist
    check_url = f"{BASE_URL}/get/check_user_exist"
    check_params = {"email_or_phone": str(phone_or_email).strip()}
    
    try:
        check_res = session.get(check_url, params=check_params, timeout=15)
        # अगर चेक API फ़ेल भी हो तो आगे प्रयास जारी रखेंगे
    except Exception as e:
        logging.warning(f"User check failed: {str(e)}")

    # 2. Step 2: User Login Post Request
    login_url = f"{BASE_URL}/post/userLogin?extra_details=0"
    payload = {
        "email_or_phone": str(phone_or_email).strip(),
        "password": str(password).strip()
    }
    
    response = session.post(login_url, data=payload, timeout=15)
    
    if response.status_code != 200:
        raise Exception(f"Server returned HTTP {response.status_code}")
        
    data = response.json()
    
    # डेटा प्रोसेसिंग व ऑथ टोकन निकालना
    res_data = data.get("data") or data
    if isinstance(res_data, dict):
        token = res_data.get("token") or res_data.get("authorisation") or res_data.get("authorization")
        user_id = res_data.get("userid") or res_data.get("id") or res_data.get("user_id")
        
        if token:
            return token, str(user_id) if user_id else ""
            
    # अगर डायरेक्ट लॉगिन में टोकन न मिले तो एरर मैसेज
    err_msg = data.get("message") or "Invalid credentials or login failed"
    raise Exception(err_msg)
