# Algoritmo: Reel Allocation

## Propósito
Asignar bobinas (`Reel`) a órdenes de producción considerando compatibilidades (gramaje, ancho), stock disponible y optimización de leftovers.

## Precondiciones
- Lista de reels en almacén, orden activa o inminente.

## Postcondiciones
- Reel reservado para la orden; evento `ReelAssigned` generado; si no hay reel, orden marcada como `BLOCKED` y se genera solicitud de aprovisionamiento.

## Pseudocódigo
INICIO
  on OrderReadyToAllocate(order):
    candidates = filter(reels_in_warehouse, matches(order.paper_grade, order.width))
    if candidates.empty():
      mark_order_blocked(order)
      push_event('RequestReelSupply', order)
      return
    sort candidates by (suitable_preference: smallest_waste, FIFO)
    selected = candidates[0]
    reserve_reel(selected, order)
    push_event('ReelAssigned', {order_id: order.id, reel_id: selected.id})
  FIN

Complejidad: O(n log n) por asignación (ordenado de candidatos).

Excepciones
- Reels con datos inconsistentes → descartar y registrar.

KPIs afectados
- Stock accuracy, Average assign time, Reel utilization

Validación
- `selected.remaining_m >= min_required_m` antes de confirmar asignación.
