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
