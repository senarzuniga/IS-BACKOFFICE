# Algoritmo: Recovery

## Propósito
Procedimientos automáticos para recuperación ante fallos: reasignar recursos, usar redundancias, y restablecer órdenes pendientes.

## Precondiciones
- Falta de disponibilidad de un recurso (MachineFailure) detectada y registrada.

## Postcondiciones
- Tareas re-asignadas o re-priorizadas; mantenimiento convocado; KPI de downtime actualizado.

## Pseudocódigo
INICIO
  on MachineFailure(event):
    affected_tasks = find_tasks_assigned_to(event.equipment_id)
    for t in affected_tasks:
      alt = find_alternative_resource(t)
      if alt:
        reassign_task(t, alt)
      else:
        queue_task_with_high_priority(t)
    call maintenance_team(event.equipment_id)
  FIN

Complejidad: Depende del número de tareas afectadas; worst-case O(n_tasks)

Excepciones
- Ninguna alternativa disponible → marcar impacto y notificar a gestión

KPIs afectados
- Recovery time, Unplanned downtime

Validación
- Simular fallo y verificar reasignaciones y tiempos de recuperación
