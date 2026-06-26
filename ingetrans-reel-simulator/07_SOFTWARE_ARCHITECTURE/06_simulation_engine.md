# Simulation Engine

## Propósito
Definir la arquitectura del motor de simulación (core): `SimulationClock`, `EventQueue`, `Scheduler`, y `EntityManager`.

## Componentes
- `SimulationClock` — avanza tiempo por ticks y emite `Tick` events.
- `EventQueue` — cola priorizada para eventos discretos.
- `Scheduler` — asigna ejecución de eventos en ticks, maneja retries.
- `EntityManager` — registro y acceso a entidades por ID.

## Consideraciones de diseño
- Determinismo: usar seeds para todos los generadores estocásticos.
- Performance: soporte para ejecuciones en paralelo por escenario (no por entidad).
