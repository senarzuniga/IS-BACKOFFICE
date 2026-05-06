# ============================================
# COMANDO MAESTRO - PRESENTACION PSC VISALIA v2.0
# ============================================

$ErrorActionPreference = "Stop"

Write-Host "INICIANDO AGENTES DE IA - INGECART PSC VISALIA v2.0" -ForegroundColor Cyan
Write-Host ""

$PROJECT_DIR = "C:\Users\Inaki Senar\Documents\GitHub\IS-BACKOFFICE"
$ASSETS_DIR = "$PROJECT_DIR\ingecart_assets_v2"
$PYTHON_EXE = "c:/Users/Inaki Senar/Documents/GitHub/IS-BACKOFFICE/.venv/Scripts/python.exe"

New-Item -ItemType Directory -Force -Path $ASSETS_DIR | Out-Null

Write-Host "[AGENTE: WEB_SCRAPER] Extrayendo contenido completo de ingecart.eu..." -ForegroundColor Yellow

& "$PYTHON_EXE" -c @"
import requests, json, re, os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import Counter

output_dir = r'$ASSETS_DIR'
os.makedirs(output_dir, exist_ok=True)

print('Descargando https://www.ingecart.eu ...')
response = requests.get('https://www.ingecart.eu', headers={'User-Agent': 'Mozilla/5.0'}, timeout=25)
response.raise_for_status()
soup = BeautifulSoup(response.text, 'html.parser')

print('Extrayendo textos...')
vision_complete = ''
services_complete = ''
why_complete = ''

for h in soup.find_all(['h1', 'h2', 'h3', 'h4']):
    txt = h.get_text(' ', strip=True).upper()
    parent = h.find_parent() or h
    block_text = []
    for elem in parent.find_all(['p', 'div', 'span']):
        t = elem.get_text(' ', strip=True)
        if t:
            block_text.append(t)
    merged = '\n'.join(block_text)

    if 'VISION' in txt and not vision_complete:
        vision_complete = merged
    if 'SERVICIOS' in txt and not services_complete:
        services_complete = merged
    if ('POR QUE' in txt or 'INGECART' in txt) and not why_complete:
        why_complete = merged

partners = []
partner_candidates = soup.find_all(['section', 'div'], class_=re.compile(r'partner|cliente|client', re.I))
for sec in partner_candidates:
    for img in sec.find_all('img'):
        alt = (img.get('alt') or '').strip()
        src = (img.get('src') or '').strip()
        if alt or src:
            name = alt if alt else os.path.basename(src).split('.')[0]
            partners.append({'name': name, 'logo': src})

if not partners:
    for img in soup.find_all('img'):
        alt = (img.get('alt') or '').strip()
        src = (img.get('src') or '').strip()
        if alt and any(k in alt.lower() for k in ['partner', 'cliente', 'client', 'logo']):
            partners.append({'name': alt, 'logo': src})

numbers_text = soup.get_text(' ', strip=True)
proyectos = re.search(r'(\d[\d,.]+)\s*proyectos?', numbers_text, re.I)
experiencia = re.search(r'(\d+)\s*a(?:n|ñ)os?\s+de\s+experiencia', numbers_text, re.I)
acuerdos = re.search(r'(\d+)\s*acuerdos?\s+internacionales', numbers_text, re.I)
instalaciones = re.search(r'(\d+)\s*instalaciones?', numbers_text, re.I)

print('Extrayendo colores...')
colors = []
for tag in soup.find_all(style=True):
    for color in re.findall(r'#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}|rgb\([^)]+\)', tag['style']):
        colors.append(color)
for tag in soup.find_all(['div', 'section', 'header', 'footer', 'nav']):
    bg = tag.get('bgcolor')
    if bg:
        colors.append(bg)

color_counts = Counter(colors)
top_colors = [c for c, _ in color_counts.most_common(6) if c and len(c) > 3]

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        return tuple(int(hex_color[i:i+2], 16) for i in (0,2,4))
    if len(hex_color) == 3:
        return tuple(int(h*2, 16) for h in hex_color)
    return None

