# Shift

## Propósito
Modelar turnos de trabajo y calendarios que afectan disponibilidad de operadores y recursos.

## Atributos
| Atributo | Tipo | Unidad | Default | Min | Max | Obligatorio |
| id | string | - | auto | - | - | Sí |
| name | string | - | "Day" | - | - | Sí |
| start_time | string | HH:MM | "06:00" | - | - | Sí |
| end_time | string | HH:MM | "14:00" | - | - | Sí |
| active_days | list | - | [1,2,3,4,5] | - | - | No |

## States
- ACTIVE / INACTIVE

## Inputs
- `ShiftScheduleUpdate`

## Outputs
- `ShiftStarted`, `ShiftEnded`

## Relaciones
- asigna_a → Operator, Maintenance

## Parámetros de Configuración
Referenciar: `03_CONFIG_DATABASE/config_shift.yaml`

## Reglas de Validación
- `start_time < end_time` (en un mismo día) o usar flag overnight

## KPIs afectados
- Labor availability

## Riesgos
- Horarios mal configurados desincronizan recursos

## Prioridad
- Media
