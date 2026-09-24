# ScenePrep

**Learn the language before you watch the scene.**

ScenePrep is a Python CLI for obtaining **WebVTT subtitles from HLS subtitle playlists that you are legally authorized to access**, then converting them to SRT for language-learning workflows.

## What it does

```
Master .m3u8
    |
    +--> subtitle tracks
            |
            +--> select English / English CC
                    |
                    +--> download WebVTT segments
                            |
                            +--> merge
                                    |
                                    +--> VTT or SRT
```

## Important limitation

ScenePrep **does not bypass DRM, FairPlay, authentication, encryption, or access controls**.

Use it only with subtitle URLs you are authorized to access, such as your own HLS streams, public/unencrypted subtitle playlists, or another source whose terms permit this use. It does not download protected video.

This MVP targets common segmented WebVTT subtitle playlists. HLS providers can use different timestamp conventions, so more robust timestamp-map handling is on the roadmap.

## Setup

Python 3.10+ is recommended.

```bash
git clone https://github.com/devgofer/ScenePrep.git
cd ScenePrep
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

List available subtitle tracks:

```bash
python -m scene_prep.cli "https://example.com/master.m3u8" --list
```

Download English subtitles as SRT:

```bash
python -m scene_prep.cli "https://example.com/master.m3u8" --lang en
```

Keep WebVTT:

```bash
python -m scene_prep.cli "https://example.com/master.m3u8" --lang en --format vtt -o episode.en.vtt
```

## Development

Install pytest and run:

```bash
pip install pytest
pytest
```

## Project structure

```
ScenePrep/
├── scene_prep/
│   ├── __init__.py
│   ├── cli.py
│   ├── hls.py
│   └── subtitle.py
├── tests/
│   ├── test_hls.py
│   └── test_subtitle.py
└── requirements.txt
```

## Roadmap

- [x] Parse HLS subtitle tracks
- [x] Select English subtitle track
- [x] Download segmented WebVTT
- [x] Merge subtitle segments
- [x] Convert VTT to SRT
- [x] CLI
- [x] Unit tests
- [ ] Better HLS timestamp-map handling
- [ ] Subtitle cleanup and duplicate-cue detection
- [ ] Episode metadata
- [ ] AI vocabulary extraction
- [ ] Grammar and natural-expression analysis
- [ ] Pre-watch English lesson generation
- [ ] Post-watch comprehension and speaking practice

## Vision

The goal is not to make another subtitle downloader.

```
🎬 Choose an episode
       ↓
📚 Prepare before watching
       ↓
   vocabulary
   natural expressions
   grammar
   reactions
   cultural context
       ↓
🎥 Watch
       ↓
🗣️ Practice
       ↓
🧠 Remember
```

ScenePrep is the infrastructure layer that gets subtitles into a form the learning system can understand.
