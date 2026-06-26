# KPI Templates

Describe cómo calcular y muestrear KPIs durante la ejecución:

- Throughput: contadores por `production_order.completed` por ventana de 1 hora.
- OEE: calcular availability (uptime / scheduled_time), performance (actual_speed / nominal_speed), quality (1 - scrap_ratio).
- Avg Inventory Days: muestrear inventario cada hora y convertir a días según demanda diaria.

Notas: Usar `kpi_engine` para agregar y emitir snapshots cada `kpi_snapshot_interval_s`.
