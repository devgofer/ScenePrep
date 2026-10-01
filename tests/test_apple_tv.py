from __future__ import annotations

import pytest

from scene_prep.apple_tv import AppleTVSubtitleProvider, parse_apple_tv_episode


URL = (
    "https://tv.apple.com/tw/episode/%E8%A9%A6%E6%92%AD%E9%9B%86/"
    "umc.cmc.zb0yksqtym68hasbq8mj4jwp"
    "?showId=umc.cmc.vtoh0mn0xn7t3c643xqonfzy"
    "&playableId=tvs.sbd.4000%3AVTEDL0560101"
)


def test_parse_apple_tv_episode():
    episode = parse_apple_tv_episode(URL)

    assert episode.episode_id == "umc.cmc.zb0yksqtym68hasbq8mj4jwp"
    assert episode.show_id == "umc.cmc.vtoh0mn0xn7t3c643xqonfzy"
    assert episode.playable_id == "tvs.sbd.4000:VTEDL0560101"


def test_reject_non_apple_tv_url():
    with pytest.raises(ValueError, match="Not an Apple TV URL"):
        parse_apple_tv_episode("https://example.com/episode/123")


class _Response:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


def test_provider_resolves_hls_from_episode_page():
    episode = parse_apple_tv_episode(URL)
    provider = AppleTVSubtitleProvider()
    provider.session.get = lambda *_args, **_kwargs: _Response(
        '<script>const x = "https://example.com/subtitles/en/main.m3u8";</script>'
    )

    resolved = provider.resolve_subtitle_url(episode)
    assert resolved == "https://example.com/subtitles/en/main.m3u8"


def test_provider_uses_fallback_when_page_has_no_hls():
    episode = parse_apple_tv_episode(URL)
    provider = AppleTVSubtitleProvider()
    provider.session.get = lambda *_args, **_kwargs: _Response("<html></html>")

    resolved = provider.resolve_subtitle_url(
        episode,
        fallback_subtitle_url="https://fallback.example.com/master.m3u8",
    )
    assert resolved == "https://fallback.example.com/master.m3u8"


def test_provider_requires_authorized_source():
    episode = parse_apple_tv_episode(URL)
    provider = AppleTVSubtitleProvider()
    provider.session.get = lambda *_args, **_kwargs: _Response("<html></html>")

    with pytest.raises(ValueError, match="Could not find an authorized HLS subtitle source"):
        provider.resolve_subtitle_url(episode)
