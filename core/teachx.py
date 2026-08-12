# core/teachx.py
import logging
from curl_cffi import requests as cffi_requests

BASE_URL = "https://rozgarapinew.teachx.in"

def get_auth_session(token: str):
    session = cffi_requests.Session(impersonate="chrome110")
    
    clean_token = token.strip().strip('"').strip("'")
    if clean_token.startswith("Bearer "):
        clean_token = clean_token.replace("Bearer ", "").strip()
        
    bearer_token = f"Bearer {clean_token}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://rojgarwithankit.co.in",
        "Referer": "https://rojgarwithankit.co.in/",
        "Client-Service": "Appx",
        "Auth-Key": "appxapi",
        "app-token": "appxapi",
        "Authorization": bearer_token,
        "token": clean_token,
        "authorisation": clean_token,
        "Host": "rozgarapinew.teachx.in"
    }
    
    session.headers.update(headers)
    return session

def get_user_profile(session, user_id: str = "") -> dict:
    """/get/get_user_dt एंडपॉइंट से यूज़र डिटेल्स लोड करने के लिए"""
    urls = [
        f"{BASE_URL}/get/get_user_dt",
        f"{BASE_URL}/get/get_my_profile"
    ]
    
    params = {"userid": str(user_id)} if user_id else {}
    
    for url in urls:
        try:
            res = session.get(url, params=params, timeout=15)
            if res.status_code == 200:
                data = res.json()
                user_data = data.get("data") or data.get("user") or data.get("user_details") or data
                
                if isinstance(user_data, list) and len(user_data) > 0:
                    user_data = user_data[0]

                if isinstance(user_data, dict):
                    return {
                        "name": user_data.get("name") or user_data.get("username") or user_data.get("full_name") or "User",
                        "email": user_data.get("email") or user_data.get("phone") or user_data.get("mobile") or "N/A",
                        "id": str(user_data.get("id") or user_data.get("userid") or user_data.get("user_id") or user_id)
                    }
        except Exception as e:
            logging.error(f"Profile fetch failed for {url}: {e}")
            
    return {"name": "User", "email": "N/A", "id": str(user_id)}

def get_my_courses(session, user_id: str = ""):
    """कोर्सेस फ़ैच करने के लिए"""
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
            logging.error(f"Error fetching courses from {url}: {e}")
            
    return []
