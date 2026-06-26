# Reports

## Propósito
Definir plantillas y pipeline para generación de reportes (KPIs, financials, event logs).

## Outputs
- `run_summary.json` / `run_summary.csv`
- `financial_report.xlsx`
- `event_log.csv`

## Pipeline
- `analytics` procesa outputs de `kpi_engine` y `financial_engine` y guarda artefactos en `persistence`.
