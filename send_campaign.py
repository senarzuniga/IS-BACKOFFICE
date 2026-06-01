import os
import pandas as pd

import email
from email import policy
import win32com.client as win32

UPLOAD_DIR = "uploaded_campaign_files"
EXCEL_PATH = os.path.join(UPLOAD_DIR, "destinatarios.xlsx")
EML_PATH = os.path.join(UPLOAD_DIR, "plantilla.eml")




# Extrae asunto, cuerpo (html o texto), imágenes y adjuntos de un .eml
def extraer_eml_completo(eml_path):
    with open(eml_path, "rb") as f:
        msg = email.message_from_bytes(f.read(), policy=policy.default)
    asunto = msg['subject']
    cuerpo_html = None
    cuerpo_text = None
    imagenes = []
    adjuntos = []
    for part in msg.walk():
        ctype = part.get_content_type()
        disp = str(part.get("Content-Disposition"))
        if ctype == "text/html" and cuerpo_html is None:
            cuerpo_html = part.get_content()
        elif ctype == "text/plain" and cuerpo_text is None:
            cuerpo_text = part.get_content()
        elif "attachment" in disp or "inline" in disp:
            filename = part.get_filename()
            if filename:
                content_id = part.get("Content-ID")
                payload = part.get_payload(decode=True)
                adjuntos.append({
                    "filename": filename,
                    "payload": payload,
                    "content_id": content_id
                })
                if ctype.startswith("image/"):
                    imagenes.append({
                        "filename": filename,
                        "payload": payload,
                        "content_id": content_id
                    })
    cuerpo = cuerpo_html if cuerpo_html else cuerpo_text
    return asunto, cuerpo, imagenes, adjuntos


# Enviar correo usando Outlook Desktop, incluyendo imágenes y adjuntos
def enviar_correo_outlook(destinatario, asunto, mensaje_html, imagenes, adjuntos):
    try:
        outlook = win32.Dispatch('Outlook.Application')
        mail = outlook.CreateItem(0)
        mail.To = destinatario
        mail.Subject = asunto
        mail.HTMLBody = mensaje_html
        # Adjuntar imágenes inline y adjuntos
        for adj in adjuntos:
            attach = mail.Attachments.Add(Source=None, Type=1, DisplayName=adj["filename"])
            attach.PropertyAccessor.SetProperty("http://schemas.microsoft.com/mapi/proptag/0x370E001F", adj["filename"])
            # Si es imagen inline, setear Content-ID
            if adj["content_id"]:
                cid = adj["content_id"].strip("<>")
                attach.PropertyAccessor.SetProperty("http://schemas.microsoft.com/mapi/proptag/0x3712001F", cid)
            # Guardar el archivo temporalmente
            temp_path = os.path.join(UPLOAD_DIR, adj["filename"])
            with open(temp_path, "wb") as f:
                f.write(adj["payload"])
            attach.PathName = temp_path
        mail.Send()
        return True, "✅ Correo enviado"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"


def main():
    if not (os.path.exists(EXCEL_PATH) and os.path.exists(EML_PATH)):
        print("Faltan archivos. Sube los archivos desde la app primero.")
        return
    df = pd.read_excel(EXCEL_PATH)
    if not set(["Nombre", "Email"]).issubset(df.columns):
        print("El Excel debe tener columnas 'Nombre' y 'Email'.")
        return
    asunto, cuerpo, imagenes, adjuntos = extraer_eml_completo(EML_PATH)
    if not asunto or not cuerpo:
        print("No se pudo extraer asunto y cuerpo del .eml.")
        return
    enviados = 0
    errores = []
    for idx, row in df.iterrows():
        nombre = str(row["Nombre"]).strip()
        email_dest = str(row["Email"]).strip()
        if not nombre or not email_dest:
            errores.append(f"Fila {idx+2}: datos incompletos")
            continue
        mensaje_personalizado = cuerpo.replace("#", nombre)
        ok, msg = enviar_correo_outlook(email_dest, asunto, mensaje_personalizado, imagenes, adjuntos)
        if ok:
            enviados += 1
            print(f"Enviado a {email_dest}")
        else:
            errores.append(f"{email_dest}: {msg}")
            print(f"Error con {email_dest}: {msg}")
    print(f"Correos enviados: {enviados}")
    if errores:
        print("Errores:\n" + "\n".join(errores))

if __name__ == "__main__":
    main()
