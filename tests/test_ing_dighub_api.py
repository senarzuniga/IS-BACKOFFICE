import unittest

from api.routes import ing_dighub
from api.routes.ing_dighub import AutonomyRunRequest, ModuleExecuteRequest


class FakePlatform:
    def list_modules(self):
        return [{"key": "spoe", "name": "SPOE"}]

    def execute_module(self, module_key, context):
        return {"status": "ok", "module_key": module_key, "context": context}

    def run_autonomy_loop(self, mission, context, max_iterations, min_expected_value):
        return {
            "status": "completed",
            "mission": mission,
            "iterations_completed": 1,
            "stop_reason": "no_positive_expected_value",
        }


class TestIngDighubRouteHandlers(unittest.TestCase):
    def test_route_handlers(self):
        original = ing_dighub._platform
        ing_dighub._platform = FakePlatform()
        try:
            mods = ing_dighub.list_modules()
            self.assertEqual(mods["status"], "ok")
            self.assertEqual(mods["modules"][0]["key"], "spoe")

            execution = ing_dighub.execute_module("spoe", ModuleExecuteRequest(context={"a": 1}))
            self.assertEqual(execution["status"], "ok")

            run = ing_dighub.run_autonomy(
                AutonomyRunRequest(mission="test", context={}, max_iterations=3, min_expected_value=0.0)
            )
            self.assertEqual(run["status"], "completed")
        finally:
            ing_dighub._platform = original


if __name__ == "__main__":
    unittest.main()
