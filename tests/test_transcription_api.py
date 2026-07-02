import unittest
import asyncio
import os

from fastapi import HTTPException

from api.routes.transcription import transcribe_audio


class TranscriptionAPITest(unittest.TestCase):
    def test_transcribe_no_api_key_returns_503(self):
        # Ensure OPENAI_API_KEY is not set to trigger the 503 guard
        os.environ.pop('OPENAI_API_KEY', None)

        class DummyUploadFile:
            def __init__(self, data: bytes = b"\x00\x01\x02", filename: str = "sample.mp3"):
                self._data = data
                self.filename = filename

            async def read(self):
                return self._data

        dummy = DummyUploadFile()

        with self.assertRaises(HTTPException) as cm:
            asyncio.run(transcribe_audio(dummy, language="en"))

        self.assertEqual(cm.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
