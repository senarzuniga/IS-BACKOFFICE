# Transfer

## Propósito
Unidad de transporte que mueve `Reel`s entre `Exchange`, `Track` y `Warehouse`. Puede representar unidades automáticas o manuales.

## Atributos
| Atributo | Tipo | Unidad | Default | Min | Max | Obligatorio |
| id | string | - | auto | - | - | Sí |
| type | string | - | "Manual" | "Manual"/"Automated" | - | Sí |
| max_speed_m_s | float | m/s | 1.0 | 0.1 | 3.0 | Sí |
| cycle_time_s | float | s | 45.0 | 5 | 3600 | No |
| capacity_units | int | uds | 1 | 1 | 10 | Sí |
| mtbf_h | float | h | 200.0 | 0 | 1e6 | No |
| mttr_min | float | min | 60.0 | 1 | 1e5 | No |

## States
- IDLE → SCHEDULED → MOVING → LOADING → UNLOADING → RETURNING → IDLE
- ANY → MAINTENANCE

## Inputs
- `TransferRequest`, `ScheduleAssignment`, `EmergencyStop`

## Outputs
- `TransferDeparted`, `TransferArrived`, `TransferFailed`

## Relaciones
- opera_sobre → Track, Exchange, Warehouse
- recibe_ordenes_de → ScenarioManager, Scheduler

## Lifecycle
1. Instanciación
2. Disponibilidad
3. Operación normal
4. Fallos y mantenimiento

## Parámetros de Configuración
Referenciar: `03_CONFIG_DATABASE/config_transfer.yaml`

## Reglas de Validación
- `capacity_units >= 1`
- `cycle_time_s > 0`

## KPIs afectados
- Cycle time promedio
- Transfer utilization

## Riesgos
- Ciclos largos generan retrasos en supply chain interno

## Prioridad
- Alta

