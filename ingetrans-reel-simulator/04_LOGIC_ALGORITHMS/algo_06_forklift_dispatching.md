# Algoritmo: Forklift Dispatching

## Propósito
Despachar carretillas a tareas optimizando distancia, prioridad y nivel de batería/opciones operativas.

## Precondiciones
- Cola de tareas, listado de forks (estado, posición, battery).

## Postcondiciones
- Fork asignado a tarea; evento `ForkliftArrived` y `ForkliftCompletedTask` en su ciclo.

## Pseudocódigo
INICIO
  on NewTask(task):
    idle_forks = filter(forks, state == IDLE and battery > threshold)
    if idle_forks.empty():
      queue_task(task)
      return
    best = argmin(idle_forks, distance_to_task)
    assign(best, task)
    push_event('ForkliftDispatch', {fork_id: best.id, task_id: task.id})
  periodic: try_assign_queued_tasks()
  FIN

Complejidad: O(f) per task (f = #forklifts).

Excepciones
- Battery low during task → interrupt and reassign

KPIs afectados
- Forklift utilization, Average move time

Validación
- `best.capacity_kg >= task.load_weight` antes de asignar.
