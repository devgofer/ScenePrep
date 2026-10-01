from __future__ import annotations

import argparse
import sys

from .hls import HLSClient
from .service import generate_subtitles, resolve_source_url


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download legally accessible HLS WebVTT subtitles."
    )
    parser.add_argument(
        "url",
        help="Authorized HLS .m3u8 URL or Apple TV episode URL.",
    )
    parser.add_argument("--lang", default="en", help="Subtitle language (default: en).")
    parser.add_argument("--format", choices=("vtt", "srt", "both"), default="both")
    parser.add_argument("-o", "--output", help="Output file path.")
    parser.add_argument("--list", action="store_true", help="List subtitle tracks and exit.")
    parser.add_argument(
        "--cookies-file",
        help="Path to browser-exported cookies file in Netscape format.",
    )
    parser.add_argument(
        "--subtitle-url",
        help=(
            "Authorized unencrypted subtitle/HLS playlist URL for an Apple TV "
            "episode. Required when the input is an Apple TV episode URL."
        ),
    )
    parser.add_argument("--user-agent", default="ScenePrep/0.1")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        if args.list:
            source_url, cookies = resolve_source_url(
                url=args.url,
                cookies_file=args.cookies_file,
                subtitle_url=args.subtitle_url,
                user_agent=args.user_agent,
            )
            client = HLSClient(user_agent=args.user_agent, cookies=cookies)
            tracks = client.list_subtitle_tracks(source_url)
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

        result = generate_subtitles(
            url=args.url,
            lang=args.lang,
            fmt=args.format,
            output=args.output,
            cookies_file=args.cookies_file,
            subtitle_url=args.subtitle_url,
            user_agent=args.user_agent,
        )
        print(f"Selected: {result.selected_track}")
        for output_path in result.outputs:
            print(f"Saved: {output_path}")
        return 0
    except Exception as exc:
        print(f"ScenePrep error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
