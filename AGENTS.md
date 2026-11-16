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

## Rules for changes
- Keep dependencies minimal. The only runtime dependency is `httpx`. yt-dlp and ffmpeg are external binaries.
- Never hardcode API keys. Read them from environment variables.
- Any LLM output is untrusted. Validate timestamps (clamp to duration, enforce min/max length, drop overlaps), as `pick_clips` already does.
- Add or update a test for every parser or timing change.
- Do not add features that download content the user has no right to use.
