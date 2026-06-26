# Algoritmo: OEE Calculation

## Propósito
Calcular OEE (Availability × Performance × Quality) para equipos y para planta agregada.

## Precondiciones
- Registro de tiempo operativo, paradas planificadas, piezas buenas/defectuosas.

## Postcondiciones
- KPI `OEE` actualizado por intervalo y summary final al terminar la simulación.

## Pseudocódigo
INICIO
  periodic (cada sampling_interval):
    for machine in monitored:
      planned_time = compute_planned_time(machine)
      run_time = compute_run_time(machine)
      availability = run_time / planned_time if planned_time>0 else 0
      performance = actual_output / theoretical_output
      quality = good_output / total_output
      oee = availability * performance * quality
      record_kpi(machine, 'OEE', oee)
  FIN

Complejidad: O(machines) por muestreo

Excepciones
- Datos de producción incompletos → excluir del cálculo temporalmente

KPIs afectados
- OEE, Availability, Performance, Quality

Validación
- Comparar con cálculos manuales y con históricos
