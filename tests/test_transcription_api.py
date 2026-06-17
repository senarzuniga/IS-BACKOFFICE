import unittest

from fastapi.testclient import TestClient
from main import app


class TranscriptionAPITest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_transcribe_no_api_key_returns_503(self):
        files = {"file": ("sample.mp3", b"\x00\x01\x02", "audio/mpeg")}
        resp = self.client.post("/audio/transcribe", files=files, data={"language": "en"})
        self.assertEqual(resp.status_code, 503)
        # Detail may vary depending on environment (missing key or client error)
        self.assertTrue(bool(resp.json().get("detail", "")))


if __name__ == "__main__":
    unittest.main()
