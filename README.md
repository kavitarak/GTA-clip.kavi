# GTAClip by kavi.onlines — Get The Attention Clipper

**GTA = Get The Attention.** Turn any long YouTube video (or your own video) into viral vertical clips for Shorts, Reels and TikTok. An LLM picks the best moments, and ffmpeg cuts them, crops them to 9:16, and burns in a hook title and captions.

Works with any LLM: Gemini, OpenAI, Claude, or a free local model through Ollama. Works with any AI coding tool too, because the project includes an `AGENTS.md` file.

## How it works

1. Downloads the video and its subtitles with **yt-dlp** (or uses your own `.vtt`/`.srt` file).
2. Sends the timestamped transcript to an **LLM**, which returns the best self-contained moments with a title, a hook and a score.
3. Validates the picks: clamps timestamps, enforces min/max length, and removes overlaps.
4. Cuts each moment with **ffmpeg**, center-crops it to 9:16 at 1080x1920, and burns in captions.
5. Writes `clip_01.mp4`, `clip_02.mp4`, … and a `manifest.json` with the titles, hooks and reasons.

## Requirements

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/) with libass (the standard builds include it), on your PATH
- [yt-dlp](https://github.com/yt-dlp/yt-dlp), on your PATH
- An API key for one provider, or [Ollama](https://ollama.com) for a free local model

## Install

```bash
git clone https://github.com/kavitarak/GTA-clip.kavi.git
cd GTA-clip.kavi
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Set an API key (only the one you use):

```bash
export GEMINI_API_KEY=...        # or OPENAI_API_KEY / ANTHROPIC_API_KEY
```

## Usage

```bash
# Make 5 clips from a YouTube video with Gemini (default provider)
gtaclip "https://www.youtube.com/watch?v=VIDEO_ID"

# Preview the AI's picks first, without rendering
gtaclip "https://youtu.be/VIDEO_ID" --plan-only

# Use Claude, 8 clips of 15 to 45 seconds
gtaclip "https://youtu.be/VIDEO_ID" --provider anthropic --clips 8 --min-len 15 --max-len 45

# Free and local with Ollama
gtaclip "https://youtu.be/VIDEO_ID" --provider ollama --model llama3.1

# Your own video with your own subtitles
gtaclip my_video.mp4 --transcript my_video.srt --provider openai

# Hindi or Hinglish captions: use a font that supports Devanagari
gtaclip "https://youtu.be/VIDEO_ID" --font "Noto Sans Devanagari" --langs "hi.*,en.*"
```

Run `gtaclip --help` for every option.

## Use it from an AI coding tool

Open the folder in Claude Code, Codex, Gemini CLI, Antigravity or Cursor, then ask:

> Read AGENTS.md, install the project, and make 5 clips from this video: <URL>. Use the Gemini provider.

The agent can then run the CLI, add features, and fix errors. `AGENTS.md` tells it the layout, commands and rules.

## Output

```
output/
  clip_01.mp4   # 1080x1920, H.264 + AAC
  clip_01.ass   # captions and hook, editable
  ...
  manifest.json # title, hook, score, reason, start/end for each clip
```

## Limitations and next steps

- Cropping is centered. Face tracking (keeping the speaker in frame) is a good next step.
- Captions come from the video's subtitles. Videos with no subtitles need Whisper (not included yet).
- The default font is Arial, which does not render Devanagari. Pass `--font`.
- Results depend on the transcript quality and on the LLM you pick.

## Legal note

Only download and clip videos you own or have permission to use. YouTube's Terms of Service restrict downloading, and copyright applies to the clips you publish.

## License

MIT. Free to copy, use, modify and share. See [LICENSE](LICENSE). Contributions are welcome.

---
Made by **kavi.onlines** (Kavi Tarak). Follow for more AI tools: [YouTube @kavi.online](https://www.youtube.com/@kavi.online)
