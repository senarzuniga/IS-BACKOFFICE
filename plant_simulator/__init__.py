"""Minimal shim for plant_simulator used in tests when real package is absent.

This module provides lightweight stubs for ConfigAgent, SimulationEngine,
ScenarioOptimizer and report generation to allow unit tests to import the
application without requiring the full external dependency.
"""

__all__ = [
    "config_agent",
    "simulation_engine",
    "report_generator",
]
