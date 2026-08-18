# INGETRANS Simulator Validation Report

The canonical loader and LEVEL 1 governance tests pass. Simulator parameter propagation is blocked because the canonical dataset intentionally contains no numeric values.

Affected simulators: `IngetransSimulationEngine`, `CorrugatorEngine`, `Reel_load_simulator`, Bobina Load Simulator, Reel Load Simulator Fixed, benchmark/demo scripts and YAML simulator. They retain their previous assumptions and must not be represented as Sterner-calibrated.