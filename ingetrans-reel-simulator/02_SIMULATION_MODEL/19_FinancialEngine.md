# FinancialEngine

## Propósito
Calcular costes (CAPEX/OPEX), ROI y métricas financieras por escenario y periodo.

## Atributos
| Atributo | Tipo | Unidad | Default | Min | Max | Obligatorio |
| tracked_items | list | - | ["capex","opex"] | - | - | Sí |
| currency | string | - | "EUR" | - | - | Sí |

## States
- IDLE → CALCULATING → REPORTING

## Inputs
- `KPIUpdate`, `CostEvent`, `ScenarioParameters`

## Outputs
- `FinancialSummary`, `ROIReport`

## Relaciones
- consume → KPIEngine

## Parámetros de Configuración
Referenciar: `03_CONFIG_DATABASE/config_financial.yaml`

## Reglas de Validación
- `currency` en lista soportada

## KPIs afectados
- Costes totales, ROI, payback

## Riesgos
- Supuestos financieros incorrectos invalidan comparaciones

## Prioridad
- Alta
