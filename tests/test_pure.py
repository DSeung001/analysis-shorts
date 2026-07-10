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


if __name__ == "__main__":
    unittest.main()
