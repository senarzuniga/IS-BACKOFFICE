"""
Página Streamlit para envío automático de correos — Ingecart
"""
# ============================================
# EMAIL SENDER PARA IONOS SE
# Cuenta: cgo@ingecart.es
# ============================================

import smtplib
import streamlit as st
import pandas as pd
from email.mime.text import MIMEText
import email
from email import policy

# Contraseña fija (NO mostrar en panel)
PASSWORD_IONOS = "Ingecartmail20261#"  # Sustituye por la contraseña real

# Función para extraer asunto y cuerpo de un .eml

def extraer_eml(eml_bytes):
    try:
        msg = email.message_from_bytes(eml_bytes, policy=policy.default)
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
    except Exception as e:
        st.error(f"Error leyendo el archivo .eml: {e}")
        return None, None

# Función para enviar correo

def enviar_correo_ionos(destinatario, asunto, mensaje):
    try:
        servidor = smtplib.SMTP("smtp.ionos.es", 587)
        servidor.starttls()
        servidor.login("cgo@ingecart.es", PASSWORD_IONOS)
        msg = MIMEText(mensaje, 'plain', 'utf-8')
        msg['From'] = "cgo@ingecart.es"
        msg['To'] = destinatario
        msg['Subject'] = asunto
        servidor.send_message(msg)
        servidor.quit()
        return True, "✅ Correo enviado"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

# Interfaz Streamlit

st.title("📧 Campaña de Emails IONOS SE - INGECART")
st.write("""
1. Sube un archivo Excel con las columnas **Nombre** y **Email**.
2. Sube un archivo .eml como plantilla del mensaje (usa # donde irá el nombre).
3. Pulsa 'Enviar campaña' para enviar un email personalizado a cada destinatario.
""")

excel_file = st.file_uploader("Excel de destinatarios (Nombre, Email)", type=["xlsx", "xls", "csv"])
eml_file = st.file_uploader("Plantilla de correo (.eml)", type=["eml"])

if st.button("Enviar campaña"):
    if not (excel_file and eml_file):
        st.warning("Completa todos los campos y sube los archivos necesarios.")
    else:
        try:
            if excel_file.name.endswith("csv"):
                df = pd.read_csv(excel_file)
            else:
                df = pd.read_excel(excel_file)
        except Exception as e:
            st.error(f"Error leyendo el Excel: {e}")
            st.stop()
        if not set(["Nombre", "Email"]).issubset(df.columns):
            st.error("El Excel debe tener columnas 'Nombre' y 'Email'.")
            st.stop()
        asunto, cuerpo = extraer_eml(eml_file.read())
        if not asunto or not cuerpo:
            st.error("No se pudo extraer asunto y cuerpo del .eml.")
            st.stop()
        enviados = 0
        errores = []
        for idx, row in df.iterrows():
            nombre = str(row["Nombre"]).strip()
            email_dest = str(row["Email"]).strip()
            if not nombre or not email_dest:
                errores.append(f"Fila {idx+2}: datos incompletos")
                continue
            mensaje_personalizado = cuerpo.replace("#", nombre)
            ok, msg = enviar_correo_ionos(email_dest, asunto, mensaje_personalizado)
            if ok:
                enviados += 1
            else:
                errores.append(f"{email_dest}: {msg}")
        st.success(f"Correos enviados: {enviados}")
        if errores:
            st.error("Errores:\n" + "\n".join(errores))