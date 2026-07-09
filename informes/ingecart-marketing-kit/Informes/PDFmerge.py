from PyPDF2 import PdfMerger

cover_pdf = r"C:\Users\Inaki Senar\Documents\GitHub\IS-BACKOFFICE\informes\ingecart-marketing-kit\Informes\PSC_PROPOSAL_REAL.pdf"
offer_pdf = r"C:\Users\Inaki Senar\Documents\GitHub\IS-BACKOFFICE\informes\ingecart-marketing-kit\Informes\First page OF110.pdf"
output_pdf = r"C:\Users\Inaki Senar\Documents\GitHub\IS-BACKOFFICE\informes\ingecart-marketing-kit\Informes\PSC_merged.pdf"

merger = PdfMerger()
merger.append(cover_pdf)
merger.append(offer_pdf)

with open(output_pdf, "wb") as f:
    merger.write(f)

merger.close()

print(f"PDF final generado en:\n{output_pdf}")