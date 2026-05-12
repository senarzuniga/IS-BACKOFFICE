#!/usr/bin/env python3
"""Extract and analyze Ingecart Palletizer PDFs for commercial content generation."""

import fitz  # PyMuPDF
from pathlib import Path

# Rutas de los PDFs
pdf_propuesta = r"C:\Users\Inaki Senar\Downloads\PROPUESTA PALETIZADOR PLUG&PLAY.pdf"
pdf_roi = r"C:\Users\Inaki Senar\Documents\INGECART\PRODUCTO\ROI\ROI PALETIZADOR EJEMPLO INGECART.pdf"

print("=" * 80)
print("ANÁLISIS PDF 1: PROPUESTA PALETIZADOR PLUG&PLAY")
print("=" * 80)

try:
    doc1 = fitz.open(pdf_propuesta)
    print(f"\n📄 Total páginas: {len(doc1)}")
    print(f"📄 Archivo: {Path(pdf_propuesta).name}\n")
    
    all_text = ""
    for page_num in range(len(doc1)):
        page = doc1[page_num]
        text = page.get_text("text")  # Force text-only mode
        all_text += text + "\n"
        
    print(all_text)
        
except FileNotFoundError:
    print(f"❌ Archivo no encontrado: {pdf_propuesta}")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")

print("\n" + "=" * 80)
print("ANÁLISIS PDF 2: ROI PALETIZADOR")
print("=" * 80)

try:
    doc2 = fitz.open(pdf_roi)
    print(f"\n📄 Total páginas: {len(doc2)}")
    print(f"📄 Archivo: {Path(pdf_roi).name}\n")
    
    all_text = ""
    for page_num in range(len(doc2)):
        page = doc2[page_num]
        text = page.get_text("text")  # Force text-only mode
        all_text += text + "\n"
        
    print(all_text)
        
except FileNotFoundError:
    print(f"❌ Archivo no encontrado: {pdf_roi}")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
