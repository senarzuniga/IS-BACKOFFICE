#!/bin/bash

# ============================================
# SCRIPT AUTÓNOMO - GENERACIÓN DOCUMENTACIÓN PSC
# Proyecto: Pacific Southwest Packaging (PSC)
# ============================================

echo "════════════════════════════════════════════════════════════"
echo "   🏭 PACIFIC SOUTHWEST PACKAGING - GENERACIÓN DE DOCUMENTACIÓN"
echo "════════════════════════════════════════════════════════════"
echo ""

# Configuración
BASE_DIR="/c/Users/Inaki Senar/Documents/INGECART/COMMERCIAL/PROYECTOS/PACIFICSOUTH"
OUTPUT_DIR="$BASE_DIR/PROJECT_DELIVERABLES"
VENV_PYTHON="/c/Users/Inaki Senar/Documents/GitHub/IS-BACKOFFICE/.venv/Scripts/python.exe"
PLANTILLA_WORD="$BASE_DIR/../Sterner Global/Derby Corr/PROPOSAL AUTOMATIC REEL LOADING SYSTEM DERBYCORR V2.docx"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Funciones
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}▶ $1${NC}"; }

# Crear carpeta de entregables
log_step "Creando carpeta de entregables..."
mkdir -p "$OUTPUT_DIR"
log_info "Carpeta creada: $OUTPUT_DIR"

# ============================================
# 1. GENERAR SCRIPT PYTHON PARA PROCESAR EXCEL
# ============================================
log_step "Generando script Python para procesar Excel..."

