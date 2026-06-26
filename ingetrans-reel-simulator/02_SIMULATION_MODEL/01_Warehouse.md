# Warehouse

## Propósito
Modelar el almacén donde se recibe, almacena y despacha `Reel`s. Gestiona ubicación física, capacidad, asignación de slots y coordinación con `Forklift` / `Transfer`.

## Atributos
| Atributo | Tipo | Unidad | Default | Min | Max | Obligatorio |
|----------|------|--------|---------:|----:|----:|:-----------:|
| id | string | - | auto | - | - | Sí |
| name | string | - | "Main Warehouse" | - | - | Sí |
| location_x | float | m | 0.0 | -1000 | 1000 | Sí |
| location_y | float | m | 0.0 | -1000 | 1000 | Sí |
| capacity_kg | float | kg | 100000.0 | 0 | 1e9 | Sí |
| capacity_units | int | uds | 1000 | 0 | 100000 | Sí |
| storage_slots | int | uds | 200 | 1 | 100000 | Sí |
| slot_length_m | float | m | 12.0 | 0.5 | 100.0 | Sí |
| slot_width_m | float | m | 1.2 | 0.2 | 10.0 | Sí |
| slot_max_weight_kg | float | kg | 2000.0 | 10 | 1e6 | Sí |
| inbound_rate_per_hour | float | reels/h | 20.0 | 0 | 1000 | No |
| outbound_rate_per_hour | float | reels/h | 18.0 | 0 | 1000 | No |
| allowed_paper_grades | list | - | ["A","B"] | - | - | No |
| operating_hours | string | hh:mm-hh:mm | "06:00-22:00" | - | - | Sí |
| reorder_point_units | int | uds | 50 | 0 | 100000 | No |
| safety_stock_units | int | uds | 20 | 0 | 100000 | No |

## States (State Machine)
- IDLE → RECEIVING → STORING → READY
- READY → PICKING → LOADING → SHIPPED → READY
- ANY → MAINTENANCE → IDLE

## Inputs
- Incoming `ReelArrived` events (inbound deliveries)
- `ProductionOrder` requests (pick lists)
- `TransferRequest` / `ForkliftDispatch` commands
- Operator interventions (manual put-away / retrieval)

## Outputs
- `ReelStored` events (slot assignment)
- `ReelPicked` events (location cleared)
- `StorageStatus` snapshots (occupancy, free slots)
- Alerts (capacity exceeded, violations)

## Relaciones
- pertenece_a → Plant / Scenario
- coordina_con → Forklift, Transfer, Operator
- almacena → Reel
- abastece → RollStand / Corrugator (vía ProductionOrder)

## Lifecycle
1. Creación (configuración inicial)
2. Activación (estado operativo)
3. Operación diaria (recepciones, almacenaje, picking)
4. Mantenimiento (limpieza, reorganización)
5. Baja (decomisionamiento)

## Parámetros de Configuración
Referenciar: `03_CONFIG_DATABASE/config_warehouse.yaml`

## Reglas de Validación
- `capacity_kg > 0`
- `capacity_units >= storage_slots`
- `slot_length_m`, `slot_width_m` > 0
- `slot_max_weight_kg >= promedio_peso_reel`
- Horario `operating_hours` usa formato 24h `HH:MM-HH:MM`

## KPIs afectados
- Storage utilization (%)
- Average put-away time (s)
- Average pick time (s)
- Inventory turns
- Fill rate vs reorder point

## Riesgos
- Configuración de capacidad incorrecta (unidades vs kg)
- Slots mal dimensionados (no encajan reels reales)
- Horarios inconsistentes con production shifts

## Prioridad
- Alta
