import unittest

from fastapi.testclient import TestClient

from main import app


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
