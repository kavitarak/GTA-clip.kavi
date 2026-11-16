from __future__ import annotations

import json
import os
from dataclasses import dataclass

import httpx

from .subtitles import Cue

DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-5-5",
    "ollama": "llama3.1",
}

PROMPT = """You are an expert short-form video editor (YouTube Shorts, Instagram Reels, TikTok).
Below is the transcript of a long video. Each line is [start-end seconds] text.

Pick the {n} most engaging, self-contained moments that work as standalone vertical clips.

Rules:
- Each clip must last between {min_len} and {max_len} seconds.
- Start on a strong opening line and end on a complete thought.
- Clips must not overlap.
- Write "title" and "hook" in the same language the speaker uses (Hindi, Hinglish or English).
- "hook" is a short on-screen line, at most 8 words.
- Return ONLY valid JSON in this exact shape, with no other text:
{{"clips": [{{"start": 12.5, "end": 48.0, "title": "...", "hook": "...", "score": 85, "reason": "..."}}]}}

Transcript:
{transcript}
"""


@dataclass
class ClipPick:
    start: float
    end: float
    title: str
    hook: str
    score: float
    reason: str


def build_prompt(cues: list[Cue], n: int, min_len: float, max_len: float) -> str:
    transcript = "\n".join(f"[{c.start:.1f}-{c.end:.1f}] {c.text}" for c in cues)
    return PROMPT.format(n=n, min_len=int(min_len), max_len=int(max_len), transcript=transcript)


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Set the {name} environment variable first.")
    return value


def ask_llm(provider: str, model: str | None, prompt: str, timeout: float = 180.0) -> str:
    model = model or DEFAULT_MODELS[provider]
    message = [{"role": "user", "content": prompt}]

    if provider == "gemini":
        r = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": _env("GEMINI_API_KEY")},
            json={"contents": [{"parts": [{"text": prompt}]}],
                  "generationConfig": {"responseMimeType": "application/json"}},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]

    if provider == "openai":
        r = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {_env('OPENAI_API_KEY')}"},
            json={"model": model, "messages": message,
                  "response_format": {"type": "json_object"}},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    if provider == "anthropic":
        r = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": _env("ANTHROPIC_API_KEY"), "anthropic-version": "2023-06-01"},
            json={"model": model, "max_tokens": 4096, "messages": message},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"]

    if provider == "ollama":
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        r = httpx.post(
            f"{host}/api/chat",
            json={"model": model, "messages": message, "stream": False, "format": "json"},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json()["message"]["content"]

    raise ValueError(f"unknown provider: {provider}")


def extract_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("The model did not return JSON.")
    return json.loads(text[start:end + 1])


def _num(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def validate_picks(items, duration: float, n: int, min_len: float,
                   max_len: float) -> list[ClipPick]:
    """Turn untrusted clip dicts (from an LLM or a picks file) into safe, non-overlapping picks."""
    picks: list[ClipPick] = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        start = _num(item.get("start"), -1.0)
        end = _num(item.get("end"), -1.0)
        if duration:
            end = min(end, duration)
        if start < 0 or end <= start:
            continue
        if end - start > max_len:
            end = start + max_len
        if end - start < min_len:
            continue
        picks.append(ClipPick(
            start=start,
            end=end,
            title=str(item.get("title") or "clip"),
            hook=str(item.get("hook") or ""),
            score=_num(item.get("score")),
            reason=str(item.get("reason") or ""),
        ))

    picks.sort(key=lambda p: p.score, reverse=True)
    chosen: list[ClipPick] = []
    for p in picks:
        if all(p.end <= c.start or p.start >= c.end for c in chosen):
            chosen.append(p)
        if len(chosen) == n:
            break
    return chosen


def picks_from_json(data, duration: float, n: int, min_len: float, max_len: float) -> list[ClipPick]:
    items = data.get("clips", []) if isinstance(data, dict) else data
    return validate_picks(items, duration, n, min_len, max_len)


def pick_clips(cues: list[Cue], duration: float, n: int, min_len: float, max_len: float,
               provider: str, model: str | None = None) -> list[ClipPick]:
    raw = ask_llm(provider, model, build_prompt(cues, n, min_len, max_len))
    return picks_from_json(extract_json(raw), duration, n, min_len, max_len)
