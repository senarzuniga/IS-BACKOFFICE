# 🖼️ Sistema de Scraping de IS-BACKOFFICE - Guía de Uso

## 📋 Descripción General

El sistema de scraping de imágenes de alta calidad permite extraer y descargar imágenes profesionales desde sitios web corporativos como INGECART, con filtros inteligentes de calidad y una interfaz visual intuitiva.

## 🚀 Inicio Rápido

### Opción 1: Interfaz Streamlit (Recomendado para usuarios)

```bash
# Activar entorno virtual
cd "C:\Users\Inaki Senar\Documents\GitHub\IS-BACKOFFICE"
.venv\Scripts\activate

# Ejecutar la aplicación
streamlit run streamlit_app.py
```

Luego:
1. Abre http://localhost:8501
2. Selecciona "🖼️ Scraping" en el sidebar
3. Ingresa la URL del sitio web
4. Configura parámetros (opcional)
5. Haz clic en "🚀 Iniciar Scraping"

### Opción 2: API REST (Para integraciones)

```bash
# En una terminal
uvicorn main:app --reload

# En otra terminal, hacer requests
curl -X POST http://localhost:8000/api/scraping/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.ingecart.eu", "max_images": 20}'
```

### Opción 3: Python (Para scripts)

```python
from backoffice.scraping.high_quality_scraper import scraper

# Scraping simple
results = scraper.scrape_website(
    url="https://www.ingecart.eu/",
    min_width=800,
    recursive=False
)

# Descargar imágenes
downloaded = scraper.download_images(results['images'], max_images=20)

print(f"✅ Descargadas {len(downloaded)} imágenes")
for img in downloaded:
    print(f"  - {img['filename']}: {img['width']}x{img['height']}px")
```

## 🎯 Características Principales

### Motor de Scraping
- **Extracción inteligente de alta resolución**: Busca srcset, data-srcset y atributos src
- **Filtros de calidad**: Descarta iconos y imágenes pequeñas automáticamente
- **Validación de dimensiones**: Asegura que las imágenes cumplan requisitos mínimos
- **Caché inteligente**: Evita redescargas innecesarias

### Interfaz Streamlit
- **Navegación intuitiva**: Sidebar con acceso a todos los módulos
- **Progreso visual**: Barra de progreso y mensajes en tiempo real
- **Galería de previsualizaciones**: Miniatura de hasta 8 imágenes
- **Exportación de datos**: Descargar metadatos en JSON
- **Historial**: Acceso rápido a sesiones anteriores

### API REST
- **Scraping asincrónico**: Procesamiento en segundo plano
- **Monitoreo de estado**: Seguimiento de tareas en tiempo real
- **Recuperación de resultados**: Obtener datos completados
- **Gestión de imágenes**: Listar y descargar archivos

## ⚙️ Configuración Avanzada

### Parámetros de Scraping

| Parámetro | Rango | Defecto | Descripción |
|-----------|-------|---------|------------|
| `url` | string | - | URL del sitio web (requerida) |
| `min_width` | 400-1920 px | 800 | Ancho mínimo de imágenes |
| `recursive` | true/false | false | Explorar enlaces internos |
| `max_pages` | 1-20 | 5 | Máximo de páginas a analizar |
| `max_images` | 5-200 | 50 | Máximo de imágenes a descargar |

### Filtros de Calidad

El motor evalúa cada imagen con una puntuación de 0-5:
- **+2 puntos**: Patrones de alta resolución en URL (large, hd, 1920w, etc.)
- **+1 punto**: Extensión webp o png
- **+1 punto**: Texto alt descriptivo (>20 caracteres)
- **+1 punto**: Clases CSS importantes (hero, banner, featured)

Solo se descargan imágenes con puntuación >= 3.

### Requisitos de Calidad

- Ancho mínimo: 800px (configurable)
- Alto mínimo: 600px
- Tamaño mínimo: 15 KB
- Formatos: JPG, PNG, WebP

## 📊 Ejemplos de Uso

### Ejemplo 1: Scraping Básico

