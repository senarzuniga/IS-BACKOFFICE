# Algoritmo: Sensitivity Analysis

## Propósito
Evaluar la sensibilidad de KPIs frente a variaciones de parámetros clave (velocidades, MTBF, costes) mediante muestreo factorial o Monte Carlo.

## Precondiciones
- Definición del conjunto de parámetros a variar y rangos/estadísticas.

## Postcondiciones
- Conjunto de escenarios generados y matriz de resultados KPI vs parámetros.

## Pseudocódigo
INICIO
  for param_set in generate_parameter_samples(method, n_samples):
    run = run_simulation_with_overrides(param_set)
    collect run.kpis
  analyze_sensitivity(results)
  output tornado_chart, correlation_matrix
  FIN

Complejidad: O(n_samples * cost_per_run) (paralelizable)

Excepciones
- Runs fallidos → registrar y excluir del análisis

KPIs afectados
- Todos (dependiendo del análisis)

Validación
- Reproducibilidad: mismas semillas producen mismos resultados
