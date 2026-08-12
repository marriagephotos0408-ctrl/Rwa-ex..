# core/teachx.py
import logging
from curl_cffi import requests as cffi_requests

BASE_URL = "https://rozgarapinew.teachx.in"

def get_auth_session(token: str):
    session = cffi_requests.Session(impersonate="chrome110")
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; M2010J19CI Build/RP1A.200720.011)",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate",
        "Client-Service": "Appx",
        "Auth-Key": "appxapi",
        "app-token": "appxapi",
        "token": token,
        "authorisation": token,
        "Authorization": f"Bearer {token}",
        "Host": "rozgarapinew.teachx.in"
    }
    session.headers.update(headers)
    return session

def get_my_courses(session, user_id: str):
    # Endpoint 1: Standard mycourseweb endpoint
    url = f"{BASE_URL}/get/mycourseweb"
    params = {"userid": str(user_id)}
    
    response = session.get(url, params=params, timeout=15)
    
    # Fallback to post or alternate get route if 500/error occurs
    if response.status_code != 200:
        alt_url = f"{BASE_URL}/get/mycourse"
        response = session.get(alt_url, params=params, timeout=15)
        
    response.raise_for_status()
    data = response.json()
    
    # Extract course list safely from various possible JSON structures
    courses = []
    if isinstance(data, list):
        courses = data
    elif isinstance(data, dict):
        courses = data.get("data") or data.get("courses") or data.get("user_courses") or []
        if isinstance(courses, dict):
            courses = courses.get("courses", [])
            
    return courses if isinstance(courses, list) else []
