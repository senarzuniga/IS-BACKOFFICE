# Modules Overview

## Propósito
Describir los módulos de software, sus responsabilidades y límites.

## Módulos propuestos
- `core_simulation` : kernel del motor de simulación (clock, event queue, scheduler)
- `models` : definiciones de entidades (Reel, Forklift, Transfer, Track, etc.)
- `engines` : submódulos (physical_engine, logistic_engine, production_engine, financial_engine, kpi_engine)
- `config` : carga y validación de YAML, overrides por escenario
- `api` : capa REST para lanzar simulaciones, consultar estados y descargar resultados
- `persistence` : adaptadores para SQLite/Postgres (schema definido)
- `analytics` : post-process y generación de KPIs y reports
- `ui_adapter` : adaptador para dashboards y visualizadores externos (export-only)
- `tools` : utilidades (validators, seedable random, metrics)

## Dependencias externas
- `PyYAML` para parsing de configuraciones
- `SQLAlchemy` para persistencia (opcional)
- `numpy/pandas` para análisis y sensivity
