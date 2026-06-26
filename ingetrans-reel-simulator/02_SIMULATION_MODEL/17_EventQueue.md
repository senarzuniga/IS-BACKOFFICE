# EventQueue

## Propósito
Estructura que gestiona eventos discretos con prioridad, timestamp y tie-breakers para determinismo.

## Atributos
| Atributo | Tipo | Unidad | Default | Min | Max | Obligatorio |
| queue_type | string | - | "priority" | - | - | Sí |
| max_size | int | - | 100000 | 1 | 1e7 | No |

## States
- IDLE → PROCESSING → BLOCKED

## Inputs
- `PushEvent`, `CancelEvent`

## Outputs
- `PopEvent`, `EventProcessed`

## Relaciones
- alimenta → SimulationClock, Entities

## Parámetros de Configuración
Referenciar: `03_CONFIG_DATABASE/config_event_queue.yaml`

## Reglas de Validación
- `max_size >= 1`

## KPIs afectados
- Event processing latency

## Riesgos
- Cola con prioridad mal definida produce nondeterminismo

## Prioridad
- Alta
