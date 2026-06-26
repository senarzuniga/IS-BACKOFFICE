# KPIEngine

## Propósito
Motor encargado de calcular y agregar KPIs durante y al final de la simulación.

## Atributos
| Atributo | Tipo | Unidad | Default | Min | Max | Obligatorio |
| tracked_kpis | list | - | ["throughput","oee"] | - | - | Sí |
| sampling_interval_s | int | s | 60 | 1 | 3600 | No |

## States
- IDLE → RUNNING → REPORTING

## Inputs
- `Event`, `MetricUpdate`, `Tick`

## Outputs
- `KPIUpdate`, `KPISummary`

## Relaciones
- consume → EventQueue, SimulationClock
- provee_a → FinancialEngine, ReportGenerator

## Parámetros de Configuración
Referenciar: `03_CONFIG_DATABASE/config_kpi.yaml`

## Reglas de Validación
- `sampling_interval_s >= 1`

## KPIs afectados
- Todos (agregador)

## Riesgos
- Muestreo inadecuado genera ruido en métricas

## Prioridad
- Alta
