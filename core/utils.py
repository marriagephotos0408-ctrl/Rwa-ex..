# core/utils.py
import re

def safe_filename(name: str) -> str:
    """Sanitize string for safe cross-platform filenames."""
    if not name:
        return "Untitled"
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:100]
