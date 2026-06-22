from types import SimpleNamespace
from typing import Any, List


class SimulationEngine:
    def __init__(self, config: Any):
        self.config = config

    def run(self) -> SimpleNamespace:
        # Return a minimal results object expected by the API
        results = SimpleNamespace()
        results.plant_name = getattr(self.config, 'name', 'Demo Plant')
        results.plant_type = getattr(self.config, 'plant_type', 'DemoType')
        results.duration_hours = 8.0
        results.m2_produced = 1000.0
        results.total_units_converted = 120.0
        results.corrugator_efficiency = 0.85
        results.average_oee = 0.78
        results.buffer_avg_occupancy = 0.25
        results.transport_utilization = 0.3
        results.recommendations = ["Run maintenance check", "Optimize flow"]

        # Bottlenecks: simple list of SimpleNamespace objects
        b1 = SimpleNamespace(location='LineA', type='queue', avg_wait_s=12.3, max_wait_s=45.0, frequency=10)
        results.bottlenecks = [b1]

        # Machine metrics: list of SimpleNamespace
        m1 = SimpleNamespace(machine_id='M1', availability=0.95, performance=0.9, quality=0.99, oee=0.85, units_produced=1000, blocked_time_s=120, setup_time_s=60)
        results.machine_metrics = [m1]

        return results


class ScenarioOptimizer:
    def __init__(self):
        pass

    def run_all(self, config: Any) -> List[SimpleNamespace]:
        # Return a small list of scenario result-like objects
        s1 = SimpleNamespace(scenario_label='S1', m2_produced=1000.0, total_units_converted=120.0, average_oee=0.78, corrugator_efficiency=0.85, buffer_avg_occupancy=0.2, transport_utilization=0.3)
        s2 = SimpleNamespace(scenario_label='S2', m2_produced=1100.0, total_units_converted=130.0, average_oee=0.82, corrugator_efficiency=0.87, buffer_avg_occupancy=0.18, transport_utilization=0.32)
        return [s1, s2]
