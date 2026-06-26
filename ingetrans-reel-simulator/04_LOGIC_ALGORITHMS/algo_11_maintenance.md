# Algoritmo: Maintenance

## Propósito
Planificar y ejecutar mantenimientos preventivos y correctivos minimizando impacto en producción.

## Precondiciones
- Horas de operación, historial de fallos, calendario de mantenimiento.

## Postcondiciones
- Órdenes de mantenimiento programadas y equipos marcados `OUT_OF_SERVICE` durante la ventana.

## Pseudocódigo
INICIO
  periodic_check():
    for eq in equipments:
      if eq.operating_hours >= eq.preventive_threshold and not eq.preventive_scheduled:
        schedule_maintenance(eq, preferred_window)
  on MachineFailure(event):
    create_corrective_maintenance_order(event.equipment_id, event.severity)
  FIN

Complejidad: O(e)

Excepciones
- Ventana de mantenimiento no disponible → escalado y reorganización de producción

KPIs afectados
- MTTR, Availability

Validación
- Simular calendario y comprobar que mantenimientos se ejecutan dentro de ventanas
