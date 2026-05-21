from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


DEST_DIR = Path(r"C:\Users\Inaki Senar\Documents\INGECART\MARKETING\CONTENT\CONTENIDOS INGECART FESPA 2026")
LOGO_PATH = DEST_DIR / "ingeeniering.png"
HERO_PATH = DEST_DIR / "imagen_slogan_principal_ingecart.png"


def draw_crop_marks(c: canvas.Canvas, x: float, y: float, w: float, h: float, mark=4 * mm, gap=2 * mm):
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.3)

    # top-left
    c.line(x - gap - mark, y + h, x - gap, y + h)
    c.line(x, y + h + gap, x, y + h + gap + mark)

    # top-right
    c.line(x + w + gap, y + h, x + w + gap + mark, y + h)
    c.line(x + w, y + h + gap, x + w, y + h + gap + mark)

    # bottom-left
    c.line(x - gap - mark, y, x - gap, y)
    c.line(x, y - gap - mark, x, y - gap)

    # bottom-right
    c.line(x + w + gap, y, x + w + gap + mark, y)
    c.line(x + w, y - gap - mark, x + w, y - gap)


def draw_header_band(c: canvas.Canvas, x: float, y: float, w: float, h: float, title: str, subtitle: str):
    c.setFillColor(colors.HexColor("#05070B"))
    c.rect(x, y + h - 35 * mm, w, 35 * mm, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#F4F5F7"))
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x + 8 * mm, y + h - 13 * mm, title)

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#D0D4DA"))
    c.drawString(x + 8 * mm, y + h - 20 * mm, subtitle)

    c.setFillColor(colors.HexColor("#FF6A00"))
    c.rect(x + 8 * mm, y + h - 24 * mm, 28 * mm, 1.4 * mm, fill=1, stroke=0)

    if LOGO_PATH.exists():
        c.drawImage(str(LOGO_PATH), x + w - 42 * mm, y + h - 27 * mm, width=32 * mm, preserveAspectRatio=True, mask="auto")


def draw_panel_guides(c: canvas.Canvas, x: float, y: float, panel_w: float, h: float):
    c.setStrokeColor(colors.HexColor("#B8B8B8"))
    c.setLineWidth(0.4)
    c.line(x + panel_w, y, x + panel_w, y + h)
    c.line(x + 2 * panel_w, y, x + 2 * panel_w, y + h)


def draw_safe_area(c: canvas.Canvas, x: float, y: float, w: float, h: float, margin: float):
    c.setStrokeColor(colors.HexColor("#CFCFCF"))
    c.setDash(2, 2)
    c.rect(x + margin, y + margin, w - 2 * margin, h - 2 * margin, fill=0, stroke=1)
    c.setDash()


