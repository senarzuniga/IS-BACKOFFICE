# SimulationClock

## Propósito
Objeto central que gobierna el avance temporal (tick = 1s) y sincroniza eventos discretos.

## Atributos
| Atributo | Tipo | Unidad | Default | Min | Max | Obligatorio |
| current_time | datetime | - | 1970-01-01T00:00:00 | - | - | Sí |
| tick_s | float | s | 1.0 | 0.1 | 3600 | Sí |
| end_time | datetime | - | null | - | - | No |

## States
- RUNNING → PAUSED → STOPPED

## Inputs
- `Start`, `Pause`, `Resume`, `Stop`

## Outputs
- `Tick`, `TimeAdvanced`, `SimulationEnded`

## Relaciones
- coordina → EventQueue, Entities

## Parámetros de Configuración
Referenciar: `03_CONFIG_DATABASE/config_simulation_clock.yaml`

## Reglas de Validación
- `tick_s > 0`

## KPIs afectados
- Sim duration, temporal resolution

## Riesgos
- Tick demasiado grande pierde resolución; demasiado pequeño eleva coste computacional

## Prioridad
- Alta
