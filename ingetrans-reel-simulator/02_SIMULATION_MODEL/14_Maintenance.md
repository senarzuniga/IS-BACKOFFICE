# Maintenance

## Propósito
Definir políticas y órdenes de mantenimiento que afectan la disponibilidad de equipos.

## Atributos
| Atributo | Tipo | Unidad | Default | Min | Max | Obligatorio |
| id | string | - | auto | - | - | Sí |
| equipment_id | string | - | - | - | - | Sí |
| type | string | - | "Preventive" | Preventive/Corrective | - | Sí |
| duration_min | float | min | 60.0 | 1 | 10000 | Sí |
| scheduled_time | datetime | - | null | - | - | No |

## States
- SCHEDULED → IN_PROGRESS → COMPLETED → CLOSED

## Inputs
- `ScheduleMaintenance`, `TriggerFailure`

## Outputs
- `MaintenanceStarted`, `MaintenanceCompleted`

## Relaciones
- aplica_a → Forklift, Transfer, Corrugator

## Parámetros de Configuración
Referenciar: `03_CONFIG_DATABASE/config_maintenance.yaml`

## Reglas de Validación
- `duration_min > 0`

## KPIs afectados
- MTTR, availability

## Riesgos
- Mantenimientos largos afectan disponibilidad

## Prioridad
- Alta