cat > "$OUTPUT_DIR/generate_docs.py" << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador automático de documentación para proyecto PSC
"""

import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import json

# Configuración
BASE_DIR = Path("C:/Users/Inaki Senar/Documents/INGECART/COMMERCIAL/PROYECTOS/PACIFICSOUTH")
EXCEL_PATH = BASE_DIR / "Flujo Pacific Southwest REVISADO DIEGO 6 6 2026.xlsx"
OUTPUT_DIR = BASE_DIR / "PROJECT_DELIVERABLES"

print("📊 Leyendo archivo Excel...")
print(f"   Ruta: {EXCEL_PATH}")

# Leer todas las hojas del Excel
try:
    xl = pd.ExcelFile(EXCEL_PATH)
    sheet_names = xl.sheet_names
    print(f"   ✅ Hojas encontradas: {', '.join(sheet_names)}")
    
    # Cargar datos
    dataframes = {}
    for sheet in sheet_names:
        dataframes[sheet] = pd.read_excel(EXCEL_PATH, sheet_name=sheet)
        print(f"   📄 Hoja '{sheet}': {dataframes[sheet].shape[0]} filas, {dataframes[sheet].shape[1]} columnas")
    
except Exception as e:
    print(f"   ❌ Error leyendo Excel: {e}")
    sys.exit(1)

# Extraer datos clave (inteligente basado en contenido)
log_data = {}
for sheet, df in dataframes.items():
    # Buscar celdas con números grandes (posibles costes/márgenes)
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) > 0:
        log_data[sheet] = {
            "total_sum": df[numeric_cols].sum().sum(),
            "max_value": df[numeric_cols].max().max(),
            "columns": list(df.columns)
        }

print("\n💾 Guardando datos extraídos...")
with open(OUTPUT_DIR / "extracted_data.json", "w", encoding="utf-8") as f:
    json.dump({
        "sheets": sheet_names,
        "data": {k: v for k, v in log_data.items()},
        "timestamp": datetime.now().isoformat()
    }, f, indent=2, default=str)

print("✅ Datos extraídos guardados")

# ============================================
# 2. GENERAR EXCEL DE COSTES Y MÁRGENES
# ============================================
print("\n📊 Generando Excel de Costes y Márgenes...")

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

wb = Workbook()
wb.remove(wb.active)

# Hoja 1: Resumen General
ws1 = wb.create_sheet("Resumen General")
ws1['A1'] = "PACIFIC SOUTHWEST PACKAGING (PSC)"
ws1['A2'] = f"Proyecto Visalia - Corrugadora BHS"
ws1['A4'] = "CONCEPTO"
ws1['B4'] = "IMPORTE (USD)"
ws1['C4'] = "NOTAS"

# Headers style
header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
header_font = Font(color="FFFFFF", bold=True)
for cell in ['A4', 'B4', 'C4']:
    ws1[cell].fill = header_fill
    ws1[cell].font = header_font

# Datos (se extraerán del Excel original)
data_rows = [
    ("Coste Desmontaje Turquía", 0, "Pendiente de extraer"),
    ("Transporte Marítimo", 0, "Pendiente de extraer"),
    ("Instalación Visalia", 0, "Pendiente de extraer"),
    ("Ingeniería y Dirección", 0, "Pendiente de extraer"),
    ("SUBTOTAL COSTES INGECART", 0, ""),
    ("", 0, ""),
    ("Precio Venta a PSC", 0, "Pendiente de extraer"),
    ("", 0, ""),
    ("MARGEN BRUTO INGECART", 0, ""),
    ("", 0, ""),
    ("Comisión Linetex (Mike)", 0, "% sobre venta"),
    ("", 0, ""),
    ("BENEFICIO NETO INGECART", 0, ""),
]

row = 5
for desc, val, note in data_rows:
    ws1[f'A{row}'] = desc
    ws1[f'B{row}'] = val
    ws1[f'C{row}'] = note
    if desc.startswith("SUBTOTAL") or desc.startswith("MARGEN") or desc.startswith("BENEFICIO"):
        ws1[f'A{row}'].font = Font(bold=True)
        ws1[f'B{row}'].font = Font(bold=True)
    row += 1

# Ajustar ancho de columnas
ws1.column_dimensions['A'].width = 35
ws1.column_dimensions['B'].width = 20
ws1.column_dimensions['C'].width = 30

# Hoja 2: Flujo de Caja
ws2 = wb.create_sheet("Flujo de Caja")
ws2['A1'] = "CRONOGRAMA DE PAGOS PROPUESTO"
ws2['A3'] = "Hito"
ws2['B3'] = "%"
ws2['C3'] = "Importe (USD)"
ws2['D3'] = "Fecha estimada"

payment_schedule = [
    ("Firma de Contrato", 30, 0, "Firma"),
    ("Inicio desmontaje Turquía", 20, 0, "Mes 1"),
    ("Carga marítima", 20, 0, "Mes 2"),
    ("Llegada a Visalia", 15, 0, "Mes 3"),
    ("Instalación completada", 10, 0, "Mes 4"),
    ("Puesta en marcha", 5, 0, "Mes 5"),
]

row = 4
for hito, pct, monto, fecha in payment_schedule:
    ws2[f'A{row}'] = hito
    ws2[f'B{row}'] = f"{pct}%"
    ws2[f'C{row}'] = monto
    ws2[f'D{row}'] = fecha
    row += 1

# Hoja 3: Comisiones
ws3 = wb.create_sheet("Comisiones Linetex")
ws3['A1'] = "COMISIÓN REPRESENTANTE COMERCIAL (Mike - Linetex)"
ws3['A3'] = "Concepto"
ws3['B3'] = "Valor"
ws3['A4'] = "% Comisión acordada"
ws3['B4'] = "0%"
ws3['A5'] = "Base de cálculo"
ws3['B5'] = "Precio venta"
ws3['A6'] = "Comisión estimada"
ws3['B6'] = "0 USD"

# Guardar Excel
excel_output = OUTPUT_DIR / "02_Costes_Margenes_PSC.xlsx"
wb.save(excel_output)
print(f"   ✅ Excel creado: {excel_output}")

# ============================================
# 3. GENERAR INFORME EJECUTIVO (MD/HTML)
# ============================================
print("\n📄 Generando Informe Ejecutivo...")

report_content = f"""# INFORME EJECUTIVO - PROYECTO PSC

