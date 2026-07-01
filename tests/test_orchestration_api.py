import unittest

from shared.schemas import RunCycleRequest

# Call route handlers directly to avoid importing TestClient/httpx in test environment.
from api.routes.orchestration import run_cycle, run_agents


class TestOrchestrationAPI(unittest.TestCase):
    def test_run_cycle_endpoint(self):
        payload = RunCycleRequest(
            source_type="txt",
            source_id="api-test-001",
            content="client=ACME contact=ana@acme.com offer=Roadmap price=25000 opportunity=Expansion value=80000",
            classification="offer",
            proactive_mode=True,
            autolearning_mode=True,
            strict_mode=False,
        )

        # Call the route function directly (synchronous). It returns a RunCycleResponse model.
        resp = run_cycle(payload)
        self.assertIsNotNone(resp)
        data = resp.model_dump() if hasattr(resp, 'model_dump') else resp.dict()
        self.assertIn('result', data)
        self.assertIn('status', data)

    def test_agent_pipeline_endpoint(self):
        payload = RunCycleRequest(
            source_type="txt",
            source_id="api-test-002",
            content="client=ACME value=notanumber",
            strict_mode=False,
        )
        resp = run_agents(payload)
        self.assertIsNotNone(resp)
        data = resp.model_dump() if hasattr(resp, 'model_dump') else resp.dict()
        self.assertIn('pipeline', data)
        self.assertIn('alerts', data)
        self.assertIn('result', data)


if __name__ == "__main__":
    unittest.main()
