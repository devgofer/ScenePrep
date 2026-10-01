from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

import m3u8
import requests


@dataclass(frozen=True)
class SubtitleTrack:
    name: str
    language: str | None
    uri: str
    is_default: bool = False
    is_autoselect: bool = False
    is_forced: bool = False
    characteristics: str | None = None

    @property
    def label(self) -> str:
        parts = [self.name or "Unnamed"]
        if self.language:
            parts.append(self.language)
        if self.is_forced:
            parts.append("forced")
        return " / ".join(parts)


class HLSClient:
    def __init__(self, *, timeout: float = 20.0,
                 user_agent: str = "ScenePrep/0.1",
                 cookies: dict[str, str] | None = None) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        if cookies:
            self.session.cookies.update(cookies)

    def _get_text(self, url: str, *, headers: dict[str, str] | None = None) -> str:
        response = self.session.get(url, timeout=self.timeout, headers=headers)
        response.raise_for_status()
        return response.content.decode("utf-8-sig", errors="replace")

    def list_subtitle_tracks(self, url: str) -> list[SubtitleTrack]:
        playlist = m3u8.loads(self._get_text(url))
        if playlist.segments and not playlist.media:
            language = self._guess_language_from_uri(url)
            return [SubtitleTrack(
                name="Direct subtitle playlist",
                language=language,
                uri=url,
                is_default=True,
            )]

        tracks: list[SubtitleTrack] = []
        for media in playlist.media:
            if media.type != "SUBTITLES" or not media.uri:
                continue
            tracks.append(SubtitleTrack(
                name=media.name or "",
                language=media.language,
                uri=urljoin(url, media.uri),
                is_default=bool(media.default),
                is_autoselect=bool(media.autoselect),
                is_forced=bool(media.forced),
                characteristics=media.characteristics,
            ))
        return tracks

    @staticmethod
    def choose_track(tracks: list[SubtitleTrack], language: str = "en") -> SubtitleTrack:
        if not tracks:
            raise ValueError("No HLS subtitle tracks were found.")
        if len(tracks) == 1:
            return tracks[0]

        requested = language.lower().replace("_", "-")

        def score(track: SubtitleTrack) -> tuple[int, int, int]:
            lang = (track.language or "").lower().replace("_", "-")
            name = track.name.lower()
            exact = int(lang == requested)
            prefix = int(bool(lang) and (
                lang.startswith(requested + "-") or requested.startswith(lang + "-")
            ))
            english_name = int(requested.startswith("en") and "english" in name)
            return exact, prefix, english_name

        ranked = sorted(tracks, key=score, reverse=True)
        if score(ranked[0]) == (0, 0, 0):
            raise ValueError(
                f"No subtitle track matched language '{language}'. "
                "Use --list to inspect available tracks."
            )
        return ranked[0]

    @staticmethod
    def _guess_language_from_uri(uri: str) -> str | None:
        tokens = [
            "_subtitles_",
            "-subtitles-",
            ".subtitles.",
            "_subs_",
            "-subs-",
            ".subs.",
        ]
        lower = uri.lower()
        for marker in tokens:
            if marker in lower:
                prefix = lower.split(marker, 1)[0]
                last = prefix.rsplit("_", 1)[-1].rsplit("-", 1)[-1]
                if last and len(last) <= 10:
                    return last
        return None

    def download_webvtt(self, track: SubtitleTrack) -> str:
        playlist = m3u8.loads(self._get_text(track.uri))
        if not playlist.segments:
            raise ValueError("The subtitle playlist contains no segments.")

        merged: list[str] = ["WEBVTT", ""]
        for index, segment in enumerate(playlist.segments, start=1):
            segment_url = urljoin(track.uri, segment.uri)
            headers: dict[str, str] | None = None
            if getattr(segment, "byterange", None):
                length, _, offset = segment.byterange.partition("@")
                if not length.isdigit():
                    raise ValueError(f"Subtitle segment {index} has invalid BYTERANGE.")
                start = int(offset) if offset.isdigit() else 0
                end = start + int(length) - 1
                headers = {"Range": f"bytes={start}-{end}"}

            text = self._get_text(segment_url, headers=headers).lstrip("\ufeff")
            if not text.lstrip().startswith("WEBVTT"):
                raise ValueError(f"Subtitle segment {index} is not WebVTT.")

            body = text.split("\n", 1)[1] if "\n" in text else ""
            body = body.strip()
            if body:
                merged.extend([f"NOTE ScenePrep segment {index}", body, ""])

        return "\n".join(merged).rstrip() + "\n"
