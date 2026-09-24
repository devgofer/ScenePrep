from scene_prep.subtitle import vtt_to_srt


def test_vtt_to_srt():
    vtt = """WEBVTT

00:00:01.000 --> 00:00:03.500
Hello!

00:00:04.000 --> 00:00:06.250 align:start
How are you?
"""
    assert vtt_to_srt(vtt) == (
        "1\n00:00:01,000 --> 00:00:03,500\nHello!\n\n"
        "2\n00:00:04,000 --> 00:00:06,250\nHow are you?\n"
    )
