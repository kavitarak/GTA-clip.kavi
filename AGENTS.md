# AGENTS.md: notes for AI coding agents

This file is for Claude Code, OpenAI Codex, Gemini CLI, Google Antigravity, Cursor and similar tools. Read it before changing anything.

## What this project does
`gtaclip` (GTAClip, "Get The Attention") takes a YouTube URL (or a local video plus a transcript file), asks an LLM to pick the most viral self-contained moments, then uses ffmpeg to cut each moment, center-crop it to 9:16, and burn in a hook title and captions.

## Layout
- `clipper/cli.py`: argument parsing and the end-to-end pipeline.
- `clipper/download.py`: yt-dlp download and ffprobe duration.
- `clipper/subtitles.py`: .vtt/.srt parser (dedupes YouTube rolling captions), window slicing, ASS writer.
- `clipper/analyze.py`: LLM prompt and provider calls (gemini, openai, anthropic, ollama) plus clip validation.
- `clipper/render.py`: the ffmpeg command.
- `tests/`: pytest unit tests. They do not need the network, yt-dlp or ffmpeg.

## Commands
- Install: `pip install -e ".[dev]"`
- Test: `pytest -q`
- Plan only (no rendering): `python -m clipper "<url>" --plan-only --provider gemini`
- Render: `python -m clipper "<url>" --clips 5 --provider gemini --out output`

## Making clips for the user (agent mode, no API key needed)
When the user asks you to make clips from a video, YOU pick the clips. Do not ask them for an API key.

1. Check `ffmpeg` and `yt-dlp` are installed. If not, install them (`pip install yt-dlp`; ffmpeg from the OS package manager, `winget install ffmpeg` on Windows, `brew install ffmpeg` on macOS).
2. Install the project once: `pip install -e .`
3. Save the transcript: `gtaclip "<URL>" --clips 5 --dump-transcript transcript.txt`
4. Read `transcript.txt`. It contains the editing instructions and the timestamped transcript. Choose the best moments and write `picks.json`:
   `{"clips": [{"start": 12.5, "end": 48.0, "title": "...", "hook": "...", "score": 85, "reason": "..."}]}`
   Write the hook and title in the speaker's language (Hindi, Hinglish or English). Hook: at most 8 words.
5. Render: `gtaclip "<URL>" --clips 5 --picks picks.json`
6. Tell the user where the clips are (`output/clip_01.mp4` …) and show them `output/manifest.json`.

For Hindi (Devanagari) captions add `--font "Noto Sans Devanagari"`. If the video has no subtitles, tell the user; Whisper is not built in yet.

## Rules for changes
- Keep dependencies minimal. The only runtime dependency is `httpx`. yt-dlp and ffmpeg are external binaries.
- Never hardcode API keys. Read them from environment variables.
- Any LLM output is untrusted. Validate timestamps (clamp to duration, enforce min/max length, drop overlaps), as `pick_clips` already does.
- Add or update a test for every parser or timing change.
- Do not add features that download content the user has no right to use.
