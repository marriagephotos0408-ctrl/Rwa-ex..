import os
import asyncio
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

async def download_teachx_hls(hls_url: str, dest: Path) -> int:
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
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await asyncio.wait_for(process.communicate(), timeout=7200)

        if process.returncode == 0 and part_file.exists():
            part_file.rename(dest)
            return os.path.getsize(dest)
        else:
            if part_file.exists():
                part_file.unlink()
            error_log = stderr.decode('utf-8', errors='ignore').strip().splitlines()[-10:]
            raise RuntimeError(f"FFmpeg Error:\n{'\n'.join(error_log)}")

    except FileNotFoundError:
        raise RuntimeError("FFmpeg is not installed on system path.")
    except asyncio.TimeoutError:
        if part_file.exists():
            part_file.unlink()
        raise RuntimeError("Download timed out after 2 hours.")
