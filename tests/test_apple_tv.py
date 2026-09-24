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


def test_provider_requires_authorized_source():
    episode = parse_apple_tv_episode(URL)
    provider = AppleTVSubtitleProvider()

    with pytest.raises(ValueError, match="No authorized subtitle source"):
        provider.resolve_subtitle_url(episode)


def test_provider_accepts_authorized_source():
    episode = parse_apple_tv_episode(URL)
    provider = AppleTVSubtitleProvider()

    assert (
        provider.resolve_subtitle_url(
            episode,
            authorized_subtitle_url="https://example.com/subtitles/master.m3u8",
        )
        == "https://example.com/subtitles/master.m3u8"
    )


def test_provider_rejects_invalid_source():
    episode = parse_apple_tv_episode(URL)
    provider = AppleTVSubtitleProvider()

    with pytest.raises(ValueError, match="HTTP"):
        provider.resolve_subtitle_url(
            episode,
            authorized_subtitle_url="file:///tmp/subtitles.m3u8",
        )
