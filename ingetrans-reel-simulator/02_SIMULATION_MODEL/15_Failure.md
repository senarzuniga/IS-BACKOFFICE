# Failure

## Propósito
Modelar eventos de fallo para equipos, con generación estocástica basada en MTBF/MTTR y reglas de criticidad.

## Atributos
| Atributo | Tipo | Unidad | Default | Min | Max | Obligatorio |
| id | string | - | auto | - | - | Sí |
| equipment_id | string | - | - | - | - | Sí |
| severity | int | - | 3 | 1 | 5 | No |
| reported_at | datetime | - | null | - | - | No |
| resolved_at | datetime | - | null | - | - | No |

## States
- PENDING → ACTIVE → RESOLVED

## Inputs
- `CheckMTBF`, `ManualReport`

## Outputs
- `MachineFailure`, `FailureResolved`

## Relaciones
- afecta_a → Corrugator, Transfer, Forklift

## Parámetros de Configuración
Referenciar: `03_CONFIG_DATABASE/config_failure.yaml`

## Reglas de Validación
- `severity` entre 1 y 5

## KPIs afectados
- MTBF, downtime, availability

## Riesgos
- Falta de modelado de fallos realistas produce falsas conclusiones

## Prioridad
- Alta
