from scene_prep.cookies import load_netscape_cookies


def test_load_netscape_cookies(tmp_path):
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text(
        "# Netscape HTTP Cookie File\n"
        ".apple.com\tTRUE\t/\tTRUE\t0\tmedia-user-token\tabc123\n"
        "#HttpOnly_.apple.com\tTRUE\t/\tTRUE\t0\tsessionid\txyz789\n",
        encoding="utf-8",
    )

    cookies = load_netscape_cookies(str(cookie_file))
    assert cookies == {"media-user-token": "abc123", "sessionid": "xyz789"}
