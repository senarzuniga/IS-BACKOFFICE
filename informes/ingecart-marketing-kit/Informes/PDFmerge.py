from PyPDF2 import PdfMerger

cover_pdf = r"C:\Users\Inaki Senar\Documents\GitHub\IS-BACKOFFICE\informes\ingecart-marketing-kit\Informes\PSC_PROPOSAL_REAL.pdf"
offer_pdf = r"C:\Users\Inaki Senar\Documents\GitHub\IS-BACKOFFICE\informes\ingecart-marketing-kit\Informes\First page OF110.pdf"
output_pdf = r"C:\Users\Inaki Senar\Documents\GitHub\IS-BACKOFFICE\informes\ingecart-marketing-kit\Informes\PSC_merged.pdf"

merger = PdfMerger()
# Append in reversed order so the second PDF becomes the first in the merged file
merger.append(offer_pdf)
merger.append(cover_pdf)

with open(output_pdf, "wb") as f:
    merger.write(f)

merger.close()

print(f"PDF final generado en:\n{output_pdf}")