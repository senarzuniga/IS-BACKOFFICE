# Algoritmo: Starvation Prediction

## Propósito
Predecir la posible inanición (starvation) de un `RollStand` o máquina de producción antes de que ocurra y disparar acciones preventivas.

## Precondiciones
- Consumo actual de la máquina, tiempo hasta la próxima entrega programada, stock en buffers.

## Postcondiciones
- Si riesgo > umbral: generar `ReelChangeRequest` urgente o subir prioridad a transfer.

## Pseudocódigo
INICIO
  for each rollstand:
    projected_remaining_time = compute_remaining_time(installed_reel.remaining_m, consumption_rate)
    if projected_remaining_time < safety_margin:
      schedule_preemptive_transfer(rollstand)
      notify_scenario_manager(rollstand)
  FIN

Complejidad: O(r) r = #rollstands

Excepciones
- Consumos erráticos → usar ventana móvil y percentiles para robustez

KPIs afectados
- Starvation events, Unplanned downtime

Validación
- Test de stress con variaciones de consumo y latencias de entrega
