from clipper.subtitles import Cue, parse_subtitles, parse_ts, window, write_ass

VTT = """WEBVTT
Kind: captions
Language: en

00:00:01.000 --> 00:00:03.000 align:start position:0%
hello there

00:00:03.000 --> 00:00:05.000 align:start position:0%
hello there <00:00:03.500><c>friends</c>

00:00:05.000 --> 00:00:07.500
friends
how are you
"""

SRT = """1
00:00:01,000 --> 00:00:02,500
namaste doston

2
00:00:02,500 --> 00:00:04,000
aaj hum baat karenge
"""


def test_parse_ts_handles_hours_and_commas():
    assert abs(parse_ts("00:01:02.345") - 62.345) < 1e-6
    assert abs(parse_ts("01:02,5") - 62.5) < 1e-6


def test_vtt_rolling_captions_are_deduplicated():
    cues = parse_subtitles(VTT)
    texts = [c.text for c in cues]
    assert texts[0] == "hello there"
    assert texts[1] == "friends"
    assert len(cues) == 3


def test_srt_is_parsed():
    cues = parse_subtitles(SRT)
    assert [c.text for c in cues] == ["namaste doston", "aaj hum baat karenge"]
    assert cues[1].start == 2.5


def test_window_shifts_and_clips_times():
    cues = [Cue(0, 5, "a"), Cue(10, 12, "b")]
    assert window(cues, 4, 11) == [Cue(0.0, 1.0, "a"), Cue(6.0, 7.0, "b")]


def test_write_ass_formats_times(tmp_path):
    path = tmp_path / "x.ass"
    write_ass(str(path), [Cue(1.0, 2.5, "hi")], hook="Wow", font="Arial")
    content = path.read_text(encoding="utf-8")
    assert "Dialogue: 0,0:00:00.00,0:00:04.00,Hook,,0,0,0,,Wow" in content
    assert "Dialogue: 0,0:00:01.00,0:00:02.50,Caption,,0,0,0,,hi" in content


def test_picks_are_validated():
    from clipper.analyze import picks_from_json
    data = {"clips": [
        {"start": 10, "end": 40, "score": 90, "title": "a"},
        {"start": 20, "end": 50, "score": 80},          # overlaps the first, dropped
        {"start": 100, "end": 105, "score": 99},        # too short, dropped
        {"end": 30, "score": 99},                        # no start, dropped
        {"start": 200, "end": 400, "score": 70},        # clipped to max_len and duration
    ]}
    picks = picks_from_json(data, duration=230, n=5, min_len=20, max_len=60)
    assert [(p.start, p.end) for p in picks] == [(10, 40), (200, 230)]
