import unittest

from backoffice.ing_dighub_platform import IngDighubPlatformService


class FakeAIFactoryClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def post_json(self, path, payload):
        self.calls.append((path, payload))
        queue = self.responses.get(path, [])
        if queue:
            return queue.pop(0)
        return {"status": "ok"}


class TestIngDighubPlatformService(unittest.TestCase):
    def test_lists_requested_modules(self):
        service = IngDighubPlatformService(ai_factory=FakeAIFactoryClient({}))
        modules = service.list_modules()
        self.assertGreaterEqual(len(modules), 12)
        keys = {m["key"] for m in modules}
        self.assertIn("industrial_knowledge_hub", keys)
        self.assertIn("simulation_center", keys)
        self.assertIn("industrial_intelligence", keys)

    def test_execute_module_uses_service_endpoint(self):
        fake = FakeAIFactoryClient({
            "/api/v1/services/spoe/execute": [{"status": "ok", "trace_id": "t-1"}],
        })
        service = IngDighubPlatformService(ai_factory=fake)
        result = service.execute_module("spoe", {"offer": "SR1400"})
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["endpoint"], "/api/v1/services/spoe/execute")
        self.assertEqual(fake.calls[0][0], "/api/v1/services/spoe/execute")

    def test_autonomy_stops_without_positive_expected_value(self):
        fake = FakeAIFactoryClient(
            {
                "/api/v1/cognitive-loop/step": [
                    {
                        "status": "ok",
                        "selected": {"expected_value": 1.5},
                        "validation": {"accepted": True},
                    },
                    {
                        "status": "ok",
                        "selected": {"expected_value": -0.1},
                        "validation": {"accepted": True},
                    },
                ]
            }
        )
        service = IngDighubPlatformService(ai_factory=fake)
        result = service.run_autonomy_loop("mission", max_iterations=6)
        self.assertEqual(result["stop_reason"], "no_positive_expected_value")
        self.assertEqual(result["iterations_completed"], 2)


if __name__ == "__main__":
    unittest.main()
