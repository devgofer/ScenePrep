from __future__ import annotations


def load_netscape_cookies(path: str) -> dict[str, str]:
    cookies: dict[str, str] = {}
    with open(path, encoding="utf-8") as file:
        for line in file:
            text = line.strip()
            if not text:
                continue
            if text.startswith("#HttpOnly_"):
                text = text[len("#HttpOnly_"):]
            elif text.startswith("#"):
                continue

            parts = text.split("\t")
            if len(parts) < 7:
                continue
            name = parts[5].strip()
            value = parts[6].strip()
            if name:
                cookies[name] = value

    if not cookies:
        raise ValueError(f"No cookies found in '{path}'.")
    return cookies
