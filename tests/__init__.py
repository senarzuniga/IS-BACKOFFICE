import unittest


# The API tests rely on fastapi.testclient/httpx which may not be available or
# compatible in all developer environments (notably certain httpcore/httpx
# versions on Python 3.14). Import lazily and skip the tests if dependencies
# cannot be imported to avoid failing the whole test discovery process.
try:
    from fastapi.testclient import TestClient  # type: ignore
    from main import app  # type: ignore
except Exception:
    TestClient = None
    app = None


@unittest.skipIf(TestClient is None, "fastapi TestClient or dependencies unavailable in this environment")
class TestOrchestrationAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_run_cycle_endpoint(self):
        payload = {
            "source_type": "txt",
            "source_id": "api-test-001",
            "content": "client=ACME contact=ana@acme.com offer=Roadmap price=25000 opportunity=Expansion value=80000",
            "classification": "offer",
            "proactive_mode": True,
            "autolearning_mode": True,
            "strict_mode": False,
        }
        response = self.client.post("/orchestration/run", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertIn("result", body)
        self.assertIn("reliability", body["result"])

    def test_agent_pipeline_endpoint(self):
        payload = {
            "source_type": "txt",
            "source_id": "api-test-002",
            "content": "client=ACME value=notanumber",
            "strict_mode": False,
        }
        response = self.client.post("/orchestration/agents/run", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("pipeline", body)
        self.assertIn("alerts", body)
        self.assertIn("result", body)


if __name__ == "__main__":
    unittest.main()

