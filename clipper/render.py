from __future__ import annotations

import os
import subprocess

from .download import require_binary
from .subtitles import Cue, write_ass

# Center-crop any landscape or square source to 9:16, then scale to 1080x1920.
VIDEO_FILTER = "crop='min(iw,trunc(ih*9/16/2)*2)':ih,scale=1080:1920,setsar=1"


def render_clip(source: str, start: float, end: float, out_path: str,
                captions: list[Cue], hook: str | None, font: str = "Arial") -> None:
    """Cut [start, end] from source, crop to vertical, and burn in hook + captions."""
    require_binary("ffmpeg")
    out_dir = os.path.dirname(os.path.abspath(out_path))
    name = os.path.basename(out_path)
    ass_name = os.path.splitext(name)[0] + ".ass"

    write_ass(os.path.join(out_dir, ass_name), captions, hook, font=font)

    # Run ffmpeg inside out_dir and reference the .ass by bare name, so the
    # subtitles filter never needs path escaping (this matters on Windows).
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", f"{start:.3f}", "-i", os.path.abspath(source),
        "-t", f"{end - start:.3f}",
        "-vf", f"{VIDEO_FILTER},subtitles={ass_name}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
        name,
    ]
    subprocess.run(cmd, cwd=out_dir, check=True)
