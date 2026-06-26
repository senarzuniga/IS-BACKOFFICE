# Dashboard

## Propósito
Definir arquitectura del dashboard que consume los endpoints API para mostrar KPIs, timelines y exports.

## Componentes
- Frontend (separado): React/Streamlit que llama a la API REST
- Backend: endpoints de `api` definidos en `04_api_rest.md`

## Vistas principales
- Run Summary
- Timeline (event log)
- Inventory heatmap
- Scenario comparison (table + charts)
