# API REST

## Propósito
Diseño de endpoints REST para operar el simulador y consultar resultados.

## Endpoints propuestos
- `POST /api/v1/scenarios` — crear escenario (body: config overrides)
- `POST /api/v1/runs` — iniciar ejecución (body: scenario_id)
- `GET /api/v1/runs/{run_id}` — estado y KPIs
- `GET /api/v1/runs/{run_id}/events` — logs de eventos
- `GET /api/v1/runs/{run_id}/export?format=csv|xlsx|json` — descarga de resultados

Seguridad: token-based auth (JWT) para endpoints de control.
