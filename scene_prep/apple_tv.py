from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import parse_qs, urlparse

import requests


APPLE_TV_HOSTS = {"tv.apple.com"}
M3U8_URL_RE = re.compile(r"https?://[^\"'\s<>]+\.m3u8[^\"'\s<>]*")
M3U8_ESCAPED_RE = re.compile(r"https?:\\\\/\\\\/[^\"'\s<>]+\.m3u8[^\"'\s<>]*")


@dataclass(frozen=True)
class AppleTVEpisode:
    url: str
    episode_id: str
    show_id: str | None = None
    playable_id: str | None = None

    @property
    def provider(self) -> str:
        return "apple_tv"


def parse_apple_tv_episode(url: str) -> AppleTVEpisode:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in APPLE_TV_HOSTS:
        raise ValueError("Not an Apple TV URL.")

    parts = [part for part in parsed.path.split("/") if part]
    try:
        episode_index = parts.index("episode")
        episode_id = parts[episode_index + 2] if parts[episode_index + 1] else ""
    except (ValueError, IndexError):
        raise ValueError(
            "Apple TV URL must be an episode URL such as "
            "https://tv.apple.com/tw/episode/.../umc.cmc...."
        ) from None

    if not episode_id:
        raise ValueError("Could not find the Apple TV episode ID.")

    query = parse_qs(parsed.query)
    return AppleTVEpisode(
        url=url,
        episode_id=episode_id,
        show_id=query.get("showId", [None])[0],
        playable_id=query.get("playableId", [None])[0],
    )


class AppleTVSubtitleProvider:
    """
    Apple TV URL adapter.

    This provider intentionally does not bypass DRM, FairPlay, authentication, or
    access controls. It only uses authorized responses available to the signed-in
    user and supports manual hand-off when direct subtitle URLs are provided.
    """

    def __init__(
        self,
        *,
        timeout: float = 20.0,
        user_agent: str = "ScenePrep/0.1",
        cookies: dict[str, str] | None = None,
    ) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        if cookies:
            self.session.cookies.update(cookies)

    def _get_text(self, url: str) -> str:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    @staticmethod
    def _score_candidate(url: str) -> tuple[int, int, int]:
        lower = url.lower()
        subtitle_hint = int("subtitle" in lower or "cc" in lower or "vtt" in lower)
        https_hint = int(lower.startswith("https://"))
        return subtitle_hint, https_hint, -len(url)

    def _extract_hls_candidates(self, html: str) -> list[str]:
        candidates = set(M3U8_URL_RE.findall(html))
        for match in M3U8_ESCAPED_RE.findall(html):
            candidates.add(match.replace("\\/", "/"))
        return sorted(candidates, key=self._score_candidate, reverse=True)

    def resolve_subtitle_url(
        self,
        episode: AppleTVEpisode,
        *,
        fallback_subtitle_url: str | None = None,
    ) -> str:
        candidates = self._extract_hls_candidates(self._get_text(episode.url))
        if candidates:
            return candidates[0]
        if fallback_subtitle_url:
            return fallback_subtitle_url
        raise ValueError(
            "Could not find an authorized HLS subtitle source from the Apple TV "
            "episode page. Provide --cookies-file for your signed-in session or "
            "--subtitle-url with an authorized subtitle/master playlist URL."
        )
