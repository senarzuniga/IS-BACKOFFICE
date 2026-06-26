# Algoritmo: Track Assignment

## Propósito
Asignar tracks para movimientos (inbound/outbound/transfers) minimizando tiempo de viaje y evitando colisiones.

## Precondiciones
- Estado actual de ocupación de tracks y tiempo estimado de liberación.

## Postcondiciones
- Track reservado; `TrackOccupied` programado; plan de movimiento con timestamps.

## Pseudocódigo
INICIO
  on RequestTrack(move):
    available = filter(tracks, will_be_free_before(move.earliest_start))
    if available.empty():
      queued_moves.append(move)
      return
    score each track by (estimated_travel_time + congestion_factor)
    chosen = argmin(score)
    reserve_track(chosen, move)
    schedule_move_on_track(chosen, move)
  FIN

Complejidad: O(t) por solicitud, t = #tracks.

Excepciones
- Colisiones en tiempo real → replanificar con latencia mínima.

KPIs afectados
- Throughput por track, Congestion

Validación
- Verificar `track.length_m` >= required_clearance
