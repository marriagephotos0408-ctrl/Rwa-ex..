# core/teachx.py
import logging
from curl_cffi import requests as cffi_requests

BASE_URL = "https://rozgarapinew.teachx.in"

def get_auth_session(token: str):
    session = cffi_requests.Session(impersonate="chrome110")
    
    clean_token = token.strip().strip('"').strip("'")
    if not clean_token.startswith("Bearer "):
        bearer_token = f"Bearer {clean_token}"
    else:
        bearer_token = clean_token
        clean_token = clean_token.replace("Bearer ", "")

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

def get_my_courses(session, user_id: str = ""):
    url = f"{BASE_URL}/get/mycourseweb"
    params = {"userid": str(user_id)} if user_id else {}
    
    try:
        response = session.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            response = session.get(url, timeout=15)

        if response.status_code != 200:
            logging.error(f"Courses Fetch Failed: HTTP {response.status_code}")
            return []

        data = response.json()
        courses = []

        if isinstance(data, list):
            courses = data
        elif isinstance(data, dict):
            courses = data.get("data") or data.get("courses") or data.get("user_courses") or []
            if isinstance(courses, dict):
                courses = courses.get("courses") or courses.get("list") or []

        return courses if isinstance(courses, list) else []

    except Exception as e:
        logging.error(f"Error in get_my_courses: {str(e)}")
        return []
