# Algoritmo: Transfer Scheduling

## Propósito
Planificar y despachar transfers (automáticos o manuales) optimizando secuencia y evitando conflictos en la red.

## Precondiciones
- Colas de requests, estado de transfers, disponibilidad de tracks/exchanges.

## Postcondiciones
- Transfer programado con ventana temporal; evento `TransferDeparted` creado a tiempo.

## Pseudocódigo
INICIO
  periodic (cada s o por evento):
    requests = collect_pending_transfer_requests()
    sort requests por priority, due_time
    for req in requests:
      candidates = find_transfers_available_at(req.earliest_start)
      for c in candidates:
        if route_is_free(c, req):
          assign_transfer(c, req)
          break
      if not assigned:
        escalate_or_queue(req)
  FIN

Complejidad: O(r * c) donde r=requests y c=available transfers (puede optimizarse).

Excepciones
- Transfer fault → reschedule dependent requests

KPIs afectados
- Transfer utilization, Average transfer delay

Validación
- Asegurar que `assigned.start_time` no colisione con otros movimientos reservados.
