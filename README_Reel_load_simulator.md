REEL LOAD SIMULATOR
=====================

Instrucciones rápidas para el módulo `Reel_load_simulator`.

Instalación
-----------

1. Asegúrate de tener el entorno del proyecto activado (`.venv`).
2. Ejecuta: `streamlit run pages/Reel_load_simulator.py`.

Estructura principal
--------------------

- `pages/Reel_load_simulator.py`: Panel Streamlit principal.
- `core/Reel_load_simulator.py`: Motor step-based.
- `agents/Reel_load_simulator/`: Agentes para configuración, órdenes y ROI.
- `data/Reel_load_simulator`: Configuración y resultados de simulaciones.

Notas
-----

Este entregable es un prototipo inicial pensado para iterar. Los agentes y
el motor son implementaciones mínimas y documentadas para su extensión.
