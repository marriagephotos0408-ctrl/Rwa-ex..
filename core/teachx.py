# core/teachx.py
import io
import json
import logging
from curl_cffi import requests as cffi_requests

BASE_URL = "https://rozgarapinew.teachx.in"

def get_auth_session(token: str = ""):
    session = cffi_requests.Session(impersonate="chrome110")
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; M2010J19CI Build/RP1A.200720.011)",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://rojgarwithankit.co.in",
        "Referer": "https://rojgarwithankit.co.in/",
        "Client-Service": "Appx",
        "Auth-Key": "appxapi",
        "app-token": "appxapi",
        "Host": "rozgarapinew.teachx.in"
    }
    if token:
        clean_token = token.replace("Bearer ", "").strip().strip('"')
        headers.update({
            "Authorization": f"Bearer {clean_token}",
            "token": clean_token,
        })
    session.headers.update(headers)
    return session

def get_subjects_by_exam(session, exam_id: str):
    """1. Exam ID से सारे Subjects की लिस्ट निकालना"""
    url = f"{BASE_URL}/get/youtubeclasstopicapi"
    params = {"examid": str(exam_id), "subjectid": "0", "start": "-1"}
    try:
        res = session.get(url, params=params, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list):
                return data
            return data.get("data") or data.get("subjects") or []
    except Exception as e:
        logging.error(f"Error fetching subjects: {e}")
    return []

def get_topics_by_subject(session, exam_id: str, subject_id: str):
    """2. Subject ID से उसके अंदर के सारे Topics की लिस्ट निकालना"""
    url = f"{BASE_URL}/get/youtubeclasstopicapi"
    params = {"examid": str(exam_id), "subjectid": str(subject_id), "start": "-1"}
    try:
        res = session.get(url, params=params, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list):
                return data
            return data.get("data") or data.get("topics") or []
    except Exception as e:
        logging.error(f"Error fetching topics: {e}")
    return []

def get_concept_classes(session, exam_id: str, subject_id: str, topic_id: str, start: str = "0"):
    """3. Naye API Endpoint se Concept wise Videos aur PDFs fetch karna"""
    url = f"{BASE_URL}/get/youtubeclassbyexamsubtopconceptapiv2"
    params = {
        "examid": str(exam_id),
        "subjectid": str(subject_id),
        "topicid": str(topic_id),
        "start": str(start)
    }
    try:
        res = session.get(url, params=params, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list):
                return data
            return data.get("data") or data.get("classes") or []
    except Exception as e:
        logging.error(f"Error fetching concept classes: {e}")
    return []

def extract_full_exam_txt(session, exam_id: str) -> tuple:
    """4. Pura Exam auto-crawl karke TXT File banana"""
    txt = f"==================================================\n"
    txt += f"        COURSE CONTENT - EXAM ID: {exam_id}\n"
    txt += f"==================================================\n\n"

    subjects = get_subjects_by_exam(session, exam_id)
    v_count, p_count = 0, 0

    if not subjects:
        subjects = [{"id": "0", "name": "General Subject"}]

    for sub in subjects:
        sub_id = str(sub.get("id") or sub.get("subjectid") or "0")
        sub_name = sub.get("name") or sub.get("subject_name") or "Subject"

        txt += f"\n==================================================\n"
        txt += f"📘 SUBJECT: {sub_name} (ID: {sub_id})\n"
        txt += f"==================================================\n\n"

        topics = get_topics_by_subject(session, exam_id, sub_id)
        if not topics:
            topics = [{"id": "0", "topic_name": "General Topic"}]

        for top in topics:
            top_id = str(top.get("id") or top.get("topicid") or "0")
            top_name = top.get("topic_name") or top.get("title") or "Topic"

            txt += f"  📁 TOPIC: {top_name}\n"
            txt += f"  ----------------------------------------------\n"

            classes = get_concept_classes(session, exam_id, sub_id, top_id)
            if classes:
                for idx, cls in enumerate(classes, 1):
                    c_title = cls.get("title") or cls.get("topic_name") or f"Lecture {idx}"
                    v_url = cls.get("url") or cls.get("youtube_url") or cls.get("link") or ""
                    
                    # AppX / Static PDF URL Extractor
                    p_url = (cls.get("pdf_url") or cls.get("pdf") or 
                             cls.get("attachment") or cls.get("notes_url") or "")

                    txt += f"   {idx}. {c_title}\n"
                    if v_url:
                        txt += f"      🎥 Video: {v_url}\n"
                        v_count += 1
                    if p_url:
                        txt += f"      📄 PDF: {p_url}\n"
                        p_count += 1
                    txt += "\n"
            else:
                txt += "   (No classes found)\n\n"

    txt += f"==================================================\n"
    txt += f"SUMMARY: Total Videos: {v_count} | Total PDFs: {p_count}\n"
    txt += f"==================================================\n"

    stream = io.BytesIO(txt.encode('utf-8'))
    filename = f"Exam_{exam_id}_Full_Course.txt"
    stream.name = filename
    return stream, filename, v_count, p_count