```python
from backoffice.scraping.high_quality_scraper import scraper

# Descargar 20 imágenes de un sitio
results = scraper.scrape_website(
    url="https://www.ejemplo.com",
    min_width=800,
    recursive=False,
    max_pages=1
)

downloaded = scraper.download_images(results['images'], max_images=20)
print(f"Se descargaron {len(downloaded)} imágenes")
```

### Ejemplo 2: Scraping Recursivo

```python
# Explorar múltiples páginas del sitio
results = scraper.scrape_website(
    url="https://www.ejemplo.com",
    recursive=True,
    max_pages=5,
    min_width=1200
)

downloaded = scraper.download_images(results['images'], max_images=100)
```

### Ejemplo 3: Con Callbacks

```python
def progress_callback(message):
    print(f"[PROGRESO] {message}")

results = scraper.scrape_website(
    url="https://www.ejemplo.com",
    progress_callback=progress_callback
)
```

### Ejemplo 4: API Asincrónica

```python
import requests
import time

# Iniciar scraping
response = requests.post(
    "http://localhost:8000/api/scraping/scrape",
    json={
        "url": "https://www.ejemplo.com",
        "max_images": 50
    }
)

task_id = response.json()["task_id"]

# Monitorear progreso
while True:
    status = requests.get(f"http://localhost:8000/api/scraping/status/{task_id}").json()
    print(f"Estado: {status['status']} ({status.get('progress', 0)}%)")
    
    if status['status'] == 'completed':
        results = requests.get(f"http://localhost:8000/api/scraping/results/{task_id}").json()
        print(f"✅ Se descargaron {len(results['downloaded_images'])} imágenes")
        break
    
    time.sleep(2)
```

## 📁 Estructura de Archivos

```
scraped_images/              # Directorio de salida
├── 20260508_100000_800x600_abc12345.jpg
├── 20260508_100001_1920x1080_def67890.jpg
└── cache/                   # Caché de descargas
    ├── md5hash1.json
    └── md5hash2.json
```

## 🔍 Solución de Problemas

### El scraping es lento
- Reduce `max_pages` si está en modo recursivo
- Aumenta `min_width` para filtrar más imágenes
- Verifica la velocidad de tu conexión

### No se descargan imágenes
- Verifica que la URL es correcta y accesible
- Comprueba que el sitio no requiere JavaScript (usa BeautifulSoup)
- Aumenta `max_images` en caso de que sea muy restrictivo

### Error de permisos
- Asegúrate de tener permisos de escritura en la carpeta `scraped_images/`
- Verifica que la carpeta existe o se puede crear

## 📈 Estadísticas

Cada sesión de scraping genera estadísticas:
- **total_found**: Total de imágenes encontradas
- **downloaded**: Imágenes descargadas exitosamente
- **failed**: Descargas fallidas
- **filtered_out**: Imágenes rechazadas por calidad/tamaño

## 🔐 Consideraciones de Seguridad

- Respeta el archivo `robots.txt` del sitio
- No hagas scraping masivo/agresivo
- Usa `User-Agent` realista (incluido por defecto)
- Verifica los términos de servicio del sitio

## 📚 API Endpoints Reference

```
POST   /api/scraping/scrape              - Iniciar scraping
GET    /api/scraping/status/{task_id}    - Estado de tarea
GET    /api/scraping/results/{task_id}   - Resultados completados
GET    /api/scraping/images              - Listar imágenes
GET    /api/scraping/images/{filename}   - Descargar imagen
GET    /api/scraping/health              - Estado del servicio
DELETE /api/scraping/task/{task_id}      - Eliminar tarea
```

## 💡 Tips

1. **Para sitios dinámicos**: Si el sitio carga imágenes con JavaScript, considera usar Playwright (ver requirements.txt)
2. **Para mejor rendimiento**: Ejecuta el scraping en segundo plano usando la API
3. **Para integración**: Usa los endpoints REST para integrar en otros sistemas
4. **Para debugging**: Revisa el archivo de log y el caché en `scraped_images/cache/`

---

**Última actualización**: Mayo 8, 2026  
**Versión**: 1.0.0
