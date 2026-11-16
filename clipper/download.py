from __future__ import annotations

import glob
import os
import shutil
import subprocess


def require_binary(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"'{name}' was not found on PATH. Install it first (see README).")


def download(url: str, workdir: str, langs: str) -> tuple[str, list[str]]:
    """Download a video plus its subtitles with yt-dlp.

    Returns (video_path, subtitle_paths). Subtitles may be empty.
    """
    require_binary("yt-dlp")
    template = os.path.join(workdir, "source.%(ext)s")
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs", langs,
        "--sub-format", "vtt/srt/best",
        "-f", "bv*[height<=1080]+ba/b[height<=1080]/b",
        "--merge-output-format", "mp4",
        "-o", template,
        url,
    ]
    subprocess.run(cmd, check=True)

    videos = [
        p for p in glob.glob(os.path.join(workdir, "source.*"))
        if not p.endswith((".vtt", ".srt"))
    ]
    if not videos:
        raise RuntimeError("yt-dlp finished but no video file was found.")
    subs = sorted(
        glob.glob(os.path.join(workdir, "source*.vtt"))
        + glob.glob(os.path.join(workdir, "source*.srt"))
    )
    return videos[0], subs


def probe_duration(path: str) -> float:
    require_binary("ffprobe")
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)
