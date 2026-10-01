from scene_prep.hls import HLSClient, SubtitleTrack


def test_choose_exact_language():
    tracks = [
        SubtitleTrack("English (US)", "en-US", "https://example.com/us.m3u8"),
        SubtitleTrack("English", "en", "https://example.com/en.m3u8"),
        SubtitleTrack("Japanese", "ja", "https://example.com/ja.m3u8"),
    ]
    assert HLSClient.choose_track(tracks, "en").language == "en"


def test_choose_language_prefix():
    tracks = [
        SubtitleTrack("English (US)", "en-US", "https://example.com/us.m3u8"),
        SubtitleTrack("Japanese", "ja", "https://example.com/ja.m3u8"),
    ]
    assert HLSClient.choose_track(tracks, "en").language == "en-US"


def test_choose_single_track_without_lang_match():
    tracks = [SubtitleTrack("Only Track", None, "https://example.com/direct.m3u8")]
    assert HLSClient.choose_track(tracks, "ja").uri == "https://example.com/direct.m3u8"


def test_direct_subtitle_playlist_is_detected():
    client = HLSClient()
    client._get_text = lambda *_args, **_kwargs: (
        "#EXTM3U\n"
        "#EXT-X-TARGETDURATION:10\n"
        "#EXTINF:10,\n"
        "seg0.vtt\n"
        "#EXT-X-ENDLIST\n"
    )
    tracks = client.list_subtitle_tracks(
        "https://example.com/P1497354115_A6807598094_en_subtitles_V2-.m3u8"
    )
    assert len(tracks) == 1
    assert tracks[0].name == "Direct subtitle playlist"
    assert tracks[0].language == "en"


class _Response:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def raise_for_status(self) -> None:
        return None


def test_download_webvtt_with_byterange_uses_range_header():
    requests: list[tuple[str, dict[str, str] | None]] = []
    client = HLSClient()

    def fake_get(url: str, timeout: float, headers: dict[str, str] | None = None):
        requests.append((url, headers))
        if url.endswith(".m3u8"):
            return _Response(
                (
                    b"#EXTM3U\n"
                    b"#EXTINF:30,\n"
                    b"#EXT-X-BYTERANGE:12@5\n"
                    b"https://example.com/segment.vtt\n"
                    b"#EXT-X-ENDLIST\n"
                )
            )
        return _Response(b"WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHello\n")

    client.session.get = fake_get
    output = client.download_webvtt(
        SubtitleTrack("English", "en", "https://example.com/subtitle.m3u8")
    )
    assert "Hello" in output
    assert requests[1][1] == {"Range": "bytes=5-16"}
