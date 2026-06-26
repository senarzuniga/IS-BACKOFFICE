# Interfaces

## Propósito
Definir interfaces públicas y contratos entre módulos (no implementaciones).

### SimulationRunner Interface
- `start_scenario(scenario_id, overrides)` -> run_id
- `stop_run(run_id)` -> status
- `get_status(run_id)` -> {progress, kpis, errors}

### ConfigLoader Interface
- `load_master(path)` -> master_config
- `validate_config(config)` -> list(errors)

### Persistence Interface
- `save_event(run_id, event)`
- `save_kpi(run_id, kpi_snapshot)`
