"""Shorts Frame Extractor.

Paste a YouTube Shorts URL and generate JPG images when the scene changes
significantly. Windows desktop MVP built on Tkinter + bundled yt-dlp / FFmpeg /
Deno executables.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# --- Global constants -------------------------------------------------------

APP_NAME = "Shorts Frame Extractor"
SCENE_THRESHOLD = 0.35
MIN_SCENE_THRESHOLD = 0.10
MAX_SCENE_THRESHOLD = 0.60
MAX_FRAMES = 60
DOWNLOAD_TIMEOUT_SECONDS = 300
TARGET_WIDTH = 1080
MAX_DURATION_SECONDS = 180
VIDEO_EXT_PRIORITY = (".mp4", ".webm", ".mkv", ".mov", ".m4v")

ALLOWED_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}

# Hide subprocess console windows on Windows; no-op elsewhere.
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


# --- Resource / path helpers ------------------------------------------------

def resource_path(relative_path: str) -> Path:
    """Return the path to a bundled resource in dev and PyInstaller runtime."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative_path


def _tool_path(name: str) -> Path:
    """Return the path to a bundled tool executable (adds .exe on Windows)."""
    exe = f"{name}.exe" if sys.platform == "win32" else name
    path = resource_path(f"tools/{exe}")
    # Bundled binaries may lose the executable bit on POSIX; restore it.
    if sys.platform != "win32":
        try:
            mode = path.stat().st_mode
            path.chmod(mode | 0o111)
        except OSError:
            pass
    return path


# --- URL validation ---------------------------------------------------------

def validate_youtube_url(url: str) -> bool:
    """Minimally validate that the URL is an allowed YouTube (Shorts) link.

    The final download feasibility is decided by yt-dlp; this only rejects
    obviously invalid input.
    """
    if not url or not url.strip():
        return False
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_HOSTS:
        return False

    path = parsed.path or ""
    if host == "youtu.be":
        # youtu.be/VIDEO_ID -> path must contain a video id segment.
        return len(path.strip("/")) > 0

    # youtube.com hosts: accept Shorts and standard watch/embed links.
    if path.startswith("/shorts/"):
        return len(path[len("/shorts/"):].strip("/")) > 0
    if path == "/watch":
        from urllib.parse import parse_qs

        return bool(parse_qs(parsed.query).get("v"))
    if path.startswith("/embed/") or path.startswith("/v/"):
        return len(path.split("/", 2)[-1].strip("/")) > 0
    return False


# --- Filesystem -------------------------------------------------------------

