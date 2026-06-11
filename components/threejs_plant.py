"""
Three.js 3D Plant component for Streamlit

Provide `render_3d_plant(hotspots, highlight_ids=None, height=600)` to
embed a lightweight Three.js scene inside Streamlit using
`st.components.v1.html()`.

Hotspot format: list of dicts with keys `id`, `name`, `x`, `y` (percent 0-100).
"""

import json
from pathlib import Path
import streamlit as st


def render_3d_plant(hotspots, highlight_ids=None, height: int = 600, auto_rotate: bool = True) -> None:
    """Renderiza una planta 3D básica con hotspots.

    Args:
        hotspots: list[dict] (id, name, x, y)
        highlight_ids: optional list of hotspot ids to highlight
        height: altura del iframe en píxeles
        auto_rotate: activar rotación automática de la cámara
    """

    hotspots_json = json.dumps(hotspots or [])
    highlight_json = json.dumps(highlight_ids or [])

    # Build HTML + JS. Use string concatenation so we don't need to escape braces.
    html = (
        "<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'/>"
        "<style>body{margin:0;overflow:hidden;background:#0a0e1a;color:#fff} .hotlabel{background:#E84C22;color:#fff;padding:4px 10px;border-radius:16px;font-family:Arial,Helvetica,sans-serif;font-size:12px}</style>"
        "</head><body>"
        "<div id='container'></div>"
        "<script type='module'>"
        "import * as THREE from 'https://unpkg.com/three@0.152.2/build/three.module.js';"
        "import { OrbitControls } from 'https://unpkg.com/three@0.152.2/examples/jsm/controls/OrbitControls.js';"
        "import { CSS2DRenderer, CSS2DObject } from 'https://unpkg.com/three@0.152.2/examples/jsm/renderers/CSS2DRenderer.js';"
        "const hotspots = "
        + hotspots_json
        + ";"
        + "const highlightIds = "
        + highlight_json
        + ";"
        + "const container = document.getElementById('container');"
        + "const scene = new THREE.Scene(); scene.background = new THREE.Color(0x0a0e1a);"
        + "const camera = new THREE.PerspectiveCamera(45, window.innerWidth/window.innerHeight, 0.1, 1000); camera.position.set(15,12,18);"
        + "const renderer = new THREE.WebGLRenderer({antialias:true, alpha:true}); renderer.setSize(window.innerWidth, window.innerHeight); renderer.setPixelRatio(window.devicePixelRatio); container.appendChild(renderer.domElement);"
        + "const labelRenderer = new CSS2DRenderer(); labelRenderer.setSize(window.innerWidth, window.innerHeight); labelRenderer.domElement.style.position='absolute'; labelRenderer.domElement.style.top='0px'; labelRenderer.domElement.style.left='0px'; labelRenderer.domElement.style.pointerEvents='none'; container.appendChild(labelRenderer.domElement);"
        + "const controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping=true; controls.dampingFactor=0.05; controls.autoRotate="
        + ("true" if auto_rotate else "false")
        + ";"
        + "const ambient = new THREE.AmbientLight(0x404060); scene.add(ambient);"
        + "const dir = new THREE.DirectionalLight(0xffffff,1); dir.position.set(5,10,7); scene.add(dir);"
        + "const planeGeo = new THREE.PlaneGeometry(25,20); const planeMat = new THREE.MeshStandardMaterial({color:0x1a1f2e,side:THREE.DoubleSide,transparent:true,opacity:0.3}); const base = new THREE.Mesh(planeGeo, planeMat); base.rotation.x = -Math.PI/2; base.position.y = -1.9; scene.add(base);"
        + "const grid = new THREE.GridHelper(30,20,0xE84C22,0x334455); grid.position.y = -2; scene.add(grid);"
        + "function createBuilding(x,z,w,h,d,color,name){const g=new THREE.BoxGeometry(w,h,d);const m=new THREE.MeshStandardMaterial({color:color,metalness:0.7,roughness:0.3});const b=new THREE.Mesh(g,m);b.position.set(x,h/2-1.5,z);b.userData={name:name};scene.add(b);const eg=new THREE.EdgesGeometry(g);const ln=new THREE.LineSegments(eg,new THREE.LineBasicMaterial({color:0xE84C22}));ln.position.copy(b.position);scene.add(ln);}"
        + "createBuilding(-8,-3,4,3,4,0x4a6a8a,'Roll Storage'); createBuilding(-3,-2,5,4,5,0xE84C22,'Corrugator'); createBuilding(2,-1,6,3,6,0x3a6a5a,'Converting'); createBuilding(7,0,5,3,5,0x4a6a8a,'Logistics');"
        + "const objects = [];"
        + "hotspots.forEach(h=>{const x=(h.x-50)/3; const z=(h.y-50)/3; const sphereGeo=new THREE.SphereGeometry(0.4,16,16); const mat=new THREE.MeshStandardMaterial({color:0xE84C22,emissive:0xE84C22,emissiveIntensity:0.6,transparent:true,opacity: highlightIds.length===0 || highlightIds.includes(h.id) ? 0.95 : 0.25}); const sph=new THREE.Mesh(sphereGeo,mat); sph.position.set(x,0.5,z); sph.userData={id:h.id,name:h.name,type:'hotspot'}; scene.add(sph); objects.push(sph); const div=document.createElement('div'); div.className='hotlabel'; div.textContent=h.name; const label=new CSS2DObject(div); label.position.set(x,1.2,z); scene.add(label);});"
        + "const raycaster = new THREE.Raycaster(); const mouse = new THREE.Vector2(); window.addEventListener('click', (evt)=>{ mouse.x = (evt.clientX / renderer.domElement.clientWidth) * 2 - 1; mouse.y = -(evt.clientY / renderer.domElement.clientHeight) * 2 + 1; raycaster.setFromCamera(mouse, camera); const inter = raycaster.intersectObjects(objects, true); if(inter.length>0){ const obj = inter[0].object; const id = obj.userData && obj.userData.id; if(id){ window.parent.postMessage({type:'hotspotClick', id:id}, '*'); window.parent.location.href = window.parent.location.pathname + '?hotspot=' + id; } } }, false);"
        + "let t=0; function animate(){ requestAnimationFrame(animate); t += 0.005; objects.forEach((o,i)=>{ o.rotation.y = Math.sin(t*2+(i*0.5))*0.1; }); controls.update(); renderer.render(scene,camera); labelRenderer.render(scene,camera);} animate();"
        + "function onResize(){ camera.aspect = window.innerWidth/window.innerHeight; camera.updateProjectionMatrix(); renderer.setSize(window.innerWidth, window.innerHeight); labelRenderer.setSize(window.innerWidth, window.innerHeight);} window.addEventListener('resize', onResize, false);"
        + "</script></body></html>"
    )

    st.components.v1.html(html, height=height, scrolling=False)


if __name__ == '__main__':
    # Quick local demo when run as script (not required)
    demo_hotspots = [
        {"id": "sr1400", "name": "SR-1400", "x": 15, "y": 30},
        {"id": "amr", "name": "AMR", "x": 55, "y": 35},
    ]
    try:
        render_3d_plant(demo_hotspots)
    except Exception:
        print('Run this inside Streamlit to view the 3D component')
