# Algoritmo: Order Generation

## Propósito
Generar órdenes de producción con parámetros configurables (longitud objetivo, prioridad, producto) a partir de demanda planificada o reglas de replenishment.

## Precondiciones
- Configuración de plant geometry y parámetros de demanda disponibles.

## Postcondiciones
- Nuevas `ProductionOrder` añadidas a la cola de órdenes y eventos `CreateOrder` en `EventQueue`.

## Pseudocódigo
INICIO
  cada tick:
    if time_to_generate_next_order():
      order = crear_nueva_orden(id, product_code, target_length_m, due_time, priority)
      push_event('CreateOrder', order)
    end
  FIN

Complejidad: O(1) por tick (decisión local). Si se genera lote masivo: O(k) para k órdenes.

Excepciones
- Falta de parámetros de demanda → registrar alerta y usar valores por defecto.

KPIs afectados
- Throughput, On-time completion

Validación
- Verificar `target_length_m > 0` y `priority` en rango permitido.
