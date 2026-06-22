# Panel de Inteligencia Competitiva — IS-BACKOFFICE

Instrucciones rápidas para ejecutar el panel de inteligencia competitiva localmente.

1. Crear y activar virtualenv

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Instalar dependencias (módulo competitivo)

```powershell
pip install -r requirements_competitive_intelligence.txt
playwright install chromium
```

3. Copiar `.env.example` a `.env` y rellenar claves (`OPENAI_API_KEY`, `NEWSAPI_KEY` si las tienes).

4. Rellenar `data/competitive_intelligence/ingecart_baseline.json` con tus datos canónicos de Ingecart.

5. Ejecutar demo local (sin web):

```powershell
python scripts/run_demo.py --company PARA --no-web
```

6. Ejecutar panel Streamlit:

```powershell
streamlit run pages/competitive_intelligence.py
```

Notas:
- El modo `--no-web` permite validar el pipeline sin acceder a la red.
- Los jobs se guardan en `data/competitive_intelligence/jobs/` y los informes en `data/competitive_intelligence/reports/`.
