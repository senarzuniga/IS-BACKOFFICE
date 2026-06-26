# Algoritmo: Financial Calculation

## Propósito
Calcular costes y métricas financieras por escenario (CAPEX amortizado, OPEX, coste por tonelada, ROI simple).

## Precondiciones
- Parametrización financiera (CAPEX, OPEX, tasas, horizonte) disponible.

## Postcondiciones
- Reporte financiero por escenario (costes, ingresos estimados, ROI, payback).

## Pseudocódigo
INICIO
  on ScenarioComplete(run_results):
    total_opex = sum(run_results.operational_costs)
    capex_ann = amortize(capex, life_years, discount_rate)
    revenue = compute_revenue(run_results.production)
    roi = (revenue - (total_opex + capex_ann)) / (total_opex + capex_ann)
    generate_financial_report({total_opex, capex_ann, revenue, roi})
  FIN

Complejidad: O(1) por resumen, O(n_periods) si hay desglose temporal

Excepciones
- Missing cost drivers → usar supuestos y anotar incertidumbre

KPIs afectados
- Total cost, ROI, Payback

Validación
- Reconciliar suma de costes con desglose operacional
