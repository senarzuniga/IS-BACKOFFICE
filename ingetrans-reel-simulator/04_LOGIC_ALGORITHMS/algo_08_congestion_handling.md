# Algoritmo: Congestion Handling

## Propósito
Detectar y mitigar congestiones en tracks, exchanges y zonas críticas mediante enrutamiento alternativo, throttling o reasignación de slots.

## Precondiciones
- Monitoreo de ocupación por tramo y umbrales configurables.

## Postcondiciones
- Acciones de mitigación (replanificación, retraso, reroute) aplicadas y registradas.

## Pseudocódigo
INICIO
  monitor occupancy per track/exchange
  if occupancy > threshold_high:
    identify incoming_moves within horizon
    for move in incoming_moves:
      if alternative_route_available(move):
        reroute(move)
      else:
        delay(move) with exponential_backoff
  if persist > threshold_time: escalate (increase maintenance or open temporary holding)
  FIN

Complejidad: O(n) con n = #moves in horizon

Excepciones
- No route alternativo → aplicar buffering en upstream warehouse

KPIs afectados
- Congestion level, Average delay

Validación
- Simular escenario de congestión y confirmar mitigaciones reducen ocupación.
