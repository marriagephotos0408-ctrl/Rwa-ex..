# core/teachx.py
import requests
from typing import Optional

BASE_URL = "https://rozgarapinew.teachx.in"

def get_authenticated_session(token: str) -> requests.Session:
    """Create session with required AppX headers."""
    session = requests.Session()
    session.headers.update({
        "token": token,
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Client-Service": "Appx",
        "Auth-Key": "appxapi",
        "Origin": "https://appx-play.akamai.net.in",
        "Referer": "https://appx-play.akamai.net.in/"
    })
    return session

def get_my_courses(session: requests.Session, user_id: str) -> list:
    url = f"{BASE_URL}/get/mycourseweb"
    params = {"userid": user_id}
    r = session.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data.get("data", []) if isinstance(data, dict) else data

def get_course_filters(session: requests.Session, course_id: str) -> dict:
    url = f"{BASE_URL}/get/userfiltercourse"
    params = {"courseid": course_id}
    r = session.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def fetch_class_lectures(session: requests.Session, course_id: str, subject_id: str, topic_id: str, concept_id: int = 1) -> list:
    all_videos = []
    start = 0
    while True:
        url = f"{BASE_URL}/get/livecourseclassbycoursesubtopconceptapiv3"
        params = {
            "courseid": course_id,
            "subjectid": subject_id,
            "topicid": topic_id,
            "conceptid": concept_id,
            "start": start
        }
        r = session.get(url, params=params, timeout=10)
        r.raise_for_status()
        res = r.json()
        
        items = res.get("data", []) if isinstance(res, dict) else (res if isinstance(res, list) else [])
        if not items:
            break
            
        all_videos.extend(items)
        if len(items) < 10:
            break
        start += len(items)
        
    return all_videos

def fetch_video_stream_url(session: requests.Session, course_id: str, video_id: str) -> Optional[str]:
    url = f"{BASE_URL}/get/fetchVideoDetailsById"
    params = {
        "course_id": course_id,
        "video_id": video_id,
        "ytflag": 0,
        "folder_wise_course": 0,
        "lc_app_api_url": ""
    }
    r = session.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    
    vdata = data.get("data", data)
    if isinstance(vdata, dict):
        return vdata.get("video_url") or vdata.get("hls_url") or vdata.get("url") or vdata.get("encrypted_link")
    return None