color_palette = {}
for c in top_colors:
    if c.startswith('#'):
        rgb = hex_to_rgb(c)
        if rgb:
            color_palette[c] = rgb
    elif c.startswith('rgb'):
        rgb_vals = re.findall(r'\d+', c)
        if len(rgb_vals) >= 3:
            color_palette[c] = tuple(map(int, rgb_vals[:3]))

print('Descargando imagenes...')
logos = []
images = []
for img in soup.find_all('img'):
    src = img.get('src')
    if not src:
        continue
    img_url = urljoin('https://www.ingecart.eu', src)
    try:
        resp = requests.get(img_url, timeout=15)
        resp.raise_for_status()
        img_data = resp.content
        img_name = os.path.basename(src.split('?')[0]) or f'image_{len(images)}.png'
        if not img_name.endswith(('.png','.jpg','.jpeg','.svg','.webp','.gif')):
            img_name += '.png'
        img_path = os.path.join(output_dir, img_name)
        with open(img_path, 'wb') as f:
            f.write(img_data)
        info = {'name': img_name, 'path': img_path, 'alt': img.get('alt', '')}
        images.append(info)
        if 'logo' in img_name.lower() or 'brand' in img_name.lower() or 'icon' in img_name.lower():
            logos.append(info)
    except Exception:
        pass

brand_data = {
    'company_name': 'Ingecart',
    'tagline': 'Engineering & Auditing | Tailored Automation & Intralogistics',
    'colors': {k:list(v) for k,v in color_palette.items()},
    'primary_color': list(next(iter(color_palette.values())) if color_palette else (0,51,102)),
    'secondary_color': list(list(color_palette.values())[1] if len(color_palette) > 1 else (0,119,190)),
    'texts': {
        'vision': vision_complete[:1000],
        'services': services_complete[:1000],
        'why': why_complete[:800],
        'stats': {
            'proyectos': proyectos.group(1) if proyectos else '1.268',
            'experiencia': experiencia.group(1) if experiencia else '28',
            'acuerdos': acuerdos.group(1) if acuerdos else '26',
            'instalaciones': instalaciones.group(1) if instalaciones else '194'
        }
    },
    'partners': partners,
    'logos': [l['path'] for l in logos],
    'all_images': images,
    'source_url': 'https://www.ingecart.eu'
}

out_json = os.path.join(output_dir, 'ingecart_brand_complete.json')
with open(out_json, 'w', encoding='utf-8') as f:
    json.dump(brand_data, f, indent=2, ensure_ascii=False)

print(f'COMPLETO: {len(images)} imagenes, {len(partners)} partners, {len(color_palette)} colores')
print(f'JSON: {out_json}')
"@

Write-Host "[WEB_SCRAPER] Extraccion completa" -ForegroundColor Green
Write-Host ""

Write-Host "[AGENTE: PRESENTATION_MASTER] Generando presentacion profesional v2.0..." -ForegroundColor Yellow

& "$PYTHON_EXE" -c @"
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import json, os

assets_dir = r'$ASSETS_DIR'
brand_file = os.path.join(assets_dir, 'ingecart_brand_complete.json')

with open(brand_file, 'r', encoding='utf-8') as f:
    brand = json.load(f)

def rgb_to_pptx(rgb):
    if not rgb or len(rgb) < 3:
        return RGBColor(0, 51, 102)
    return RGBColor(int(rgb[0]), int(rgb[1]), int(rgb[2]))

PRIMARY = rgb_to_pptx(brand.get('primary_color', [0,51,102]))
SECONDARY = rgb_to_pptx(brand.get('secondary_color', [0,119,190]))
ACCENT = RGBColor(255, 140, 0)
WHITE = RGBColor(255,255,255)
GRAY = RGBColor(80,80,80)
LIGHT_GRAY = RGBColor(245,245,245)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

stats = brand.get('texts', {}).get('stats', {})
partners = brand.get('partners', [])
logos = brand.get('logos', [])

