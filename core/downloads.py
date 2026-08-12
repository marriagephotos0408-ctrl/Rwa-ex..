# core/downloads.py
import os
import subprocess
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def download_teachx_hls(hls_url: str, dest: Path) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part_file = dest.with_suffix(".tmp.mp4")
    
    cmd = [
        "ffmpeg", "-y",
        "-user_agent", USER_AGENT,
        "-headers", "Referer: https://appx-play.akamai.net.in/\r\nOrigin: https://appx-play.akamai.net.in\r\n",
        "-i", hls_url,
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        str(part_file)
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=7200, check=True)
        part_file.rename(dest)
        return os.path.getsize(dest)
    except FileNotFoundError:
        raise RuntimeError("ffmpeg is not installed on this system.")
    except subprocess.CalledProcessError as e:
        if part_file.exists():
            part_file.unlink()
        stderr = (e.stderr or "").strip().splitlines()[-10:]
        raise RuntimeError(f"FFmpeg Error:\n{'\n'.join(stderr)}")
