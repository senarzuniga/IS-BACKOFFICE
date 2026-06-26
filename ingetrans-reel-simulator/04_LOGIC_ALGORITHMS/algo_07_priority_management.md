# Algoritmo: Priority Management

## Propósito
Resolver conflictos entre tareas y recursos aplicando reglas de prioridad, SLA y criticidad de máquinas.

## Precondiciones
- Cada tarea tiene `priority`, `due_time`, y `criticality`.

## Postcondiciones
- Cola de tareas ordenada y decisiones de preempción si procede.

## Pseudocódigo
INICIO
  function compare_tasks(a,b):
    score_a = w1*a.priority + w2*urgency(a) + w3*criticality(a)
    score_b = w1*b.priority + w2*urgency(b) + w3*criticality(b)
    return score_a > score_b

  when resource_free: select highest scoring task
  if new_task has higher score than running_task and preemptible(running_task):
    preempt running_task
    start new_task
  FIN

Complejidad: O(log n) por inserción en heap prioridad.

Excepciones
- Tareas no preemtibles → usar fallback schedules

KPIs afectados
- On-time completion, Average delay

Validación
- Verificar que `preemption` respete restricciones de seguridad y producción.
