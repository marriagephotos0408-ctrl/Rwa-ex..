# core/teachx.py
import io
import urllib.parse
import logging
from curl_cffi import requests as cffi_requests
from config import BASE_URL, ENDPOINTS, DEFAULT_HEADERS

logging.basicConfig(level=logging.INFO)

def get_auth_session(token: str = ""):
    session = cffi_requests.Session(impersonate="chrome110")
    headers = DEFAULT_HEADERS.copy()
    if token:
        clean_token = token.replace("Bearer ", "").strip().strip('"')
        headers.update({
            "Authorization": f"Bearer {clean_token}",
            "token": clean_token,
        })
    session.headers.update(headers)
    return session

def send_otp_api(phone: str):
    session = get_auth_session()
    url = f"{BASE_URL}{ENDPOINTS['send_otp']}"
    try:
        res = session.get(url, params={"phone": phone}, timeout=15)
        return res.json()
    except Exception as e:
        logging.error(f"Send OTP Error: {e}")
        return None

def verify_otp_api(phone: str, otp: str):
    session = get_auth_session()
    url = f"{BASE_URL}{ENDPOINTS['verify_otp']}"
    device_id = f"WebBrowser{phone}niudjrtwvx"
    params = {
        "useremail": phone,
        "otp": otp,
        "device_id": device_id,
        "mydeviceid": "",
        "mydeviceid2": ""
    }
    try:
        res = session.get(url, params=params, timeout=15)
        return res.json()
    except Exception as e:
        logging.error(f"Verify OTP Error: {e}")
        return None

def auto_extract_keys(item: dict) -> dict:
    if not isinstance(item, dict):
        return {"id": "", "title": str(item), "video": "", "pdf": ""}

    title_keys = ["name", "title", "topic_name", "subject_name", "exam_name", "course_name", "chapter_name"]
    title = next((str(item[k]) for k in title_keys if k in item and item[k]), "Item")

    id_keys = ["id", "examid", "subjectid", "topicid", "course_id", "exam_id", "subject_id"]
    item_id = next((str(item[k]) for k in id_keys if k in item and item[k]), "")

    video_keys = ["url", "youtube_url", "link", "video_url", "stream_url", "embed_url"]
    video = next((str(item[k]) for k in video_keys if k in item and item[k]), "")

    pdf_keys = ["pdf_url", "pdf", "attachment", "notes", "notes_url", "file", "download_url"]
    pdf = next((str(item[k]) for k in pdf_keys if k in item and item[k]), "")

    # Extract Direct PDF from ClassX Viewer URL if present
    if "pdfjs-latest" in pdf or "file=" in pdf:
        try:
            parsed = urllib.parse.urlparse(pdf)
            queries = urllib.parse.parse_qs(parsed.query)
            if 'file' in queries:
                pdf = queries['file'][0]
        except Exception:
            pass

    return {"id": item_id, "title": title, "video": video, "pdf": pdf}

def fetch_dynamic_api(session, endpoint_key: str, params: dict = None):
    endpoint = ENDPOINTS.get(endpoint_key, endpoint_key)
    url = f"{BASE_URL}{endpoint}" if not endpoint.startswith("http") else endpoint
    try:
        res = session.get(url, params=params, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                for key in ["data", "list", "topics", "subjects", "classes", "exams", "courses", "result"]:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                return [data]
    except Exception as e:
        logging.error(f"Dynamic API Fetch Error ({endpoint_key}): {e}")
    return []

def extract_recursive_txt(session, initial_data: list, exam_id: str) -> tuple:
    txt = f"==================================================\n"
    txt += f"      AUTOMATIC DYNAMIC EXTRACTOR (EXAM ID: {exam_id})\n"
    txt += f"==================================================\n\n"

    v_count, p_count = 0, 0

    def parse_node(node, depth=0):
        nonlocal v_count, p_count, txt
        indent = "  " * depth

        if isinstance(node, list):
            for child in node:
                parse_node(child, depth)
        elif isinstance(node, dict):
            parsed = auto_extract_keys(node)
            txt += f"{indent}📌 {parsed['title']} (ID: {parsed['id']})\n"
            
            if parsed['video']:
                txt += f"{indent}   🎥 Video: {parsed['video']}\n"
                v_count += 1
            if parsed['pdf']:
                txt += f"{indent}   📄 PDF: {parsed['pdf']}\n"
                p_count += 1
            
            txt += "\n"

            for k, v in node.items():
                if isinstance(v, (list, dict)):
                    parse_node(v, depth + 1)

    parse_node(initial_data)

    txt += f"==================================================\n"
    txt += f"SUMMARY: Total Videos: {v_count} | Total PDFs: {p_count}\n"
    txt += f"==================================================\n"

    stream = io.BytesIO(txt.encode('utf-8'))
    filename = f"Dynamic_Exam_{exam_id}.txt"
    stream.name = filename
    return stream, filename, v_count, p_count
