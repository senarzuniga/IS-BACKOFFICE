BOBINA LOAD SIMULATOR
======================

Instrucciones rápidas para el módulo `bobina_load_simulator`.

Instalación
-----------

1. Asegúrate de tener el entorno del proyecto activado (`.venv`).
2. Ejecuta: `streamlit run pages/bobina_load_simulator.py`.

Estructura principal
--------------------

- `pages/bobina_load_simulator.py`: Panel Streamlit principal.
- `core/bobina_simulation_engine.py`: Motor step-based.
- `agents/bobina_simulator/`: Agentes para configuración, órdenes y ROI.
- `data/bobina_simulator`: Configuración y resultados de simulaciones.

Notas
-----

Este entregable es un prototipo inicial pensado para iterar. Los agentes y
el motor son implementaciones mínimas y documentadas para su extensión.
