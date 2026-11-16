from __future__ import annotations

import html
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str


_TS = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{1,3})")


def parse_ts(value: str) -> float:
    """Parse '00:01:02.345' or '01:02,345' into seconds."""
    m = _TS.search(value)
    if not m:
        raise ValueError(f"bad timestamp: {value!r}")
    hours = int(m.group(1) or 0)
    frac = m.group(4)
    return hours * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + int(frac) / 10 ** len(frac)


def parse_subtitles(text: str) -> list[Cue]:
    """Parse .vtt or .srt text.

    YouTube auto-captions repeat the previous line inside each new cue ("rolling"
    captions). We keep only the new words so every cue appears once.
    """
    cues: list[Cue] = []
    previous = ""
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n")):
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        arrow = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if arrow is None:
            continue
        left, right = lines[arrow].split("-->", 1)
        start, end = parse_ts(left), parse_ts(right)
        full = html.unescape(re.sub(r"<[^>]+>", "", " ".join(lines[arrow + 1:])))
        full = re.sub(r"\s+", " ", full).strip()
        if not full or full == previous:
            continue
        if previous and full.startswith(previous):
            new = full[len(previous):].strip()
        else:
            new = full
        previous = full
        if new:
            cues.append(Cue(start, end, new))
    return cues


def window(cues: list[Cue], start: float, end: float) -> list[Cue]:
    """Return the cues that overlap [start, end], with times shifted to start at 0."""
    out: list[Cue] = []
    for c in cues:
        if c.end <= start or c.start >= end:
            continue
        out.append(Cue(max(c.start, start) - start, min(c.end, end) - start, c.text))
    return out


def ass_header(font: str) -> str:
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{font},60,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,4,1,2,80,80,320,1
Style: Hook,{font},72,&H0000FFFF,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,100,100,0,0,1,5,1,8,70,70,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ass_time(seconds: float) -> str:
    cs = int(round(seconds * 100))
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    s, cs = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _ass_text(text: str) -> str:
    return text.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ")


def write_ass(path: str, cues: list[Cue], hook: str | None = None,
              font: str = "Arial", hook_seconds: float = 4.0) -> None:
    """Write an ASS subtitle file: a top hook title plus bottom captions."""
    lines = [ass_header(font)]
    if hook:
        lines.append(
            f"Dialogue: 0,{_ass_time(0)},{_ass_time(hook_seconds)},Hook,,0,0,0,,{_ass_text(hook)}\n"
        )
    for c in cues:
        lines.append(
            f"Dialogue: 0,{_ass_time(c.start)},{_ass_time(c.end)},Caption,,0,0,0,,{_ass_text(c.text)}\n"
        )
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
