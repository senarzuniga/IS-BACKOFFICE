REEL LOAD SIMULATOR
=====================

Quick start (RC1)
------------------

Goal: entregar una versión ejecutable y estable (RC1) del simulador
Reel Load Simulator para uso diario. RC1 es un lanzador "headless" que
ejecuta el runner mínimo y escribe resultados en `ingetrans-reel-simulator/outputs/`.

Prerequisitos
-------------

1. Activar el entorno virtual del repo (Windows PowerShell):

	```powershell
	& ".venv\Scripts\Activate.ps1"
	```

2. Instalar dependencias mínimas (ya incluidas en `requirements.txt`):

	```bash
	pip install -r requirements.txt
	```

Ejecutar RC1 (un comando)
--------------------------

Desde la raíz del repo, ejecutar el lanzador RC1 (cross-platform):

```bash
python scripts/run_reel_rc1.py --duration 600
```

Esto lanzará el runner mínimo (ingetrans-reel-simulator/scripts/run_simulator.py)
con el escenario por defecto y escribirá `run_summary.json` y `event_log.csv`
en `ingetrans-reel-simulator/outputs/<run_id>/`.

Si prefieres invocar directamente el script del simulador:

```bash
python ingetrans-reel-simulator/scripts/run_simulator.py --duration 600
```

Entradas y escenarios
---------------------

Los escenarios YAML se encuentran en `ingetrans-reel-simulator/06_SCENARIOS/`.
El lanzador RC1 usa por defecto `scenario_01_baseline_forklift.yaml`.

Notas de producto (RC1)
----------------------

- RC1 provee un runner headless estable y reproducible para demos y pruebas.
- No cambia la arquitectura general: se prioriza la usabilidad.
- UI Streamlit y Job API siguen disponibles pero no son necesarias para RC1.

Siguientes pasos sugeridos
-------------------------

- Validar outputs con casos reales y anexar scenarios de clientes.
- Añadir un pequeño script de sanity-check para aceptar RC1 automáticamente.
- Empaquetar RC1 como release (tar/zip) si se aprueba.

Licencia y créditos
-------------------

Módulo prototipo preparado por el equipo de IS-BACKOFFICE para Ingecart.

