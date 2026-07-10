import unittest
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app  # noqa: E402


class ValidateUrlTests(unittest.TestCase):
    def test_valid_shorts(self):
        self.assertTrue(app.validate_youtube_url("https://www.youtube.com/shorts/abc123"))
        self.assertTrue(app.validate_youtube_url("https://youtube.com/shorts/abc123"))
        self.assertTrue(app.validate_youtube_url("https://m.youtube.com/shorts/abc123"))
        self.assertTrue(
            app.validate_youtube_url(
                "https://youtube.com/shorts/KylLDrQjZ0E?si=YID3IsDUkuMDfcyg"
            )
        )

    def test_valid_youtu_be(self):
        self.assertTrue(app.validate_youtube_url("https://youtu.be/abc123"))

    def test_valid_watch(self):
        self.assertTrue(app.validate_youtube_url("https://www.youtube.com/watch?v=abc123"))

    def test_invalid(self):
        self.assertFalse(app.validate_youtube_url(""))
        self.assertFalse(app.validate_youtube_url("   "))
        self.assertFalse(app.validate_youtube_url("not a url"))
        self.assertFalse(app.validate_youtube_url("https://vimeo.com/12345"))
        self.assertFalse(app.validate_youtube_url("https://www.youtube.com/shorts/"))
        self.assertFalse(app.validate_youtube_url("https://youtu.be/"))
        self.assertFalse(app.validate_youtube_url("ftp://youtube.com/shorts/abc"))

    def test_strips_whitespace(self):
        self.assertTrue(app.validate_youtube_url("  https://youtu.be/abc123  "))


class LimitFramesTests(unittest.TestCase):
    def _make_frames(self, count, tmp):
        frames = []
        for i in range(count):
            p = Path(tmp) / f"frame_{i:03d}.jpg"
            p.write_bytes(b"x")
            frames.append(p)
        return frames

    def test_no_limit_when_under_max(self):
        with tempfile.TemporaryDirectory() as tmp:
            frames = self._make_frames(10, tmp)
            result = app.limit_frames(frames, max_count=60)
            self.assertEqual(len(result), 10)
            self.assertTrue(all(p.exists() for p in result))

    def test_limits_and_deletes_extra(self):
        with tempfile.TemporaryDirectory() as tmp:
            frames = self._make_frames(100, tmp)
            result = app.limit_frames(frames, max_count=60)
            self.assertEqual(len(result), 60)
            remaining = list(Path(tmp).glob("frame_*.jpg"))
            self.assertEqual(len(remaining), 60)
            self.assertTrue(all(p.exists() for p in result))

    def test_exact_max(self):
        with tempfile.TemporaryDirectory() as tmp:
            frames = self._make_frames(60, tmp)
            result = app.limit_frames(frames, max_count=60)
            self.assertEqual(len(result), 60)


class DownloadedVideoSelectionTests(unittest.TestCase):
    def test_prefers_mp4_when_multiple_candidates_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            (temp_dir / "input.f137.mp4").write_bytes(b"x")
            (temp_dir / "input.webm").write_bytes(b"x")
            (temp_dir / "input.mp4").write_bytes(b"x")

            selected = app._select_downloaded_video(temp_dir)
            self.assertIsNotNone(selected)
            self.assertEqual(selected.name, "input.mp4")

    def test_falls_back_to_nonempty_unknown_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            (temp_dir / "input.bin").write_bytes(b"x")

            selected = app._select_downloaded_video(temp_dir)
            self.assertIsNotNone(selected)
            self.assertEqual(selected.name, "input.bin")

    def test_returns_none_when_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            selected = app._select_downloaded_video(Path(tmp))
            self.assertIsNone(selected)


class SceneThresholdTests(unittest.TestCase):
    def test_default_threshold(self):
        self.assertEqual(app.normalize_scene_threshold(app.SCENE_THRESHOLD), 0.35)

    def test_clamps_to_min(self):
        self.assertEqual(app.normalize_scene_threshold(0.01), 0.10)

    def test_clamps_to_max(self):
        self.assertEqual(app.normalize_scene_threshold(1.2), 0.60)

    def test_rounds_to_two_decimals(self):
        self.assertEqual(app.normalize_scene_threshold(0.236), 0.24)


if __name__ == "__main__":
    unittest.main()
