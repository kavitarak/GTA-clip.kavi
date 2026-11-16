from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

from .analyze import DEFAULT_MODELS, pick_clips
from .download import download, probe_duration
from .render import render_clip
from .subtitles import parse_subtitles, window


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gtaclip",
        description="Turn a long video into viral vertical (9:16) clips using an LLM + ffmpeg.",
    )
    p.add_argument("source", help="YouTube URL, or a local video file (then also pass --transcript)")
    p.add_argument("--transcript", help="existing .vtt or .srt file to use instead of downloading subtitles")
    p.add_argument("--clips", type=int, default=5, help="how many clips to make (default 5)")
    p.add_argument("--min-len", type=float, default=20, help="minimum clip length in seconds")
    p.add_argument("--max-len", type=float, default=60, help="maximum clip length in seconds")
    p.add_argument("--provider", choices=sorted(DEFAULT_MODELS), default="gemini",
                   help="which LLM picks the clips (default gemini)")
    p.add_argument("--model", help="model name; defaults depend on the provider")
    p.add_argument("--langs", default="en.*,hi.*",
                   help="subtitle languages to fetch, as a yt-dlp pattern list")
    p.add_argument("--font", default="Arial",
                   help='caption font, e.g. "Noto Sans Devanagari" for Hindi text')
    p.add_argument("--out", default="output", help="output folder")
    p.add_argument("--plan-only", action="store_true",
                   help="only print the AI's picks, do not render video")
    p.add_argument("--keep-source", action="store_true", help="keep the downloaded source video")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    out = Path(args.out).resolve()
    work = out / "_work"
    work.mkdir(parents=True, exist_ok=True)

    if os.path.isfile(args.source):
        video, sub_files = args.source, []
    else:
        video, sub_files = download(args.source, str(work), args.langs)

    transcript_path = args.transcript or (sub_files[0] if sub_files else None)
    if not transcript_path:
        raise SystemExit("No subtitles found. Pass --transcript FILE (.vtt or .srt) or change --langs.")

    cues = parse_subtitles(Path(transcript_path).read_text(encoding="utf-8", errors="replace"))
    if not cues:
        raise SystemExit("The transcript has no readable lines.")

    duration = probe_duration(video)
    print(f"Video {duration:.0f}s, {len(cues)} transcript lines. Asking {args.provider} for picks...")
    picks = pick_clips(cues, duration, args.clips, args.min_len, args.max_len,
                       args.provider, args.model)
    if not picks:
        raise SystemExit("The model returned no usable clips. Try another --provider or --model.")

    manifest = []
    for i, pick in enumerate(picks, 1):
        print(f"[{i}] {pick.start:.1f}-{pick.end:.1f}s  score {pick.score:.0f}  {pick.title}")
        entry = {
            "file": f"clip_{i:02d}.mp4",
            "start": pick.start,
            "end": pick.end,
            "title": pick.title,
            "hook": pick.hook,
            "score": pick.score,
            "reason": pick.reason,
        }
        if not args.plan_only:
            render_clip(video, pick.start, pick.end, str(out / entry["file"]),
                        window(cues, pick.start, pick.end), pick.hook or None, args.font)
        manifest.append(entry)

    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if not args.keep_source:
        shutil.rmtree(work, ignore_errors=True)
    print(f"Done. Output in {out}")
    return 0


def run() -> None:
    raise SystemExit(main())