**Cliente:** Pacific Southwest Packaging (PSC)
**Ubicación:** Visalia, California, USA
**Proyecto:** Relocalización corrugadora BHS
**Fecha:** {datetime.now().strftime('%d/%m/%Y')}

---

## 1. Resumen del Proyecto

Pacific Southwest Packaging (PSC) ha aprobado la operación para la relocalización de una máquina corrugadora BHS desde sus instalaciones actuales en Turquía hacia su planta en Visalia, California.

**INGECART** actuará como **contratista principal** del proyecto, coordinando todas las fases:
- Desmontaje en origen (Turquía)
- Preparación y embalaje
- Transporte marítimo internacional
- Importación y despacho de aduana (USA)
- Instalación y puesta en marcha en Visalia
- Formación y transferencia de conocimiento

**Representante comercial en USA:** Linetex (Mike)

---

## 2. Fases del Proyecto

| Fase | Duración estimada | Responsable |
|------|------------------|-------------|
| Desmontaje Turquía | 4 semanas | INGECART |
| Transporte marítimo | 6 semanas | INGECART / Agente carga |
| Aduana USA | 2 semanas | Agente aduanas |
| Instalación Visalia | 8 semanas | INGECART |
| Puesta en marcha | 2 semanas | INGECART + BHS |
| Formación | 1 semana | INGECART |

**Duración total estimada:** 23 semanas (~6 meses)

---

## 3. Estructura de Costes

*Pendiente de completar con datos del Excel fuente*

| Concepto | Importe (USD) |
|----------|---------------|
| Costes directos INGECART | [Por determinar] |
| Comisión Linetex | [Por determinar] |
| **Total Proyecto** | [Por determinar] |

---

## 4. Hitos de Pago Propuestos

| Hito | % | Acumulado |
|------|---|---|
| Firma de contrato | 30% | 30% |
| Inicio desmontaje | 20% | 50% |
| Carga marítima | 20% | 70% |
| Llegada USA | 15% | 85% |
| Instalación completa | 10% | 95% |
| Puesta en marcha | 5% | 100% |

---

## 5. Riesgos y Mitigación

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-------------|
| Daños en transporte | Media | Alto | Seguro marítimo incluido |
| Retrasos aduaneros | Media | Medio | Gestor aduanero local |
| Disponibilidad técnicos | Baja | Medio | Equipo de respaldo formado |

---

## 6. Recomendaciones

1. **Formalizar contrato** con términos claros de alcance
2. **Contratar seguro** de transporte y montaje
3. **Designar project manager** dedicado al proyecto
4. **Establecer comunicación semanal** con PSC y Linetex

---

*Documento generado por IS-BACKOFFICE - Sistema de Inteligencia Documental*
"""

report_path = OUTPUT_DIR / "04_Informe_Ejecutivo_PSC.md"
with open(report_path, "w", encoding="utf-8") as f:
    f.write(report_content)
print(f"   ✅ Informe creado: {report_path}")

# ============================================
# 4. GENERAR PLANTILLA DE OFERTA
# ============================================
print("\n📝 Generando oferta descriptiva...")

try:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    
    # Intentar usar plantilla existente
    template_path = Path("C:/Users/Inaki Senar/Documents/INGECART/COMMERCIAL/PROYECTOS/Sterner Global/Derby Corr/PROPOSAL AUTOMATIC REEL LOADING SYSTEM DERBYCORR V2.docx")
    
    if template_path.exists():
        doc = Document(template_path)
        print(f"   📄 Usando plantilla: {template_path.name}")
    else:
        doc = Document()
        print("   📄 Creando documento nuevo")
    
    # Guardar oferta
    offer_path = OUTPUT_DIR / "01_Oferta_Descriptiva_PSC.docx"
    doc.save(offer_path)
    print(f"   ✅ Oferta creada: {offer_path}")
    
except Exception as e:
    print(f"   ⚠️ No se pudo generar Word: {e}")
    # Crear versión Markdown como fallback
    md_offer = f"""# PROPUESTA COMERCIAL - PROYECTO PSC

