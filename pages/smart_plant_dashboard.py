"""
INGECART Smart Corrugated Plant Dashboard
Interactive Digital Factory Platform

Minimal, self-contained Streamlit page that reads configuration from
`data/smart_plant_config.json` and renders a plant overview with
hotspots and a right-hand panel with KPIs, overview text and video.
"""

import streamlit as st
import json
import base64
from pathlib import Path


st.set_page_config(page_title="INGECART Smart Plant Dashboard", page_icon="🏭", layout="wide")

CONFIG_PATH = Path("data/smart_plant_config.json")


def load_config():
    default = {
        "overview_text": "INGECART Smart Corrugated Plant — configure aquí el texto overview.",
        "general_video_path": "assets/videos/general/overview.mp4",
        "plant_image_path": "assets/images/smart_plant_overview.png",
        "hotspots": [],
        "kpis": {"productivity": 67, "automation": 82, "labor": 34, "waste": 12},
        "subpages": [],
        "solutions_mapping": {},
    }
    if CONFIG_PATH.exists():
        try:
            c = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            c = default
        for k, v in default.items():
            if k not in c:
                c[k] = v
        return c
    else:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
        return default


def image_to_base64(path: str) -> str | None:
    p = Path(path)
    if p.exists():
        return base64.b64encode(p.read_bytes()).decode()
    return None


def render_header(config: dict) -> None:
    cols = st.columns([1, 6, 1])
    with cols[1]:
        st.markdown(
            "<div style='text-align:center'>"
            "<h1 style='color:#E84C22;margin:0'>INGECART</h1>"
            "<h3 style='color:#8892b0;margin:0'>Smart Corrugated Plant</h3>"
            "<p style='color:#5a6a8a;margin:0'>Interactive path to the efficiency</p>"
            "</div>",
            unsafe_allow_html=True,
        )


def render_filters(config: dict) -> None:
    filters = [
        "All",
        "Labor shortage",
        "Productivity",
        "Waste",
        "Logistics",
        "Sustainability",
        "Energy",
    ]
    cols = st.columns(len(filters))
    for i, f in enumerate(filters):
        with cols[i]:
            if st.button(f, key=f"filter_{f}", use_container_width=True):
                st.session_state.active_filter = f
                st.experimental_rerun()


def render_plant(config: dict, highlight_ids=None) -> None:
    plant_img_b64 = image_to_base64(config.get("plant_image_path", ""))
    img_src = f"data:image/png;base64,{plant_img_b64}" if plant_img_b64 else ""

    html = f"""
    <div style="position:relative;width:100%;border-radius:8px;overflow:hidden;background:#0a0e1a;padding:6px;">
      <img src="{img_src}" style="width:100%; display:block; border-radius:6px;" />
      <div id="hotspots" style="position:absolute;left:0;top:0;width:100%;height:100%;">
    """

    for h in config.get("hotspots", []):
        is_high = (highlight_ids is None) or (h.get("id") in highlight_ids)
        opacity = "1" if is_high else "0.25"
        left = f"{h.get('x', 50)}%"
        top = f"{h.get('y', 50)}%"
        html += (
            """
        <div title="{name}" onclick="window.parent.location.href=window.parent.location.pathname + '?hotspot={id}'"
             style="position:absolute;left:{left};top:{top};transform:translate(-50%,-50%);width:36px;height:36px;
                    background:rgba(232,76,34,{opacity});border-radius:50%;cursor:pointer;box-shadow:0 6px 18px rgba(0,0,0,0.4);
                    display:flex;align-items:center;justify-content:center;color:white;font-weight:bold;">
          <span style="font-size:12px;">●</span>
        </div>
        """.format(name=h.get("name", ""), id=h.get("id", ""), left=left, top=top, opacity=opacity)
        )

    html += "</div></div>"
    st.components.v1.html(html, height=560, scrolling=False)


def render_right_panel(config: dict, selected_hotspot_id: str | None = None) -> None:
    st.markdown("### 📊 PLANT STATUS")
    kpis = config.get("kpis", {})
    for key, val in kpis.items():
        st.markdown(f"**{key.capitalize()}**: {val}%")
        try:
            st.progress(int(val))
        except Exception:
            pass

    st.markdown("---")
    st.markdown("### 🎥 OVERVIEW VIDEO")
    vpath = config.get("general_video_path", "")
    if Path(vpath).exists():
        st.video(str(vpath))
    else:
        st.info("Sube el video general en el configurador (assets/videos/general/overview.mp4)")

    st.markdown("---")
    st.markdown("### 📋 OVERVIEW")
    st.write(config.get("overview_text", ""))

    if selected_hotspot_id:
        st.markdown("---")
        hotspot = next((h for h in config.get("hotspots", []) if h.get("id") == selected_hotspot_id), None)
        if hotspot:
            st.markdown(f"### 🔧 {hotspot.get('name')}")
            st.write(hotspot.get("description", ""))
            st.write("**ROI:**", hotspot.get("roi", ""))
            st.write("**Ahorro anual:**", hotspot.get("savings", ""))
            if hotspot.get("video") and Path(hotspot["video"]).exists():
                st.video(str(hotspot["video"]))
            st.download_button("📥 Brochure (placeholder)", data="PDF", file_name=f"{hotspot.get('id')}_brochure.pdf")
            if st.button("Enviar detalle al chat"):
                st.session_state.chat = st.session_state.get("chat", [])
                st.session_state.chat.append(f"{hotspot.get('name')}: {hotspot.get('description')}")
                st.experimental_rerun()


def render_chat_area() -> None:
    st.markdown("### 💬 Chat demo")
    chat = st.session_state.get("chat", [])
    for msg in chat:
        st.write(msg)


def main():
    if "active_filter" not in st.session_state:
        st.session_state.active_filter = "All"
    if "chat" not in st.session_state:
        st.session_state.chat = []
    config = load_config()
    render_header(config)
    render_filters(config)
    active_filter = st.session_state.get("active_filter", "All")
    mapping = config.get("solutions_mapping", {})
    highlight_ids = None if active_filter == "All" else mapping.get(active_filter, [])
    # Toggle 3D view (uses components/threejs_plant.py if available)
    use_3d = st.checkbox("Activar vista 3D (Three.js)", value=False, key="use_3d_toggle")

    # Precompute highlight ids for filters so both renderers can use them
    active_filter = st.session_state.get("active_filter", "All")
    mapping = config.get("solutions_mapping", {})
    highlight_ids = None if active_filter == "All" else mapping.get(active_filter, [])

    c1, c2 = st.columns([2, 1])
    with c1:
        if use_3d:
            try:
                from components.threejs_plant import render_3d_plant

                render_3d_plant(config.get("hotspots", []), highlight_ids=highlight_ids, height=600)
            except Exception:
                st.error("No se pudo cargar el componente 3D. Se mostrará la vista 2D.")
                render_plant(config)
        else:
            render_plant(config)
    with c2:
        params = st.experimental_get_query_params()
        hotspot_id = params.get("hotspot", [None])[0]
        render_right_panel(config, selected_hotspot_id=hotspot_id)
        render_chat_area()


if __name__ == "__main__":
    main()
