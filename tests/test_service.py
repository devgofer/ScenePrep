from scene_prep.service import dual_output_paths, generate_subtitles


def test_dual_output_paths():
    assert dual_output_paths(None) == ("subtitle.srt", "subtitle.txt")
    assert dual_output_paths("episode.en.srt") == ("episode.en.srt", "episode.en.txt")
    assert dual_output_paths("episode.en") == ("episode.srt", "episode.txt")


def test_generate_subtitles_both(monkeypatch):
    writes = []

    class _Track:
        label = "English / en"

    class _Client:
        def __init__(self, **_kwargs):
            return None

        def list_subtitle_tracks(self, _url):
            return [_Track()]

        def choose_track(self, tracks, _lang):
            return tracks[0]

        def download_webvtt(self, _track):
            return "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHello\n"

    monkeypatch.setattr("scene_prep.service.resolve_source_url", lambda **_kwargs: ("https://example.com/sub.m3u8", None))
    monkeypatch.setattr("scene_prep.service.HLSClient", _Client)
    monkeypatch.setattr("scene_prep.service.save_subtitle", lambda vtt, path, fmt: writes.append((path, fmt, vtt)))

    result = generate_subtitles(url="https://example.com/master.m3u8", fmt="both", output="lesson")

    assert result.selected_track == "English / en"
    assert result.outputs == ("lesson.srt", "lesson.txt")
    assert [x[1] for x in writes] == ["srt", "txt"]


def test_generate_subtitles_single_format(monkeypatch):
    writes = []

    class _Track:
        label = "English / en"

    class _Client:
        def __init__(self, **_kwargs):
            return None

        def list_subtitle_tracks(self, _url):
            return [_Track()]

        def choose_track(self, tracks, _lang):
            return tracks[0]

        def download_webvtt(self, _track):
            return "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHello\n"

    monkeypatch.setattr("scene_prep.service.resolve_source_url", lambda **_kwargs: ("https://example.com/sub.m3u8", None))
    monkeypatch.setattr("scene_prep.service.HLSClient", _Client)
    monkeypatch.setattr("scene_prep.service.save_subtitle", lambda vtt, path, fmt: writes.append((path, fmt, vtt)))

    result = generate_subtitles(url="https://example.com/master.m3u8", fmt="vtt")

    assert result.outputs == ("subtitle.vtt",)
    assert writes[0][1] == "vtt"