def add_cover(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid(); bg.fill.fore_color.rgb = PRIMARY; bg.line.fill.background()
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(5.5), prs.slide_width, Inches(0.1))
    line.fill.solid(); line.fill.fore_color.rgb = ACCENT; line.line.fill.background()
    title = slide.shapes.add_textbox(Inches(0.5), Inches(2.2), Inches(12.333), Inches(1.5))
    tf = title.text_frame
    tf.text = 'PSC VISALIA PROJECT\nComplete Relocation + Modernization + Automation'
    tf.paragraphs[0].font.size = Pt(44)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = WHITE
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    if logos:
        try:
            slide.shapes.add_picture(logos[0], Inches(5), Inches(0.3), height=Inches(0.8))
        except Exception:
            pass
    subtitle = slide.shapes.add_textbox(Inches(0.5), Inches(6.2), Inches(12.333), Inches(0.8))
    sf = subtitle.text_frame
    sf.text = 'Solving Real Bottlenecks in Corrugated Plants'
    sf.paragraphs[0].font.size = Pt(20)
    sf.paragraphs[0].font.color.rgb = RGBColor(200,200,200)
    sf.paragraphs[0].alignment = PP_ALIGN.CENTER

def add_stats_slide(prs, stats):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    title = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.333), Inches(0.8))
    tf = title.text_frame
    tf.text = 'Ingecart en numeros - La fuerza de nuestra experiencia'
    tf.paragraphs[0].font.size = Pt(32)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = PRIMARY
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(1.1), Inches(4), Inches(0.05))
    line.fill.solid(); line.fill.fore_color.rgb = SECONDARY
    stat_items = [
        (stats.get('proyectos', '1.268'), 'Proyectos', 1.5),
        (stats.get('experiencia', '28'), 'Anos experiencia', 4.5),
        (stats.get('acuerdos', '26'), 'Acuerdos internacionales', 7.5),
        (stats.get('instalaciones', '194'), 'Instalaciones', 10.5)
    ]
    for value, label, x in stat_items:
        num = slide.shapes.add_textbox(Inches(x), Inches(2.5), Inches(2), Inches(1))
        nf = num.text_frame
        nf.text = str(value)
        nf.paragraphs[0].font.size = Pt(48)
        nf.paragraphs[0].font.bold = True
        nf.paragraphs[0].font.color.rgb = ACCENT
        nf.paragraphs[0].alignment = PP_ALIGN.CENTER
        lbl = slide.shapes.add_textbox(Inches(x), Inches(3.6), Inches(2), Inches(0.6))
        lf = lbl.text_frame
        lf.text = label
        lf.paragraphs[0].font.size = Pt(14)
        lf.paragraphs[0].font.color.rgb = GRAY
        lf.paragraphs[0].alignment = PP_ALIGN.CENTER

def add_partners_slide(prs, partners):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    title = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.333), Inches(0.8))
    tf = title.text_frame
    tf.text = 'Nuestros Partners - Confianza global'
    tf.paragraphs[0].font.size = Pt(32)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = PRIMARY
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(1.1), Inches(4), Inches(0.05))
    line.fill.solid(); line.fill.fore_color.rgb = SECONDARY
    if partners:
        cols = 3
        for idx, partner in enumerate(partners[:9]):
            col = idx % cols
            row = idx // cols
            x = 1.5 + col * 4
            y = 2 + row * 1.8
            box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(3), Inches(1.2))
            box.fill.solid(); box.fill.fore_color.rgb = LIGHT_GRAY
            box.line.color.rgb = SECONDARY; box.line.width = Pt(1)
            name_box = slide.shapes.add_textbox(Inches(x+0.2), Inches(y+0.4), Inches(2.6), Inches(0.6))
            nf = name_box.text_frame
            nf.text = str(partner.get('name', 'Partner'))[:30]
            nf.paragraphs[0].font.size = Pt(12)
            nf.paragraphs[0].font.bold = True
            nf.paragraphs[0].alignment = PP_ALIGN.CENTER
            nf.paragraphs[0].font.color.rgb = PRIMARY

