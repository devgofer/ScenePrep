from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse


APPLE_TV_HOSTS = {"tv.apple.com"}


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

    This provider intentionally does not bypass DRM, FairPlay, authentication,
    encryption, or other access controls. It parses episode metadata from the
    public URL and provides a clear hand-off for an authorized subtitle source.
    """

    def resolve_subtitle_url(self, episode: AppleTVEpisode) -> str:
        raise NotImplementedError(
            "Apple TV does not expose a public subtitle playlist in the episode "
            "page URL. ScenePrep cannot bypass DRM or access controls. "
            "Provide an authorized unencrypted subtitle/HLS URL or subtitle file."
        )
