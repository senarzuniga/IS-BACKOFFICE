# Algoritmo: Simulation End Conditions

## Propósito
Determinar condiciones que terminan una corrida de simulación: tiempo máximo, orders completadas, estabilidad de KPIs, o número de eventos procesados.

## Precondiciones
- Parámetros de salida en `config_simulation_clock.yaml` o `config_master`.

## Postcondiciones
- `SimulationEnded` emitido y proceso de cierre ejecutado (resumen de KPIs y dump de logs).

## Pseudocódigo
INICIO
  after each tick or event:
    if current_time >= end_time_configured: finish
    if all_orders_completed and no_pending_events: finish
    if kpi_stability_detected(window, tolerance): finish (opcional)
  FIN

Complejidad: O(1) por evaluación

Excepciones
- Fallback: forzar final si supera max_runtime absoluta

KPIs afectados
- None (control flow)

Validación
- Probar cada condición con escenarios unitarios
