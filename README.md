English | [한국어](README.ko.md)

# Shorts Frame Extractor

A minimal Windows app that extracts representative JPG frames from a YouTube Short. Paste a YouTube Shorts URL and generate JPG images when the scene changes significantly.

## Download

- **Windows (x64):** [ShortsFrameExtractor.exe](https://github.com/DSeung001/analysis-shorts/releases/download/latest/ShortsFrameExtractor.exe)
- **macOS (Apple Silicon):** [ShortsFrameExtractor-macos-arm64.zip](https://github.com/DSeung001/analysis-shorts/releases/download/latest/ShortsFrameExtractor-macos-arm64.zip)

> The macOS build is for Apple Silicon (M1 and later) only. It is not code-signed, so on first launch macOS may block it. Right-click the app and choose **Open**, then confirm. (Or run `xattr -dr com.apple.quarantine ShortsFrameExtractor.app`.)

## Usage

### Windows

1. Download and run `ShortsFrameExtractor.exe`.
2. Paste a public YouTube Shorts URL.
3. Select an output folder.
4. Adjust the sensitivity slider (`0.10~0.60`) as needed. Lower threshold values usually generate more frames.
5. Click **Generate Frames**.
6. Open the generated output folder.

### macOS

1. Download and unzip `ShortsFrameExtractor-macos-arm64.zip`.
2. Right-click `ShortsFrameExtractor.app` and choose **Open** on first launch.
3. Follow the same steps as Windows.

## What it does

- Downloads one public YouTube Short temporarily.
- Extracts the first frame.
- Extracts frames when the scene changes significantly.
- Deletes the temporary video after processing.

## Limitations

- Windows x64 and macOS Apple Silicon only.
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

Both artifacts are built automatically by GitHub Actions after a push to `main`. The Windows job produces a single `--onefile --windowed` `ShortsFrameExtractor.exe`; the macOS job produces an Apple Silicon `.app` bundle zipped as `ShortsFrameExtractor-macos-arm64.zip`. Each bundles `yt-dlp`, `ffmpeg`, `ffprobe`, and `deno`, and both are published to the `latest` GitHub Release.

## License

Licensed under GPL-3.0-or-later. This app bundles third-party software (yt-dlp, FFmpeg GPL build, Deno) whose licenses apply to the distributed executable.
