# 01_ARCHITECTURE_REPORT

Propósito: Documentar la arquitectura del modelo de simulación para el "Reel Loading Simulator V4". Este documento identifica entidades, recursos, eventos, state machines, parámetros configurables, KPIs, variables financieras, reportes y reglas de validación.

## Entidades identificadas
- Warehouse
- Exchange
- Transfer
- Track
- RollStand
- Corrugator
- Forklift
- AutomaticTransfer (INGETRANS)
- Operator
- Reel
- ProductionOrder
- PaperGrade
- Shift
- Maintenance
- Failure
- SimulationClock
- EventQueue
- KPIEngine
- FinancialEngine
- AnimationEngine
- ScenarioManager
- AGV (preparado)

## Recursos
- Material: Reels (stock), Pallets, Packaging
- Equipamiento móvil: Forklifts, Transfer Units, AGVs
- Infrastructure: Tracks, Exchanges, Roll Stands, Corrugators
- Humanos: Operators, Maintenance Crew
- Software: Event Queue, KPI Engine, Financial Engine

## Eventos clave
- ReelArrived
- ReelStored
- ReelAssigned
- ReelPicked
- ReelLoadedOnTransfer
- TransferDeparted
- TransferArrived
- ForkliftDispatch
- ReelChange (en producción)
- MachineFailure
- MaintenanceStart / MaintenanceEnd
- ShiftStart / ShiftEnd
- ProductionOrderCreated / Completed

## State machines (resumen por tipo)
- `Forklift`: IDLE → ASSIGNED → MOVING → LOADING → UNLOADING → RETURNING → MAINTENANCE
- `Transfer`/`AutomaticTransfer`: IDLE → SCHEDULED → MOVING → LOADING → UNLOADING → IDLE
- `Reel`: INBOUND → STORED → ASSIGNED → IN_TRANSIT → INSTALLED → CONSUMED → DISCARDED
- `ProductionOrder`: NEW → SCHEDULED → RUNNING → PAUSED → COMPLETED

## Parámetros configurables (ejemplos)
- Distancias (m), Velocidades (m/s), Aceleraciones (m/s²)
- Capacidades de almacén (kg, uds)
- MTBF (h), MTTR (min)
- Costes: labor (€/h), energía (€/kWh), mantenimiento (€/h)
- Horarios y turnos
- Configuración de la planta: número de Roll Stands, tracks por stand, longitudes

## KPIs principales
- Throughput (m/min, t/day)
- OEE (overall equipment effectiveness)
- Utilización de recursos (%)
- Tiempo medio de espera por reel (s)
- Tiempo de ciclo de transfer/forklift (s)
- MTBF / MTTR
- Inventory turns, Fill rate
- Costes operativos y ROI

## Variables financieras
- CAPEX por sistema (Forklift vs INGETRANS)
- OPEX: energía, mano de obra, mantenimiento
- Coste por transporte de reel
- Ingresos por producción extra (si aplica)

## Reportes a generar
- Run summary (KPIs agregados)
- Timeline de eventos (por entidad)
- Inventario por hora/día
- Cost & ROI report por escenario
- Logs de fallos y mantenimientos
- Detalle de asignaciones y tiempos de espera

## Reglas de validación (ejemplos)
- Todas las distancias > 0, unidades en metros.
- Capacidades y masas > 0; gramajes en g/m².
- MTBF > MTTR (sentido operativo)
- Cross-check: `total_tracks == tracks_per_rollstand * number_rollstands`.
- Config_master.yaml debe referenciar a todos los configs hijos existentes.

## Conclusión y siguientes pasos
1. Validar este reporte con stakeholders (ingeniería, operaciones, finanzas).
2. Tras aprobación, generar los 22 archivos de entidad en `02_SIMULATION_MODEL/` siguiendo la plantilla estándar.
3. Crear la base de configuración en `03_CONFIG_DATABASE/` y definir `config_master.yaml`.
