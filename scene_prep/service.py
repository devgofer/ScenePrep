from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .apple_tv import AppleTVSubtitleProvider, parse_apple_tv_episode
from .cookies import load_netscape_cookies
from .hls import HLSClient
from .subtitle import save_subtitle


@dataclass(frozen=True)
class SubtitleJobResult:
    selected_track: str
    outputs: tuple[str, ...]


def dual_output_paths(value: str | None) -> tuple[str, str]:
    if not value:
        return "subtitle.srt", "subtitle.txt"
    path = Path(value)
    base = path.with_suffix("") if path.suffix else path
    return f"{base}.srt", f"{base}.txt"


def generate_subtitles(
    *,
    url: str,
    lang: str = "en",
    fmt: str = "both",
    output: str | None = None,
    cookies_file: str | None = None,
    subtitle_url: str | None = None,
    user_agent: str = "ScenePrep/0.1",
) -> SubtitleJobResult:
    source_url, cookies = resolve_source_url(
        url=url,
        cookies_file=cookies_file,
        subtitle_url=subtitle_url,
        user_agent=user_agent,
    )
    client = HLSClient(user_agent=user_agent, cookies=cookies)
    tracks = client.list_subtitle_tracks(source_url)
    track = client.choose_track(tracks, lang)
    vtt = client.download_webvtt(track)

    if fmt == "both":
        srt_path, txt_path = dual_output_paths(output)
        save_subtitle(vtt, srt_path, "srt")
        save_subtitle(vtt, txt_path, "txt")
        outputs = (srt_path, txt_path)
    else:
        output_path = output or f"subtitle.{fmt}"
        save_subtitle(vtt, output_path, fmt)
        outputs = (output_path,)

    return SubtitleJobResult(selected_track=track.label, outputs=outputs)


def resolve_source_url(
    *,
    url: str,
    cookies_file: str | None = None,
    subtitle_url: str | None = None,
    user_agent: str = "ScenePrep/0.1",
) -> tuple[str, dict[str, str] | None]:
    cookies = load_netscape_cookies(cookies_file) if cookies_file else None
    source_url = url
    if url.startswith(("https://tv.apple.com/", "http://tv.apple.com/")):
        episode = parse_apple_tv_episode(url)
        source_url = AppleTVSubtitleProvider(
            user_agent=user_agent,
            cookies=cookies,
        ).resolve_subtitle_url(
            episode,
            fallback_subtitle_url=subtitle_url,
        )
    return source_url, cookies