def create_output_directory(base_path: Path) -> Path:
    """Create and return a run-specific subfolder under ``base_path``."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = base_path / f"shorts_frames_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=False)
    return output_dir


# --- Download ---------------------------------------------------------------

class JobError(Exception):
    """User-facing error raised during a job."""


def _debug_log_path() -> Path:
    return Path(tempfile.gettempdir()) / "shorts-frame-extractor.log"


def _log_debug(message: str) -> None:
    """Write a short debug line to the temp log without affecting app flow."""
    try:
        with _debug_log_path().open("a", encoding="utf-8") as fh:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fh.write(f"[{ts}] {message}\n")
    except OSError:
        pass


def _run(args: list[str], timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
        creationflags=CREATE_NO_WINDOW,
        timeout=timeout,
    )


def normalize_scene_threshold(value: float) -> float:
    """Clamp and normalize scene threshold to a 2-decimal safe value."""
    clamped = max(MIN_SCENE_THRESHOLD, min(MAX_SCENE_THRESHOLD, float(value)))
    return round(clamped, 2)


def download_video(url: str, temp_dir: Path) -> Path:
    """Download the video with the bundled yt-dlp and return its file path."""
    yt_dlp = _tool_path("yt-dlp")
    deno = _tool_path("deno")
    tools_dir = _tool_path("ffmpeg").parent
    output_template = str(temp_dir / "input.%(ext)s")

    args = [
        str(yt_dlp),
        "--no-playlist",
        "--js-runtimes", f"deno:{deno}",
        "--ffmpeg-location", str(tools_dir),
        "--match-filter", f"duration <= {MAX_DURATION_SECONDS}",
        "-f", "bv*[height<=1080]+ba/b[height<=1080]/b",
        "--merge-output-format", "mp4",
        "-o", output_template,
        url,
    ]

    try:
        _run(args, DOWNLOAD_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        _log_debug("yt-dlp timeout")
        raise JobError("The operation timed out.") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").lower()
        _log_debug(f"yt-dlp failed: {(exc.stderr or '').strip()[-400:]}")
        if "private" in stderr or "unavailable" in stderr or "not available" in stderr:
            raise JobError(
                "The video could not be downloaded. "
                "It may be private or unavailable."
            ) from exc
        if "duration" in stderr and "match" in stderr:
            raise JobError("The video is too long for this tool.") from exc
        raise JobError(
            "The download failed. Check your internet connection and try again."
        ) from exc

    video_file = _select_downloaded_video(temp_dir)
    if not video_file:
        _log_debug(f"No downloadable input.* video found in {temp_dir}")
        raise JobError(
            "The video could not be downloaded. It may be private or unavailable."
        )
    return video_file


def _select_downloaded_video(temp_dir: Path) -> Path | None:
    """Pick the most likely final video file from yt-dlp output candidates."""
    candidates = sorted(p for p in temp_dir.glob("input.*") if p.is_file())
    if not candidates:
        return None

    for preferred_name in ("input.mp4", "input.webm", "input.mkv", "input.mov", "input.m4v"):
        preferred = temp_dir / preferred_name
        if preferred.is_file() and preferred.stat().st_size > 0:
            return preferred

    for ext in VIDEO_EXT_PRIORITY:
        for candidate in candidates:
            if candidate.suffix.lower() == ext and candidate.stat().st_size > 0:
                return candidate

    # Fallback for uncommon containers.
    for candidate in candidates:
        if candidate.stat().st_size > 0:
            return candidate
    return None


# --- Frame extraction -------------------------------------------------------

def extract_frames(
    video_path: Path, output_dir: Path, scene_threshold: float
) -> list[Path]:
    """Extract the first frame plus scene-change frames as JPGs."""
    ffmpeg = _tool_path("ffmpeg")
    scene_threshold = normalize_scene_threshold(scene_threshold)
    # Use arithmetic OR for broad FFmpeg expression compatibility.
    select_expr = f"select='eq(n,0)+gt(scene,{scene_threshold})'"
    scale_expr = f"scale='min({TARGET_WIDTH},iw)':-2"
    args = [
        str(ffmpeg),
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-i", str(video_path),
        "-vf", f"{select_expr},{scale_expr}",
        "-fps_mode", "vfr",
        "-q:v", "2",
        str(output_dir / "frame_%03d.jpg"),
    ]
    try:
        _run(args, DOWNLOAD_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        _log_debug("ffmpeg timeout during frame extraction")
        raise JobError("The operation timed out.") from exc
    except subprocess.CalledProcessError as exc:
        _log_debug(f"ffmpeg extraction failed: {(exc.stderr or '').strip()[-500:]}")
        raise JobError("Frame extraction failed.") from exc

    return sorted(output_dir.glob("frame_*.jpg"))


def limit_frames(frames: list[Path], max_count: int = MAX_FRAMES) -> list[Path]:
    """Keep at most ``max_count`` frames using even sampling; delete the rest."""
    if len(frames) <= max_count:
        return frames

    ordered = sorted(frames)
    step = len(ordered) / max_count
    keep_indices = {int(i * step) for i in range(max_count)}
    kept: list[Path] = []
    for index, frame in enumerate(ordered):
        if index in keep_indices:
            kept.append(frame)
        else:
            try:
                frame.unlink()
            except OSError:
                pass
    return kept


# --- Job orchestration ------------------------------------------------------

def run_job(url: str, output_base: str, on_status, scene_threshold: float = SCENE_THRESHOLD) -> Path:
    """Run the full pipeline and always clean up the temporary video.

    Returns the output directory. Raises ``JobError`` with a user-facing
    message on failure.
    """
    url = (url or "").strip()
    if not validate_youtube_url(url):
        raise JobError("Enter a valid YouTube Shorts URL.")

    if not output_base or not output_base.strip():
        raise JobError("Select an output folder.")

    base_path = Path(output_base).expanduser()
    if not base_path.exists() or not base_path.is_dir():
        raise JobError("The selected output folder does not exist.")

    try:
        output_dir = create_output_directory(base_path)
    except OSError as exc:
        raise JobError("Could not create the output folder.") from exc

    with tempfile.TemporaryDirectory(prefix="shorts_job_") as temp_name:
        temp_dir = Path(temp_name)
        scene_threshold = normalize_scene_threshold(scene_threshold)

        on_status("Downloading video...")
        video_path = download_video(url, temp_dir)

        on_status(f"Extracting frames... (sensitivity {scene_threshold:.2f})")
        frames = extract_frames(video_path, output_dir, scene_threshold)

        if not frames:
            raise JobError("No frames were generated from this video.")

        frames = limit_frames(frames)

    on_status(f"Done. {len(frames)} image(s) created.")
    return output_dir


def open_folder(path: Path) -> None:
    """Open ``path`` in the OS file explorer."""
    try:
        if sys.platform == "win32":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except OSError:
        pass


# --- GUI --------------------------------------------------------------------

class App:
    """Single-window Tkinter GUI managing the extraction job state."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.last_output_dir: Path | None = None
        self._build_widgets()

    def _build_widgets(self) -> None:
        self.root.title(APP_NAME)
        self.root.geometry("640x330")
        self.root.resizable(False, False)

        pad = {"padx": 12, "pady": 4}
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="YouTube Shorts URL").pack(anchor="w")
        self.url_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.url_var, width=72).pack(
            fill="x", **pad
        )

        ttk.Label(frame, text="Output folder").pack(anchor="w")
        folder_row = ttk.Frame(frame)
        folder_row.pack(fill="x", **pad)
        default_dir = str(Path.home() / "Pictures" / "ShortsFrames")
        self.folder_var = tk.StringVar(value=default_dir)
        ttk.Entry(folder_row, textvariable=self.folder_var).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(folder_row, text="Browse...", command=self._on_browse).pack(
            side="left", padx=(8, 0)
        )

        ttk.Label(
            frame, text="Sensitivity (lower threshold = more frames)"
        ).pack(anchor="w")
        sensitivity_row = ttk.Frame(frame)
        sensitivity_row.pack(fill="x", **pad)
        self.sensitivity_var = tk.DoubleVar(value=SCENE_THRESHOLD)
        self.sensitivity_value_var = tk.StringVar(value=f"{SCENE_THRESHOLD:.2f}")
        self.sensitivity_scale = ttk.Scale(
            sensitivity_row,
            from_=MIN_SCENE_THRESHOLD,
            to=MAX_SCENE_THRESHOLD,
            variable=self.sensitivity_var,
            command=self._on_sensitivity_changed,
        )
        self.sensitivity_scale.pack(side="left", fill="x", expand=True)
        ttk.Label(
            sensitivity_row, textvariable=self.sensitivity_value_var, width=5
        ).pack(side="left", padx=(8, 0))

        self.generate_btn = ttk.Button(
            frame, text="Generate Frames", command=self._on_generate
        )
        self.generate_btn.pack(pady=(8, 4))

        self.status_var = tk.StringVar(value="Status: Ready")
        ttk.Label(frame, textvariable=self.status_var).pack(anchor="w", pady=4)

        self.open_btn = ttk.Button(
            frame,
            text="Open Output Folder",
            command=self._on_open_folder,
            state="disabled",
        )
        self.open_btn.pack(anchor="w")

    # -- Event handlers ------------------------------------------------------

    def _on_browse(self) -> None:
        selected = filedialog.askdirectory()
        if selected:
            self.folder_var.set(selected)

    def _on_open_folder(self) -> None:
        if self.last_output_dir is not None:
            open_folder(self.last_output_dir)

    def _on_sensitivity_changed(self, _value: str) -> None:
        normalized = normalize_scene_threshold(self.sensitivity_var.get())
        self.sensitivity_value_var.set(f"{normalized:.2f}")

    def _on_generate(self) -> None:
        url = self.url_var.get()
        output_base = self.folder_var.get()
        scene_threshold = normalize_scene_threshold(self.sensitivity_var.get())

        base_path = Path(output_base).expanduser()
        if output_base and not base_path.exists():
            try:
                base_path.mkdir(parents=True, exist_ok=True)
            except OSError:
                messagebox.showerror(APP_NAME, "Could not create the output folder.")
                return

        self.generate_btn.config(state="disabled")
        self.open_btn.config(state="disabled")
        self._set_status("Starting...")

        thread = threading.Thread(
            target=self._worker, args=(url, str(base_path), scene_threshold), daemon=True
        )
        thread.start()

    # -- Worker thread -------------------------------------------------------

    def _worker(self, url: str, output_base: str, scene_threshold: float) -> None:
        try:
            output_dir = run_job(url, output_base, self._set_status, scene_threshold)
        except JobError as exc:
            self._on_error(str(exc))
        except Exception:  # noqa: BLE001 - convert to a friendly message
            self._on_error("An unexpected error occurred.")
        else:
            self._on_success(output_dir)

    # -- Thread-safe UI updates ---------------------------------------------

    def _set_status(self, text: str) -> None:
        self.root.after(0, lambda: self.status_var.set(f"Status: {text}"))

    def _on_error(self, message: str) -> None:
        def show() -> None:
            self.status_var.set("Status: Ready")
            self.generate_btn.config(state="normal")
            messagebox.showerror(APP_NAME, message)

        self.root.after(0, show)

    def _on_success(self, output_dir: Path) -> None:
        def done() -> None:
            self.last_output_dir = output_dir
            self.generate_btn.config(state="normal")
            self.open_btn.config(state="normal")

        self.root.after(0, done)


def build_gui() -> tk.Tk:
    """Construct and return the single application window."""
    root = tk.Tk()
    App(root)
    return root


def main() -> None:
    """Application entry point."""
    root = build_gui()
    root.mainloop()


if __name__ == "__main__":
    main()
