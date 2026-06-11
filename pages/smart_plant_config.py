"""
Panel de Configuración - Smart Plant Dashboard
Permite administrar todo el contenido dinámico

Este módulo implementa una interfaz Streamlit que edita
`data/smart_plant_config.json` y guarda imágenes/videos en `assets/`.
"""

import streamlit as st
import json
from pathlib import Path


st.set_page_config(page_title="Configurar Smart Plant", page_icon="⚙️", layout="wide")
CONFIG_PATH = Path("data/smart_plant_config.json")


def load_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_config(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    st.title("⚙️ Configuración Smart Plant Dashboard")
    config = load_config()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Información General",
        "Hotspots",
        "KPIs",
        "Subpáginas",
        "Filtros",
    ])

    with tab1:
        st.subheader("Información General del Dashboard")
        col1, col2 = st.columns(2)
        with col1:
            overview_text = st.text_area(
                "Texto Overview",
                value=config.get("overview_text", ""),
                height=200,
            )
            config["overview_text"] = overview_text
        with col2:
            st.markdown("### Imagen de la Planta")
            uploaded_image = st.file_uploader("Subir imagen de la planta", type=["png", "jpg", "jpeg", "svg"])
            if uploaded_image:
                image_path = Path("assets/images/smart_plant_overview.png")
                image_path.parent.mkdir(parents=True, exist_ok=True)
                with open(image_path, "wb") as f:
                    f.write(uploaded_image.getbuffer())
                config["plant_image_path"] = str(image_path)
                st.success("✅ Imagen actualizada")

            st.markdown("### Video General")
            uploaded_video = st.file_uploader("Subir video general", type=["mp4", "mov", "avi"])
            if uploaded_video:
                video_path = Path("assets/videos/general/overview.mp4")
                video_path.parent.mkdir(parents=True, exist_ok=True)
                with open(video_path, "wb") as f:
                    f.write(uploaded_video.getbuffer())
                config["general_video_path"] = str(video_path)
                st.success("✅ Video actualizado")

    with tab2:
        st.subheader("Configuración de Hotspots")
        hotspots = config.get("hotspots", [])

        for idx, hotspot in enumerate(list(hotspots)):
            with st.expander(f"📍 {hotspot.get('name', f'Hotspot {idx+1}')}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    hotspot['id'] = st.text_input(f"ID", hotspot.get('id', ''), key=f"id_{idx}")
                    hotspot['name'] = st.text_input(f"Nombre", hotspot.get('name', ''), key=f"name_{idx}")
                    hotspot['description'] = st.text_area(f"Descripción", hotspot.get('description', ''), key=f"desc_{idx}")
                with col2:
                    hotspot['x'] = st.slider(f"Posición X %", 0, 100, hotspot.get('x', 50), key=f"x_{idx}")
                    hotspot['y'] = st.slider(f"Posición Y %", 0, 100, hotspot.get('y', 50), key=f"y_{idx}")
                    hotspot['roi'] = st.text_input(f"ROI", hotspot.get('roi', ''), key=f"roi_{idx}")
                    hotspot['savings'] = st.text_input(f"Ahorro anual", hotspot.get('savings', ''), key=f"savings_{idx}")

                video_file = st.file_uploader(f"Video para {hotspot.get('name')}", type=["mp4"], key=f"video_{idx}")
                if video_file:
                    video_dir = Path(f"assets/videos/hotspots/{hotspot.get('id','hotspot')}")
                    video_dir.mkdir(parents=True, exist_ok=True)
                    video_path = video_dir / "demo.mp4"
                    with open(video_path, 'wb') as f:
                        f.write(video_file.getbuffer())
                    hotspot['video'] = str(video_path)
                    st.success(f"✅ Video guardado para {hotspot.get('name')}")

                if st.button(f"🗑️ Eliminar {hotspot.get('name')}", key=f"del_{idx}"):
                    hotspots.pop(idx)
                    st.experimental_rerun()

        if st.button("➕ Añadir nuevo hotspot"):
            hotspots.append({
                "id": f"new_{len(hotspots)+1}",
                "name": "Nuevo Equipo",
                "x": 50,
                "y": 50,
                "description": "Descripción del equipo",
                "video": "",
                "roi": "Por definir",
                "savings": "Por definir",
            })
            st.experimental_rerun()

        config['hotspots'] = hotspots

    with tab3:
        st.subheader("Indicadores de Planta (KPIs)")
        kpis = config.get('kpis', {"productivity": 92, "automation": 87, "labor": 42, "waste": 6})
        col1, col2 = st.columns(2)
        with col1:
            kpis['productivity'] = st.slider("Productivity (%)", 0, 100, kpis.get('productivity', 92))
            kpis['automation'] = st.slider("Automation (%)", 0, 100, kpis.get('automation', 87))
        with col2:
            kpis['labor'] = st.slider("Labor Efficiency (%)", 0, 100, kpis.get('labor', 42))
            kpis['waste'] = st.slider("Waste Reduction (%)", 0, 100, kpis.get('waste', 6))
        config['kpis'] = kpis

    with tab4:
        st.subheader("Navegación a Subpáginas")
        subpages = config.get('subpages', [{"name": "Industry 4.0", "icon": "🤖", "url": "/industry40"}])
        for idx, page in enumerate(subpages):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                page['name'] = st.text_input(f"Nombre", page.get('name', ''), key=f"page_name_{idx}")
            with col2:
                page['icon'] = st.text_input(f"Icono", page.get('icon', '📄'), key=f"page_icon_{idx}")
            with col3:
                page['url'] = st.text_input(f"URL", page.get('url', '#'), key=f"page_url_{idx}")
        config['subpages'] = subpages

    with tab5:
        st.subheader("Filtros por Problema del Cliente")
        solutions_mapping = config.get('solutions_mapping', {})
        all_solution_ids = [h['id'] for h in config.get('hotspots', [])]
        for filter_name in ["Labor shortage", "Productivity", "Waste", "Logistics", "Sustainability", "Energy"]:
            with st.expander(f"🎯 {filter_name}"):
                current = solutions_mapping.get(filter_name, [])
                selected = st.multiselect(
                    f"Equipos para {filter_name}", options=all_solution_ids, default=current, key=f"filter_{filter_name}"
                )
                solutions_mapping[filter_name] = selected
        config['solutions_mapping'] = solutions_mapping

    st.markdown("---")
    col_save1, col_save2, col_save3 = st.columns(3)
    with col_save2:
        if st.button("💾 GUARDAR CONFIGURACIÓN", type="primary", use_container_width=True):
            save_config(config)
            st.success("✅ Configuración guardada correctamente")
            st.balloons()

    with st.expander("📋 Ver configuración actual (JSON)"):
        st.json(config)


if __name__ == "__main__":
    main()
