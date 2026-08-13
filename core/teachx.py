# core/teachx.py
import json
import base64
import logging
from curl_cffi import requests as cffi_requests

BASE_URL = "https://rozgarapinew.teachx.in"

def decode_jwt(token: str) -> dict:
    """JWT Token को Decode करके अंदर से user_id, email, mobile निकालने के लिए"""
    try:
        clean_token = token.replace("Bearer ", "").strip()
        parts = clean_token.split(".")
        if len(parts) >= 2:
            payload = parts[1]
            padding = '=' * (4 - len(payload) % 4)
            decoded_bytes = base64.urlsafe_b64decode(payload + padding)
            return json.loads(decoded_bytes.decode('utf-8'))
    except Exception as e:
        logging.error(f"JWT Decode error: {e}")
    return {}

def get_auth_session(token: str = ""):
    session = cffi_requests.Session(impersonate="chrome110")
    
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; M2010J19CI Build/RP1A.200720.011)",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://rojgarwithankit.co.in",
        "Referer": "https://rojgarwithankit.co.in/",
        "Client-Service": "Appx",
        "Auth-Key": "appxapi",
        "app-token": "appxapi",
        "Content-Type": "application/json",
        "Host": "rozgarapinew.teachx.in"
    }
    
    if token:
        clean_token = token.strip().strip('"').strip("'")
        if clean_token.startswith("Bearer "):
            clean_token = clean_token.replace("Bearer ", "").strip()
        
        headers.update({
            "Authorization": f"Bearer {clean_token}",
            "token": clean_token,
            "authorisation": clean_token,
        })

    session.headers.update(headers)
    return session

def get_user_profile(session, token: str, user_id: str = "") -> dict:
    jwt_data = decode_jwt(token) if token else {}
    extracted_id = user_id or str(jwt_data.get("id") or jwt_data.get("userid") or jwt_data.get("user_id") or jwt_data.get("sub") or "")
    jwt_email = jwt_data.get("email") or jwt_data.get("phone") or jwt_data.get("mobile") or ""
    jwt_name = jwt_data.get("name") or jwt_data.get("full_name") or ""

    url = f"{BASE_URL}/get/get_user_dt"
    params = {"userid": extracted_id} if extracted_id else {}
    
    try:
        res = session.get(url, params=params, timeout=15)
        if res.status_code == 200:
            data = res.json()
            user_data = data.get("data") or data.get("user") or data.get("user_details") or data
            
            if isinstance(user_data, list) and len(user_data) > 0:
                user_data = user_data[0]

            if isinstance(user_data, dict):
                name = user_data.get("full_name") or user_data.get("name") or user_data.get("username") or jwt_name or "Verified User"
                email = user_data.get("email") or user_data.get("useremail") or jwt_email or "N/A"
                phone = user_data.get("phone") or user_data.get("phone_number") or user_data.get("mobile") or ""
                
                final_id = str(user_data.get("userid") or user_data.get("id") or user_data.get("user_id") or extracted_id)
                contact = f"{email} | {phone}" if phone and email != "N/A" else (email if email != "N/A" else phone)
                
                return {
                    "name": name,
                    "email": contact or "N/A",
                    "id": final_id
                }
    except Exception as e:
        logging.error(f"Profile API Error: {e}")

    return {
        "name": jwt_name or "Verified User",
        "email": jwt_email or "N/A",
        "id": extracted_id
    }

def get_my_courses(session, user_id: str = ""):
    """पेड कोर्सेस फ़ैच करने के लिए"""
    urls = [
        f"{BASE_URL}/get/mycourseweb",
        f"{BASE_URL}/get/mycourse"
    ]
    params = {"userid": str(user_id)} if user_id else {}
    
    for url in urls:
        try:
            response = session.get(url, params=params, timeout=15)
            if response.status_code != 200 and params:
                response = session.get(url, timeout=15)

            if response.status_code == 200:
                data = response.json()
                courses = []

                if isinstance(data, list):
                    courses = data
                elif isinstance(data, dict):
                    courses = data.get("data") or data.get("courses") or data.get("user_courses") or []
                    if isinstance(courses, dict):
                        courses = courses.get("courses") or courses.get("list") or []

                if isinstance(courses, list) and len(courses) > 0:
                    return courses
        except Exception as e:
            logging.error(f"Error fetching courses: {e}")
            
    return []

# --- फ्री कोर्सेस वाले नए API फंक्शन्स ---

def get_free_exams(session):
    """फ्री कोर्सेस/Exams की लिस्ट फ़ैच करने के लिए (/get/examslist)"""
    url = f"{BASE_URL}/get/examslist"
    try:
        res = session.get(url, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get("data") or data.get("exams") or data.get("list") or []
    except Exception as e:
        logging.error(f"Error fetching free exams list: {e}")
    return []

def get_youtube_class_topics(session, exam_id: str, subject_id: str = "1187", start: str = "-1"):
    """फ्री क्लासेज और टॉपिक्स फ़ैच करने के लिए (/get/youtubeclasstopicapi)"""
    url = f"{BASE_URL}/get/youtubeclasstopicapi"
    params = {
        "examid": str(exam_id),
        "subjectid": str(subject_id),
        "start": str(start)
    }
    try:
        res = session.get(url, params=params, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get("data") or data.get("topics") or data.get("classes") or []
    except Exception as e:
        logging.error(f"Error fetching YT topics: {e}")
    return []

def get_telegram_course_info(session, course_id: str, item_type: str = "6"):
    """टेलीग्राम लिंक और डिटेल्स निकालने के लिए (/get/telegram)"""
    url = f"{BASE_URL}/get/telegram"
    params = {
        "course_id": str(course_id),
        "item_type": str(item_type)
    }
    try:
        res = session.get(url, params=params, timeout=15)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        logging.error(f"Error fetching Telegram info: {e}")
    return {}
