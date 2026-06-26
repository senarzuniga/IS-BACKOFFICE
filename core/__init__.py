"""Core simulation package for Reel Loading simulator.

This file makes `core` a proper Python package so imports like
`from core.consumption_engine import CorrugatorEngineV3` work when
executing the Streamlit app.
"""

__all__ = [
    "track_state",
    "roll_stand",
    "predictive_logic",
    "reactive_logic",
    "kpi_calculator",
    "consumption_engine",
]
# core package initializer

__all__ = []
"""Paquete core para el simulador de bobinas.
Archivo inicial para permitir imports de paquete.
"""
