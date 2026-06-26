# Exchange

## Propósito
Zona de intercambio entre `Track`/`Transfer` y `RollStand` donde se depositan y recogen `Reel`s para carga/descarga.

## Atributos
| Atributo | Tipo | Unidad | Default | Min | Max | Obligatorio |
|----------|------|--------|--------:|----:|----:|:-----------:|
| id | string | - | auto | - | - | Sí |
| name | string | - | "Exchange A" | - | - | Sí |
| position_x | float | m | 0.0 | -1000 | 1000 | Sí |
| position_y | float | m | 0.0 | -1000 | 1000 | Sí |
| capacity_slots | int | uds | 2 | 1 | 50 | Sí |
| slot_length_m | float | m | 9.0 | 0.5 | 50.0 | Sí |

## States
- IDLE → LOADING → OCCUPIED → UNLOADING → IDLE
- ANY → BLOCKED → MAINTENANCE

## Inputs
- `TransferArrived`, `ForkliftArrived`, `ReelArrived`

## Outputs
- `ReelPlaced`, `ReelPicked`, `ExchangeBlocked`

## Relaciones
- conecta_a → Track
- sirve_a → RollStand
- coordina_con → Transfer, Forklift

## Lifecycle
1. Creación
2. Activación
3. Operación (intercambio de bobinas)
4. Mantenimiento

## Parámetros de Configuración
Referenciar: `03_CONFIG_DATABASE/config_exchange.yaml`

## Reglas de Validación
- `capacity_slots >= 1`
- `slot_length_m >= required_reel_length`

## KPIs afectados
- Throughput por roll stand
- Waiting time en exchange

## Riesgos
- Exchange pequeño genera cuellos de botella

## Prioridad
- Alta
