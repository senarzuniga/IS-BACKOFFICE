# Bobina Load Simulator

Panel comparativo Forklift vs INGETRANS.

Ejecución:

```bash
streamlit run pages/bobina_load_simulator.py
```

Controla el número de carretillas, velocidad de simulación e inyecta eventos desde la barra lateral.

La geometría base está en `assets/layout_common.json`. Extensiones en `assets/layout_forklift.json` y `assets/layout_ingetrans.json`.

KPIs y ROI son calculados en `utils/kpi_calculator.py`.

Notas:
- El motor corre paso a paso en incrementos de 0.1 minutos.
- Render con PIL en `utils/canvas_renderer.py`.
