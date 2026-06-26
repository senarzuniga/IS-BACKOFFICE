# Risks and Assumptions

## Riesgos
- Falta de datos reales para calibración (Impacto: alto). Mitigación: usar level3_historical_validation cuando esté disponible.
- Suposición de determinismo en engine; riesgos de replicabilidad si librerías externas introducen nondeterminism.

## Hipótesis
- Todos los tiempos en configuración están en segundos.
- `.` es separador decimal en YAML.