def add_vision_slide(prs, vision_text):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    title = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.333), Inches(0.8))
    tf = title.text_frame
    tf.text = 'Nuestra Vision - Revolucionando el corrugado'
    tf.paragraphs[0].font.size = Pt(32)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = PRIMARY
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(1.1), Inches(4), Inches(0.05))
    line.fill.solid(); line.fill.fore_color.rgb = SECONDARY
    quote = slide.shapes.add_textbox(Inches(0.5), Inches(1.8), Inches(12.333), Inches(1))
    qf = quote.text_frame
    qf.text = '"Ninguno de nosotros es tan inteligente como todos nosotros juntos." - Ken Blanchard'
    qf.paragraphs[0].font.size = Pt(16)
    qf.paragraphs[0].font.italic = True
    qf.paragraphs[0].font.color.rgb = ACCENT
    vision_box = slide.shapes.add_textbox(Inches(0.5), Inches(3.2), Inches(12.333), Inches(3.5))
    vf = vision_box.text_frame
    vf.word_wrap = True
    vf.text = (vision_text or 'Revolucionando el mundo del papel y el carton corrugado...')[:800]
    vf.paragraphs[0].font.size = Pt(14)
    vf.paragraphs[0].font.color.rgb = GRAY

def add_project_summary(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    title = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.333), Inches(0.8))
    tf = title.text_frame
    tf.text = 'Proyecto PSC Visalia - Resumen'
    tf.paragraphs[0].font.size = Pt(32)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = PRIMARY
    content = [
        '',
        '• Corrugadora BHS 2500mm (1997) - Reubicacion Turquia -> USA',
        '• Modernizacion completa: Siemens S7 + nuevos drives + HMI tactil',
        '• Ingetrans - Carga automatica de bobinas: $1.14M',
        '• Conveyors + AMR - Flujo continuo: $1.45M',
        '• Eliminacion de obsolescencia critica',
        '• Plataforma MES/ERP ready',
        '',
        'INVERSION TOTAL: ~$7M USD',
        'RETORNO ESTIMADO: <18 meses'
    ]
    content_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(12.333), Inches(5))
    cf = content_box.text_frame
    cf.word_wrap = True
    for i, line in enumerate(content):
        p = cf.paragraphs[0] if i == 0 else cf.add_paragraph()
        p.text = line
        p.font.size = Pt(16)
        p.font.color.rgb = GRAY
        p.space_after = Pt(8)

def add_closing_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid(); bg.fill.fore_color.rgb = PRIMARY; bg.line.fill.background()
    title = slide.shapes.add_textbox(Inches(0.5), Inches(2), Inches(12.333), Inches(1.5))
    tf = title.text_frame
    tf.text = 'Solving Real Bottlenecks\nin Corrugated Plants'
    tf.paragraphs[0].font.size = Pt(44)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = WHITE
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    subtitle = slide.shapes.add_textbox(Inches(0.5), Inches(4), Inches(12.333), Inches(1))
    sf = subtitle.text_frame
    sf.text = 'Industrial Intelligence Applied to Performance'
    sf.paragraphs[0].font.size = Pt(28)
    sf.paragraphs[0].font.color.rgb = RGBColor(200,200,200)
    sf.paragraphs[0].alignment = PP_ALIGN.CENTER

print('Generando presentacion v2.0...')
add_cover(prs)
add_stats_slide(prs, stats)
add_partners_slide(prs, partners)
add_vision_slide(prs, brand.get('texts', {}).get('vision', ''))
add_project_summary(prs)
add_closing_slide(prs)

output_path = r'$PROJECT_DIR\PSC_VISALIA_v2_FINAL.pptx'
prs.save(output_path)
print('Presentacion v2.0 guardada en: ' + output_path)
print('Diapositivas: ' + str(len(prs.slides)))
print('Partners incluidos: ' + str(len(partners)))
"@

Write-Host "[PRESENTATION_MASTER] Presentacion v2.0 generada" -ForegroundColor Green
Write-Host ""

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "PRESENTACION PSC VISALIA v2.0 COMPLETADA" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "ARCHIVOS GENERADOS:" -ForegroundColor Yellow
Write-Host " - Presentacion final: $PROJECT_DIR\PSC_VISALIA_v2_FINAL.pptx"
Write-Host " - Assets web: $ASSETS_DIR"
Write-Host " - Datos extraidos: $ASSETS_DIR\ingecart_brand_complete.json"
