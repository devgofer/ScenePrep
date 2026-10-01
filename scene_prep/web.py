from __future__ import annotations

import argparse
import html
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from .service import generate_subtitles


def _field(data: dict[str, list[str]], key: str, default: str = "") -> str:
    return data.get(key, [default])[0].strip()


def _render_page(
    message: str = "",
    error: str = "",
    values: dict[str, str] | None = None,
    srt_preview: str = "",
) -> str:
    values = values or {}
    msg_html = f"<p style='color:#0a0'>{html.escape(message)}</p>" if message else ""
    err_html = f"<p style='color:#b00'>{html.escape(error)}</p>" if error else ""
    preview_html = (
        "<h2>SRT 預覽</h2><pre style='white-space:pre-wrap;background:#f6f8fa;padding:12px;border-radius:8px;'>"
        f"{html.escape(srt_preview)}</pre>"
    ) if srt_preview else ""
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>ScenePrep Web UI</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 860px; margin: 30px auto; padding: 0 16px; }}
    label {{ display: block; font-weight: 600; margin-top: 12px; }}
    input, select {{ width: 100%; box-sizing: border-box; margin-top: 6px; padding: 8px; }}
    button {{ margin-top: 16px; padding: 10px 16px; }}
    .hint {{ color: #666; font-size: 14px; }}
  </style>
</head>
<body>
  <h1>ScenePrep 字幕擷取</h1>
  <p class="hint">輸入 Apple TV 網址或授權的 m3u8 字幕來源，會在目前目錄輸出字幕檔。</p>
  {msg_html}
  {err_html}
  <form method="post">
    <label>URL</label>
    <input name="url" required value="{html.escape(values.get("url", ""))}" />

    <label>Language</label>
    <input name="lang" value="{html.escape(values.get("lang", "en"))}" />

    <label>Format</label>
    <select name="fmt">
      <option value="both"{" selected" if values.get("fmt", "both") == "both" else ""}>both (srt + txt)</option>
      <option value="srt"{" selected" if values.get("fmt") == "srt" else ""}>srt</option>
      <option value="vtt"{" selected" if values.get("fmt") == "vtt" else ""}>vtt</option>
    </select>

    <label>SRT action</label>
    <select name="srt_action">
      <option value="display"{" selected" if values.get("srt_action", "display") == "display" else ""}>顯示 SRT 在畫面</option>
      <option value="download"{" selected" if values.get("srt_action") == "download" else ""}>下載 SRT 檔案</option>
    </select>

    <label>Output basename/path (optional)</label>
    <input name="output" value="{html.escape(values.get("output", ""))}" />

    <label>Cookies file path (optional)</label>
    <input name="cookies_file" value="{html.escape(values.get("cookies_file", ""))}" />

    <label>Subtitle URL fallback (optional)</label>
    <input name="subtitle_url" value="{html.escape(values.get("subtitle_url", ""))}" />

    <label>User-Agent</label>
    <input name="user_agent" value="{html.escape(values.get("user_agent", "ScenePrep/0.1"))}" />

    <button type="submit">開始擷取</button>
  </form>
  {preview_html}
</body>
</html>"""


def app(environ, start_response):  # type: ignore[no-untyped-def]
    method = environ.get("REQUEST_METHOD", "GET").upper()
    if method == "POST":
        size = int(environ.get("CONTENT_LENGTH") or "0")
        raw = environ["wsgi.input"].read(size).decode("utf-8", errors="replace")
        form = parse_qs(raw, keep_blank_values=True)
        values = {k: _field(form, k) for k in form}

        try:
            result = generate_subtitles(
                url=values.get("url", ""),
                lang=values.get("lang", "en"),
                fmt=values.get("fmt", "both"),
                output=values.get("output") or None,
                cookies_file=values.get("cookies_file") or None,
                subtitle_url=values.get("subtitle_url") or None,
                user_agent=values.get("user_agent", "ScenePrep/0.1"),
            )
            srt_file = next((x for x in result.outputs if x.endswith(".srt")), "")
            if values.get("srt_action", "display") == "download" and srt_file:
                payload = Path(srt_file).read_bytes()
                filename = Path(srt_file).name
                start_response(
                    "200 OK",
                    [
                        ("Content-Type", "application/x-subrip; charset=utf-8"),
                        ("Content-Disposition", f'attachment; filename="{filename}"'),
                        ("Content-Length", str(len(payload))),
                    ],
                )
                return [payload]

            message = f"完成，選到 {result.selected_track}；輸出：{', '.join(result.outputs)}"
            preview = Path(srt_file).read_text(encoding="utf-8") if srt_file else ""
            body = _render_page(message=message, values=values, srt_preview=preview)
        except Exception as exc:
            body = _render_page(error=f"失敗：{exc}", values=values)
    else:
        body = _render_page()

    payload = body.encode("utf-8")
    start_response(
        "200 OK",
        [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(payload)))],
    )
    return [payload]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ScenePrep local web UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    with make_server(args.host, args.port, app) as server:
        print(f"ScenePrep Web UI running at http://{args.host}:{args.port}")
        print("Press Ctrl+C to stop.")
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
