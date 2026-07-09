from PyPDF2 import PdfMerger

cover_pdf = r"C:\Users\Inaki Senar\Documents\INGECART\COMMERCIAL\PROYECTOS\PACIFICSOUTH\First page OF110.pdf"
offer_pdf = r"C:\Users\Inaki Senar\Documents\INGECART\COMMERCIAL\PROYECTOS\PACIFICSOUTH\PCS BHS Corrugator Line OFF-2026-110.pdf"
output_pdf = r"C:\Users\Inaki Senar\Documents\INGECART\COMMERCIAL\PROYECTOS\PACIFICSOUTH\PSC_Offer_OFF-2026-110_Final.pdf"

merger = PdfMerger()
merger.append(cover_pdf)
merger.append(offer_pdf)

with open(output_pdf, "wb") as f:
    merger.write(f)

merger.close()

print(f"PDF final generado en:\n{output_pdf}")