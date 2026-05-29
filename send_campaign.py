import os
import pandas as pd
import smtplib
from email.mime.text import MIMEText
import email
from email import policy

UPLOAD_DIR = "uploaded_campaign_files"
EXCEL_PATH = os.path.join(UPLOAD_DIR, "destinatarios.xlsx")
EML_PATH = os.path.join(UPLOAD_DIR, "plantilla.eml")

# Configuración SMTP
SMTP_SERVER = "smtp.ionos.es"
SMTP_PORT = 587
SMTP_USER = "cgo@ingecart.es"
SMTP_PASS = "Ingecartmail20261#"  # Cambia por la contraseña real

# Función para extraer asunto y cuerpo de un .eml
def extraer_eml(eml_path):
    with open(eml_path, "rb") as f:
        msg = email.message_from_bytes(f.read(), policy=policy.default)
    asunto = msg['subject']
    cuerpo = None
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                cuerpo = part.get_content()
                break
        if cuerpo is None:
            cuerpo = msg.get_body(preferencelist=('plain', 'html')).get_content()
    else:
        cuerpo = msg.get_content()
    return asunto, cuerpo

def enviar_correo(destinatario, asunto, mensaje):
    try:
        servidor = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        servidor.starttls()
        servidor.login(SMTP_USER, SMTP_PASS)
        msg = MIMEText(mensaje, 'plain', 'utf-8')
        msg['From'] = SMTP_USER
        msg['To'] = destinatario
        msg['Subject'] = asunto
        servidor.send_message(msg)
        servidor.quit()
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
    asunto, cuerpo = extraer_eml(EML_PATH)
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
        ok, msg = enviar_correo(email_dest, asunto, mensaje_personalizado)
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
