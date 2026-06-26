# AnimationEngine

## Propósito
Motor opcional para generar trazas de animación (no UI) que permitan reproducir movimiento y generar outputs para visualizadores externos.

## Atributos
| Atributo | Tipo | Unidad | Default | Min | Max | Obligatorio |
| enabled | bool | - | false | - | - | No |
| sample_rate_s | int | s | 1 | 1 | 60 | No |

## States
- IDLE → RECORDING → STOPPED

## Inputs
- `EntityStateChange`, `Tick`

## Outputs
- `AnimationFrame`, `TraceFile`

## Relaciones
- consume → EventQueue, SimulationClock

## Parámetros de Configuración
Referenciar: `03_CONFIG_DATABASE/config_animation.yaml`

## Reglas de Validación
- `sample_rate_s >= 1`

## KPIs afectados
- N/A (soporte para debugging/visualización)

## Riesgos
- Registro excesivo produce archivos grandes

## Prioridad
- Baja (opcional)
