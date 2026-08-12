# core/teachx.py
from curl_cffi import requests as cffi_requests

BASE_URL = "https://rozgarapinew.teachx.in"

def get_auth_session(token: str):
    session = cffi_requests.Session(impersonate="chrome110")
    session.headers.update({
        "token": token,
        "Authorization": f"Bearer {token}",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11)",
        "Accept": "application/json",
        "Client-Service": "Appx",
        "Auth-Key": "appxapi",
        "app-token": "appxapi"
    })
    return session

def get_my_courses(session, user_id: str) -> list:
    url = f"{BASE_URL}/get/mycourseweb"
    params = {"userid": user_id}
    res = session.get(url, params=params, timeout=15)
    res.raise_for_status()
    data = res.json()
    return data.get("data", []) if isinstance(data, dict) else data
