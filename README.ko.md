[English](README.md) | 한국어

# 쇼츠 프레임 추출기

YouTube Shorts URL을 입력하면 화면이 크게 바뀌는 장면을 대표 JPG 이미지로 생성하는 Windows 프로그램입니다.

## 다운로드

[최신 Windows EXE 다운로드](https://github.com/DSeung001/analysis-shorts/releases/download/latest/ShortsFrameExtractor.exe)

## 사용법

1. `ShortsFrameExtractor.exe`를 내려받아 실행합니다.
2. 공개 YouTube Shorts URL을 붙여 넣습니다.
3. 출력 폴더를 선택합니다.
4. **Generate Frames**를 누릅니다.
5. 생성된 결과 폴더를 엽니다.

## 동작 방식

- 공개 YouTube Short 한 개를 임시로 다운로드합니다.
- 첫 프레임을 추출합니다.
- 화면 변화가 큰 장면의 프레임을 추출합니다.
- 처리가 끝나면 임시 영상을 삭제합니다.

## 제한사항

- Windows x64만 지원합니다.
- 공개 영상만 지원합니다.
- 한 번에 URL 하나만 처리합니다.
- YouTube 변경으로 다운로드 기능이 일시적으로 동작하지 않을 수 있습니다.

## 법적 고지

본인이 소유하거나 사용 권한이 있는 콘텐츠만 처리해야 합니다. YouTube 약관과 관련 저작권법을 준수할 책임은 사용자에게 있습니다.

## 개발

```powershell
python app.py
```

순수 로직 테스트 실행:

```powershell
python -m unittest discover -s tests
```

## 빌드

`main` 브랜치에 푸시하면 GitHub Actions가 Windows EXE를 자동으로 빌드합니다. `yt-dlp.exe`, `ffmpeg.exe`, `ffprobe.exe`, `deno.exe`를 `--onefile --windowed` 단일 실행파일에 번들한 뒤 `latest` GitHub Release에 게시합니다.

## 라이선스

GPL-3.0-or-later 라이선스를 따릅니다. 이 앱은 서드파티 소프트웨어(yt-dlp, GPL FFmpeg 빌드, Deno)를 번들하며, 배포되는 실행파일에는 해당 라이선스가 적용됩니다.
