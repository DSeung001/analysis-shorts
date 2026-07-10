English | [한국어](README.ko.md)

# Shorts Frame Extractor

A minimal Windows app that extracts representative JPG frames from a YouTube Short. Paste a YouTube Shorts URL and generate JPG images when the scene changes significantly.

## Download

[Download the latest Windows EXE](https://github.com/DSeung001/analysis-shorts/releases/download/latest/ShortsFrameExtractor.exe)

## Usage

1. Download and run `ShortsFrameExtractor.exe`.
2. Paste a public YouTube Shorts URL.
3. Select an output folder.
4. Click **Generate Frames**.
5. Open the generated output folder.

## What it does

- Downloads one public YouTube Short temporarily.
- Extracts the first frame.
- Extracts frames when the scene changes significantly.
- Deletes the temporary video after processing.

## Limitations

- Windows x64 only.
- Public videos only.
- One URL at a time.
- YouTube changes may temporarily break downloading.

## Legal notice

Only process content that you own or are authorized to use. You are responsible for complying with YouTube's terms and applicable copyright laws.

## Development

```powershell
python app.py
```

Run the pure-logic tests:

```powershell
python -m unittest discover -s tests
```

## Build

The Windows EXE is built automatically by GitHub Actions after a push to `main`. It bundles `yt-dlp.exe`, `ffmpeg.exe`, `ffprobe.exe`, and `deno.exe` into a single `--onefile --windowed` executable, then publishes it to the `latest` GitHub Release.

## License

Licensed under GPL-3.0-or-later. This app bundles third-party software (yt-dlp, FFmpeg GPL build, Deno) whose licenses apply to the distributed executable.