def create_trifold_a4_print_pdf(path: Path):
    # A4 landscape with bleed 3mm around
    final_w = 297 * mm
    final_h = 210 * mm
    bleed = 3 * mm
    page_w = final_w + 2 * bleed
    page_h = final_h + 2 * bleed

    c = canvas.Canvas(str(path), pagesize=(page_w, page_h))

    x = bleed
    y = bleed
    panel_w = final_w / 3

    # PAGE 1: EXTERIOR
    c.setFillColor(colors.white)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    draw_header_band(c, x, y, final_w, final_h, "Ingecart | FESPA 2026", "Triptico A4 Premium - Cara Exterior")
    draw_panel_guides(c, x, y, panel_w, final_h)
    draw_safe_area(c, x, y, final_w, final_h, margin=5 * mm)

    # Right panel (front cover)
    rx = x + 2 * panel_w + 6 * mm
    c.setFillColor(colors.HexColor("#05070B"))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(rx, y + final_h - 55 * mm, "Menos friccion")
    c.drawString(rx, y + final_h - 63 * mm, "Mas produccion util")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#333333"))
    c.drawString(rx, y + final_h - 74 * mm, "Automatizacion e intralogistica")
    c.drawString(rx, y + final_h - 80 * mm, "con resultados medibles.")

    if HERO_PATH.exists():
        c.drawImage(str(HERO_PATH), x + 2 * panel_w + 4 * mm, y + 26 * mm, width=panel_w - 10 * mm, height=78 * mm, preserveAspectRatio=True, mask="auto")

    c.setFillColor(colors.HexColor("#FF6A00"))
    c.rect(x + 2 * panel_w + 4 * mm, y + 16 * mm, panel_w - 10 * mm, 7 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 2 * panel_w + 8 * mm, y + 18.2 * mm, "Reserve reunion tecnica en stand")

    # Center panel (back)
    cx = x + panel_w + 6 * mm
    c.setFillColor(colors.HexColor("#05070B"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(cx, y + final_h - 55 * mm, "Contacto")
    c.setFont("Helvetica", 9.5)
    c.setFillColor(colors.HexColor("#333333"))
    contact_lines = [
        "www.ingecart.eu",
        "www.ingecart.eu/book-online",
        "hablemos@ingecart.eu",
        "+34 938 183 316",
    ]
    yy = y + final_h - 62 * mm
    for line in contact_lines:
        c.drawString(cx, yy, line)
        yy -= 6 * mm

    c.setFillColor(colors.HexColor("#05070B"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(cx, y + final_h - 100 * mm, "Datos clave")
    c.setFont("Helvetica", 9.5)
    c.setFillColor(colors.HexColor("#333333"))
    facts = ["28 anos", "1.268 proyectos", "26 acuerdos", "194 instalaciones"]
    yy = y + final_h - 107 * mm
    for f in facts:
        c.drawString(cx, yy, f"- {f}")
        yy -= 6 * mm

    # Left panel (flap)
    lx = x + 6 * mm
    c.setFillColor(colors.HexColor("#05070B"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(lx, y + final_h - 55 * mm, "Por que Ingecart")
    c.setFont("Helvetica", 9.5)
    c.setFillColor(colors.HexColor("#333333"))
    vals = [
        "Ingenieria independiente",
        "Implantacion por fases",
        "KPI orientados a negocio",
        "Soporte integral en planta",
    ]
    yy = y + final_h - 62 * mm
    for v in vals:
        c.drawString(lx, yy, f"- {v}")
        yy -= 6 * mm

    draw_crop_marks(c, x, y, final_w, final_h)
    c.showPage()

    # PAGE 2: INTERIOR
    c.setFillColor(colors.white)
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    draw_header_band(c, x, y, final_w, final_h, "Soluciones Core", "Triptico A4 Premium - Cara Interior")
    draw_panel_guides(c, x, y, panel_w, final_h)
    draw_safe_area(c, x, y, final_w, final_h, margin=5 * mm)

    panels = [
        (
            x + 6 * mm,
            "Paletizer + Easy Pack",
            ["Apilado y embalado automatico", "Cadencia estable de fin de linea", "Menos retrabajo y dano logistico"],
        ),
        (
            x + panel_w + 6 * mm,
            "Retal + Ingetrans",
            ["Gestion eficiente de desperdicio", "Flujo de bobinas sincronizado", "Menos trafico de carretillas"],
        ),
        (
            x + 2 * panel_w + 6 * mm,
            "AMR + Ing_PRO",
            ["Movilidad flexible sin obra fija", "IA operacional accionable", "Mejora de OEE y MTTR"],
        ),
    ]

    for px, title, bullets in panels:
        c.setFillColor(colors.HexColor("#05070B"))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(px, y + final_h - 55 * mm, title)
        c.setFillColor(colors.HexColor("#333333"))
        c.setFont("Helvetica", 9.5)
        yy = y + final_h - 64 * mm
        for b in bullets:
            c.drawString(px, yy, f"- {b}")
            yy -= 6.5 * mm

        c.setFillColor(colors.HexColor("#FF6A00"))
        c.rect(px, y + 16 * mm, panel_w - 14 * mm, 7 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8.6)
        c.drawString(px + 2.4 * mm, y + 18.2 * mm, "Diagnostico express post-feria")

    draw_crop_marks(c, x, y, final_w, final_h)
    c.save()


def create_rollup_print_pdf(path: Path):
    # Rollup 85x200 cm with 3mm bleed and 150mm hidden bottom area
    final_w = 850 * mm
    final_h = 2000 * mm
    bleed = 3 * mm
    hidden_bottom = 150 * mm
    page_w = final_w + 2 * bleed
    page_h = final_h + 2 * bleed

    c = canvas.Canvas(str(path), pagesize=(page_w, page_h))

    x = bleed
    y = bleed

    # Background gradient-like bands
    c.setFillColor(colors.HexColor("#05070B"))
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#1A1D24"))
    c.rect(x, y + hidden_bottom, final_w, final_h - hidden_bottom, fill=1, stroke=0)

    # Header band
    c.setFillColor(colors.HexColor("#05070B"))
    c.rect(x, y + final_h - 260 * mm, final_w, 260 * mm, fill=1, stroke=0)

    if LOGO_PATH.exists():
        c.drawImage(str(LOGO_PATH), x + final_w - 220 * mm, y + final_h - 120 * mm, width=180 * mm, preserveAspectRatio=True, mask="auto")

    c.setFillColor(colors.HexColor("#F4F5F7"))
    c.setFont("Helvetica-Bold", 56)
    c.drawString(x + 50 * mm, y + final_h - 95 * mm, "INGECART")

    c.setFont("Helvetica-Bold", 36)
    c.drawString(x + 50 * mm, y + final_h - 145 * mm, "Menos friccion operativa")
    c.setFillColor(colors.HexColor("#FF6A00"))
    c.drawString(x + 50 * mm, y + final_h - 190 * mm, "Mas produccion util")

    # Hero visual
    if HERO_PATH.exists():
        c.drawImage(str(HERO_PATH), x + 60 * mm, y + final_h - 990 * mm, width=730 * mm, height=520 * mm, preserveAspectRatio=True, mask="auto")

    # Value blocks
    blocks = [
        ("Paletizer + Easy Pack", "Fin de linea estable y automatizado"),
        ("Retal + Ingetrans", "Flujo interno seguro y eficiente"),
        ("AMR + Ing_PRO", "Flexibilidad y decision operacional"),
    ]

    by = y + final_h - 1160 * mm
    for idx, (t, s) in enumerate(blocks):
        bx = x + 60 * mm + idx * 250 * mm
        c.setFillColor(colors.HexColor("#F4F5F7"))
        c.roundRect(bx, by, 230 * mm, 120 * mm, 8 * mm, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#05070B"))
        c.setFont("Helvetica-Bold", 16)
        c.drawString(bx + 12 * mm, by + 82 * mm, t)
        c.setFont("Helvetica", 12)
        c.drawString(bx + 12 * mm, by + 58 * mm, s)

    # CTA zone
    c.setFillColor(colors.HexColor("#FF6A00"))
    c.rect(x + 60 * mm, y + 290 * mm, 730 * mm, 90 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(x + 90 * mm, y + 338 * mm, "Agende su diagnostico express post-feria")

    c.setFillColor(colors.HexColor("#F4F5F7"))
    c.setFont("Helvetica", 14)
    c.drawString(x + 90 * mm, y + 306 * mm, "www.ingecart.eu  |  hablemos@ingecart.eu  |  +34 938 183 316")

    # Hidden area marker for print operator
    c.setStrokeColor(colors.HexColor("#FF6A00"))
    c.setLineWidth(1)
    c.line(x, y + hidden_bottom, x + final_w, y + hidden_bottom)
    c.setFillColor(colors.HexColor("#FF6A00"))
    c.setFont("Helvetica", 10)
    c.drawString(x + 8 * mm, y + hidden_bottom + 3 * mm, "AREA OCULTA EN BASE ROLLUP (150 mm)")

    # Safe area
    draw_safe_area(c, x, y + hidden_bottom, final_w, final_h - hidden_bottom, margin=15 * mm)

    draw_crop_marks(c, x, y, final_w, final_h)
    c.save()


def create_print_specs(path: Path):
    txt = (
        "ESPECIFICACIONES DE IMPRENTA PREMIUM - FESPA 2026\n"
        "===============================================\n\n"
        "1) TRIPTICO A4\n"
        "- Formato final: 297 x 210 mm (horizontal)\n"
        "- Sangrado: 3 mm perimetral\n"
        "- Margen de seguridad recomendado: 5 mm\n"
        "- Paneles: 3 paneles verticales\n"
        "- Entrega: PDF 2 paginas (exterior + interior) con marcas de corte\n\n"
        "2) ROLLUP STAND\n"
        "- Formato final: 850 x 2000 mm\n"
        "- Sangrado: 3 mm perimetral\n"
        "- Margen de seguridad recomendado: 15 mm\n"
        "- Area oculta base: 150 mm inferior\n"
        "- Entrega: PDF con marcas de corte y guia de area oculta\n\n"
        "3) COLOR Y PRODUCCION\n"
        "- Perfil sugerido: CMYK Coated FOGRA39 o segun imprenta\n"
        "- Resolucion imagenes: 300 dpi recomendada\n"
        "- Fuentes: trazadas o incrustadas segun flujo preprensa\n"
        "- Revisar pruebas de color antes de tirada final\n"
    )
    path.write_text(txt, encoding="utf-8")


def main():
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    trifold_pdf = DEST_DIR / "08_Triptico_A4_Imprenta_Premium_FESPA_2026.pdf"
    rollup_pdf = DEST_DIR / "09_Rollup_85x200_Imprenta_Premium_FESPA_2026.pdf"
    specs_txt = DEST_DIR / "10_Especificaciones_Imprenta_Premium_FESPA_2026.txt"

    create_trifold_a4_print_pdf(trifold_pdf)
    create_rollup_print_pdf(rollup_pdf)
    create_print_specs(specs_txt)

    print(f"Generado: {trifold_pdf}")
    print(f"Generado: {rollup_pdf}")
    print(f"Generado: {specs_txt}")


if __name__ == "__main__":
    main()
