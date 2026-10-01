from __future__ import annotations

from io import BytesIO
from pathlib import Path
from urllib.parse import urlencode

from scene_prep.service import SubtitleJobResult
from scene_prep.web import app


def _call_app(method: str = "GET", form: dict[str, str] | None = None) -> tuple[str, list[tuple[str, str]], bytes]:
    payload = urlencode(form or {}).encode("utf-8")
    status_holder: list[str] = []
    headers_holder: list[list[tuple[str, str]]] = []

    def _start_response(status, headers):  # type: ignore[no-untyped-def]
        status_holder.append(status)
        headers_holder.append(headers)

    environ = {
        "REQUEST_METHOD": method,
        "CONTENT_LENGTH": str(len(payload)),
        "wsgi.input": BytesIO(payload),
    }
    body = b"".join(app(environ, _start_response))
    return status_holder[0], headers_holder[0], body


def test_get_renders_form():
    status, headers, body = _call_app("GET")
    assert status == "200 OK"
    assert any(h[0] == "Content-Type" and "text/html" in h[1] for h in headers)
    assert "ScenePrep".encode("utf-8") in body


def test_post_display_mode_renders_srt(monkeypatch, tmp_path: Path):
    srt = tmp_path / "demo.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n", encoding="utf-8")
    monkeypatch.setattr(
        "scene_prep.web.generate_subtitles",
        lambda **_kwargs: SubtitleJobResult(selected_track="English / en", outputs=(str(srt),)),
    )
    status, headers, body = _call_app(
        "POST",
        {"url": "https://example.com/sub.m3u8", "fmt": "srt", "srt_action": "display"},
    )
    assert status == "200 OK"
    assert any(h[0] == "Content-Type" and "text/html" in h[1] for h in headers)
    assert b"SRT" in body
    assert b"Hello" in body


def test_post_download_mode_returns_attachment(monkeypatch, tmp_path: Path):
    srt = tmp_path / "dl.srt"
    srt.write_text("1\n00:00:00,000 --> 00:00:01,000\nHi\n", encoding="utf-8")
    monkeypatch.setattr(
        "scene_prep.web.generate_subtitles",
        lambda **_kwargs: SubtitleJobResult(selected_track="English / en", outputs=(str(srt),)),
    )
    status, headers, body = _call_app(
        "POST",
        {"url": "https://example.com/sub.m3u8", "fmt": "srt", "srt_action": "download"},
    )
    assert status == "200 OK"
    assert any(h[0] == "Content-Disposition" and "attachment" in h[1] for h in headers)
    assert body.startswith(b"1\n00:00:00,000")
