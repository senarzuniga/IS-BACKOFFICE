# Classes

## Propósito
Definir las principales clases del sistema, atributos clave y métodos públicos (solo diseño).

## Ejemplos de clases
- `SimulationClock`:
  - attrs: `current_time`, `tick_s`, `end_time`
  - methods: `start()`, `pause()`, `tick()`, `stop()`
- `EventQueue`:
  - attrs: `queue` (priority structure)
  - methods: `push(event)`, `pop()`, `cancel(event_id)`
- `Reel`:
  - attrs: `id`, `width_mm`, `length_m`, `remaining_m`, `mass_kg`, `status`
  - methods: `consume(m)`, `assign_to(order_id)`
- `Forklift`, `Transfer`, `Corrugator`, `RollStand` — clases con estados y controladores minimalistas

## Consideraciones
- Mantener POCO estado mutable fuera del EventQueue para facilitar reproducibilidad.