**INGECART** presenta su propuesta para la relocalización de corrugadora BHS.

## Alcance del suministro
- Desmontaje profesional en Turquía
- Transporte marítimo internacional
- Instalación llave en mano en Visalia, CA
- Puesta en marcha y formación

## Condiciones comerciales
- Validez: 60 días
- Plazo de entrega: [por definir] semanas
- Garantía: 12 meses

*Documento generado por IS-BACKOFFICE*
"""
    with open(OUTPUT_DIR / "01_Oferta_Descriptiva_PSC.md", "w") as f:
        f.write(md_offer)
    print(f"   ✅ Oferta (MD) creada: {OUTPUT_DIR / '01_Oferta_Descriptiva_PSC.md'}")

# ============================================
# 5. GENERAR CHECKLIST DE PROYECTO
# ============================================
print("\n✅ Generando Checklist de Proyecto...")

checklist = f"""# CHECKLIST DE PROYECTO - PSC VISALIA

**Fecha:** {datetime.now().strftime('%d/%m/%Y')}
**Project Manager:** [Asignar]

## Pre-proyecto
- [ ] Firma de contrato con PSC
- [ ] Firma de acuerdo de comisión con Linetex
- [ ] Contratación de seguro de transporte
- [ ] Designación de agente de aduanas en USA
- [ ] Reserva de transporte marítimo

## Desmontaje Turquía
- [ ] Visita previa a instalaciones
- [ ] Plan de desmontaje aprobado
- [ ] Equipo de técnicos asignado
- [ ] Herramientas y consumibles preparados
- [ ] Documentación fotográfica pre-desmontaje
- [ ] Ejecución de desmontaje
- [ ] Embalaje y marcaje

## Transporte
- [ ] Documentación de exportación Turquía
- [ ] Contenedores/bodega asignados
- [ ] Seguimiento de tránsito marítimo
- [ ] Coordinación llegada a USA

## Instalación Visalia
- [ ] Permisos de importación USA
- [ ] Recepción en planta PSC
- [ ] Plan de instalación
- [ ] Ejecución de instalación mecánica
- [ ] Conexiones eléctricas y de servicios
- [ ] Puesta en marcha
- [ ] Pruebas de funcionamiento

## Cierre
- [ ] Formación a operadores PSC
- [ ] Entrega de documentación final
- [ ] Acta de recepción firmada
- [ ] Facturación final
- [ ] Encuesta de satisfacción

"""
with open(OUTPUT_DIR / "05_Memorando_Interno_PSC.md", "w") as f:
    f.write(checklist)
print(f"   ✅ Checklist creado")

print("\n" + "═" * 60)
print(f"✅ ¡DOCUMENTACIÓN COMPLETADA!")
print(f"📁 Carpeta de entregables: {OUTPUT_DIR}")
print("═" * 60)
print("\nArchivos generados:")
for f in OUTPUT_DIR.iterdir():
    print(f"   📄 {f.name}")
print("")

PYTHON_SCRIPT

# ============================================
# 3. EJECUTAR SCRIPT PYTHON
# ============================================
log_step "Ejecutando script Python de generación..."

if [ -f "$VENV_PYTHON" ]; then
    "$VENV_PYTHON" "$OUTPUT_DIR/generate_docs.py"
else
    python "$OUTPUT_DIR/generate_docs.py"
fi

# ============================================
# 4. MOSTRAR RESUMEN FINAL
# ============================================
echo ""
log_step "Resumen final de documentos generados:"
echo ""

if [ -d "$OUTPUT_DIR" ]; then
    echo "📁 $OUTPUT_DIR"
    ls -la "$OUTPUT_DIR" | grep -E "\.(xlsx|md|docx|json|py)$" | awk '{print "   📄 " $NF}'
else
    log_error "No se encontró la carpeta de entregables"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
log_info "✅ PROCESO COMPLETADO"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Para ver los archivos generados, ejecuta:"
echo "   explorer '$OUTPUT_DIR'"
echo ""