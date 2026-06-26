# Algoritmo: Failure Generation

## Propósito
Generar fallos estocásticos en equipos basados en MTBF y modelos de probabilidad (exponencial / Weibull) y clasificar severidad.

## Precondiciones
- Parámetros MTBF/MTTR por equipo disponibles en configuración.

## Postcondiciones
- `MachineFailure` insertado en `EventQueue` con timestamp de fallo y severidad.

## Pseudocódigo
INICIO
  for each equipment in monitored:
    if next_failure_time not set:
      next_failure_time = current_time + sample_failure_interval(mtbf)
    if current_time >= next_failure_time:
      severity = sample_severity()
      push_event('MachineFailure', {equipment_id, severity})
      next_failure_time = current_time + sample_repair_time(mttr)
  FIN

Complejidad: O(e) por tick (e = #equipments)

Excepciones
- Datos MTBF ausentes → usar defaults y anotar incertidumbre

KPIs afectados
- MTBF, Downtime

Validación
- Comparar histogramas de fallos simulados con históricos (nivel3 calibration)
