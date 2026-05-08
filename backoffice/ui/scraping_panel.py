import streamlit as st
from backoffice.scraping.high_quality_scraper import scraper
import pandas as pd
from datetime import datetime
import json
import os
from PIL import Image
import plotly.express as px

class ScrapingPanel:
    """
    Panel de control para scraping de imágenes de alta calidad
    Interfaz humana intuitiva con feedback visual
    """
    
    def __init__(self):
        if 'scraping_results' not in st.session_state:
            st.session_state.scraping_results = None
        if 'scraping_history' not in st.session_state:
            st.session_state.scraping_history = []
    
    def render(self):
        """Renderiza el panel completo de scraping"""
        
        st.markdown("""
        <style>
        .scraping-card {
            background: linear-gradient(135deg, #1e293b, #0f172a);
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
            border: 1px solid #334155;
        }
        .quality-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }
        .quality-high { background: #10b981; color: white; }
        .quality-medium { background: #f59e0b; color: white; }
        .quality-low { background: #ef4444; color: white; }
        </style>
        """, unsafe_allow_html=True)
        
        st.title("🖼️ Agente de Scraping de Alta Calidad")
        st.markdown("*Extrae imágenes profesionales con resolución óptima para tu backoffice*")
        
        # Configuración principal
        col1, col2 = st.columns([2, 1])
        
        with col1:
            url = st.text_input(
                "🌐 URL del sitio web",
                placeholder="https://www.ejemplo.com",
                help="Ingresa la URL completa del sitio que quieres analizar"
            )
        
        with col2:
            max_images = st.number_input(
                "📸 Máximo de imágenes",
                min_value=5,
                max_value=200,
                value=50,
                help="Número máximo de imágenes a descargar"
            )
        
        # Opciones avanzadas en expander
        with st.expander("⚙️ Configuración avanzada"):
            col_adv1, col_adv2, col_adv3 = st.columns(3)
            
            with col_adv1:
                min_width = st.slider(
                    "Ancho mínimo (px)",
                    min_value=400,
                    max_value=1920,
                    value=800,
                    help="Imágenes con ancho menor serán ignoradas"
                )
            
            with col_adv2:
                recursive = st.checkbox(
                    "🔍 Scraping recursivo",
                    value=False,
                    help="Explora enlaces internos del sitio"
                )
            
            with col_adv3:
                if recursive:
                    max_pages = st.number_input(
                        "Máximo de páginas",
                        min_value=1,
                        max_value=20,
                        value=5
                    )
                else:
                    max_pages = 1
            
            st.markdown("---")
            st.markdown("**📋 Tipos de contenido a priorizar:**")
            content_types = st.multiselect(
                "",
                ["Banners hero", "Imágenes de productos", "Logos corporativos", "Galerías", "Backgrounds"],
                default=["Banners hero", "Imágenes de productos"]
            )
        
        # Botón de ejecución
        if st.button("🚀 Iniciar Scraping", type="primary", width='stretch'):
            if not url:
                st.error("Por favor ingresa una URL válida")
            else:
                self._execute_scraping(url, min_width, recursive, max_pages, max_images, content_types)
        
        # Mostrar resultados si existen
        if st.session_state.scraping_results:
            self._display_results()
        
        # Mostrar historial
        if st.session_state.scraping_history:
            self._display_history()
    
    def _execute_scraping(self, url, min_width, recursive, max_pages, max_images, content_types):
        """Ejecuta el proceso de scraping con feedback visual"""
        
        # Crear contenedor para progreso
        progress_container = st.container()
        
        with progress_container:
            st.markdown("### 🔄 Progreso del Scraping")
            
            # Barra de progreso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(message):
                status_text.markdown(f"🔄 {message}")
            
            # Paso 1: Análisis
            status_text.markdown("🔍 **Paso 1/3:** Analizando estructura del sitio...")
            progress_bar.progress(10)
            
            # Scraping
            results = scraper.scrape_website(
                url=url,
                min_width=min_width,
                recursive=recursive,
                max_pages=max_pages,
                progress_callback=update_progress
            )
            
            progress_bar.progress(50)
            status_text.markdown("⬇️ **Paso 2/3:** Descargando imágenes de alta calidad...")
            
            # Descarga
            if results['images']:
                downloaded = scraper.download_images(
                    results['images'],
                    max_images=max_images,
                    progress_callback=update_progress
                )
                results['downloaded_images'] = downloaded
            else:
                results['downloaded_images'] = []
            
            progress_bar.progress(100)
            status_text.markdown("✅ **Paso 3/3:** ¡Proceso completado!")
            
            # Guardar en sesión
            st.session_state.scraping_results = results
            
            # Guardar en historial
            st.session_state.scraping_history.insert(0, {
                'timestamp': datetime.now(),
                'url': url,
                'total_images': len(results.get('downloaded_images', [])),
                'pages_scraped': len(results.get('pages_scraped', [])),
                'results': results
            })
            
            # Limitar historial a 10 items
            st.session_state.scraping_history = st.session_state.scraping_history[:10]
            
            st.success(f"✅ Completado! Se descargaron {len(downloaded)} imágenes de alta calidad")
            st.rerun()
    
    def _display_results(self):
        """Muestra los resultados del scraping"""
        
        results = st.session_state.scraping_results
        downloaded = results.get('downloaded_images', [])
        
        st.markdown("---")
        st.markdown("## 📊 Resultados del Scraping")
        
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total encontradas", results['stats']['total_found'])
        with col2:
            st.metric("Descargadas", len(downloaded))
        with col3:
            st.metric("Páginas analizadas", len(results.get('pages_scraped', [])))
        with col4:
            st.metric("Calidad media", f"{self._avg_quality(downloaded):.1f}/5")
        
        # Tabla de imágenes descargadas
        if downloaded:
            st.markdown("### 🖼️ Imágenes Descargadas")
            
            # Convertir a DataFrame para mostrar
            df_data = []
            for img in downloaded:
                df_data.append({
                    'Archivo': img['filename'],
                    'Dimensiones': f"{img['width']}x{img['height']}",
                    'Tamaño': f"{img['size_kb']:.1f} KB",
                    'Calidad': f"{img['quality_score']}/5"
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, width='stretch')
            
            # Galería de miniaturas
            st.markdown("### 🎨 Vista previa")
            
            # Mostrar en grid
            cols = st.columns(4)
            for idx, img in enumerate(downloaded[:8]):  # Máximo 8 preview
                with cols[idx % 4]:
                    try:
                        image = Image.open(img['filepath'])
                        st.image(image, caption=img['filename'][:30], width='stretch')
                        
                        # Botón para ver detalles
                        if st.button(f"📋 Detalles", key=f"detail_{idx}"):
                            st.json(img)
                    except Exception as e:
                        st.warning(f"No se pudo cargar: {img['filename']}")
            
            # Botón de descarga masiva
            st.markdown("---")
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                # Exportar metadatos
                export_data = {
                    'timestamp': results['timestamp'],
                    'source_url': results['url'],
                    'images': downloaded
                }
                st.download_button(
                    label="📥 Exportar metadatos (JSON)",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"scraping_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            with col_btn2:
                # Limpiar resultados
                if st.button("🗑️ Limpiar resultados", width='stretch'):
                    st.session_state.scraping_results = None
                    st.rerun()
        else:
            st.info("No se descargaron imágenes en esta sesión")
    
    def _display_history(self):
        """Muestra el historial de scraping"""
        
        with st.expander("📜 Historial de Scraping"):
            for entry in st.session_state.scraping_history[:5]:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.markdown(f"**{entry['url']}**")
                with col2:
                    st.markdown(f"{entry['total_images']} imágenes")
                with col3:
                    st.markdown(f"{entry['timestamp'].strftime('%H:%M')}")
                with col4:
                    if st.button("🔄 Recargar", key=f"reload_{entry['timestamp']}"):
                        st.session_state.scraping_results = entry['results']
                        st.rerun()
                
                st.markdown("---")
    
    def _avg_quality(self, downloaded_images: list) -> float:
        """Calcula la calidad media de las imágenes descargadas"""
        if not downloaded_images:
            return 0
        total = sum(img.get('quality_score', 0) for img in downloaded_images)
        return total / len(downloaded_images)

# Función para integrar en la app principal
def render_scraping_panel():
    panel = ScrapingPanel()
    panel.render()
