# Algoritmo: Warehouse Selection

## Propósito
Seleccionar el almacén o zona de stock óptima para suministrar una orden o recibir una entrega, balanceando distancia, coste y frescura del stock.

## Precondiciones
- Mapa de almacenes con coordenadas y capacidades; lista de reels disponibles por ubicación.

## Postcondiciones
- Elegido `warehouse_id` y reservado el stock; evento `ReelStoreSelected`.

## Pseudocódigo
INICIO
  function select_warehouse(candidates, weights):
    scores = []
    for w in candidates:
      score = weights.distance*distance(w, target) + weights.cost*move_cost(w) + weights.age*average_age(w)
      scores.append((w, score))
    chosen = argmin(scores)
    return chosen
  FIN

Complejidad: O(m) para m almacenes candidatos.

Excepciones
- Si todos los almacenes están llenos → fallback a proveedor externo o agente de alerta.

KPIs afectados
- Move cost, Average lead time

Validación
- `chosen.capacity` debe ser suficiente; `distance` calculada en m.
