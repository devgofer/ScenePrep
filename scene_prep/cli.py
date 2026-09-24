from __future__ import annotations

import argparse
import sys

from .apple_tv import AppleTVSubtitleProvider, parse_apple_tv_episode
from .hls import HLSClient
from .subtitle import save_subtitle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download legally accessible HLS WebVTT subtitles."
    )
    parser.add_argument(
        "url",
        help="Authorized HLS .m3u8 URL or Apple TV episode URL.",
    )
    parser.add_argument("--lang", default="en", help="Subtitle language (default: en).")
    parser.add_argument("--format", choices=("vtt", "srt"), default="srt")
    parser.add_argument("-o", "--output", help="Output file path.")
    parser.add_argument("--list", action="store_true", help="List subtitle tracks and exit.")
    parser.add_argument("--user-agent", default="ScenePrep/0.1")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        if args.url.startswith(("https://tv.apple.com/", "http://tv.apple.com/")):
            episode = parse_apple_tv_episode(args.url)
            AppleTVSubtitleProvider().resolve_subtitle_url(episode)

        client = HLSClient(user_agent=args.user_agent)
        tracks = client.list_subtitle_tracks(args.url)

        if args.list:
            if not tracks:
                print("No subtitle tracks found.")
                return 0
            for index, track in enumerate(tracks, 1):
                flags = []
                if track.is_default:
                    flags.append("default")
                if track.is_forced:
                    flags.append("forced")
                suffix = f" [{' '.join(flags)}]" if flags else ""
                print(f"{index}. {track.label}{suffix}")
            return 0

        track = client.choose_track(tracks, args.lang)
        print(f"Selected: {track.label}")
        vtt = client.download_webvtt(track)
        output = args.output or f"subtitle.{args.format}"
        save_subtitle(vtt, output, args.format)
        print(f"Saved: {output}")
        return 0
    except Exception as exc:
        print(f"ScenePrep error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
