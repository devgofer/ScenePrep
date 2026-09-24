from __future__ import annotations

import re

TIMESTAMP_RE = re.compile(
    r"(?P<hours>\d{2}):(?P<minutes>\d{2}):(?P<seconds>\d{2})[\\.,](?P<millis>\d{3})"
)


def _timestamp(value: str) -> str:
    match = TIMESTAMP_RE.fullmatch(value.strip())
    if not match:
        raise ValueError(f"Invalid subtitle timestamp: {value}")
    return (
        f"{match.group('hours')}:{match.group('minutes')}:"
        f"{match.group('seconds')},{match.group('millis')}"
    )


def vtt_to_srt(vtt: str) -> str:
    lines = vtt.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    cues: list[tuple[str, str]] = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if not line or line == "WEBVTT" or line.startswith("WEBVTT "):
            i += 1
            continue

        if line.startswith(("NOTE", "STYLE", "REGION")):
            i += 1
            while i < len(lines) and lines[i].strip():
                i += 1
            continue

        timestamp_line = line
        if "-->" not in timestamp_line and i + 1 < len(lines) and "-->" in lines[i + 1]:
            i += 1
            timestamp_line = lines[i].strip()

        if "-->" not in timestamp_line:
            i += 1
            continue

        start, end_and_settings = timestamp_line.split("-->", 1)
        end = end_and_settings.strip().split()[0]
        i += 1

        text_lines: list[str] = []
        while i < len(lines) and lines[i].strip():
            text_lines.append(lines[i])
            i += 1

        cues.append((f"{_timestamp(start)} --> {_timestamp(end)}", "\n".join(text_lines)))
        i += 1

    output: list[str] = []
    for number, (timing, text) in enumerate(cues, start=1):
        output.extend([str(number), timing, text, ""])
    return "\n".join(output)


def save_subtitle(vtt: str, output_path: str, fmt: str = "vtt") -> None:
    fmt = fmt.lower()
    if fmt not in {"vtt", "srt"}:
        raise ValueError("Format must be 'vtt' or 'srt'.")
    content = vtt if fmt == "vtt" else vtt_to_srt(vtt)
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(content)
