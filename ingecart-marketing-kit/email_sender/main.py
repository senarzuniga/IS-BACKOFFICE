
import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import imaplib
import email
import json
from pathlib import Path


st.set_page_config(page_title="Envío Automático de Correos", layout="wide")
st.title("Envío Automático de Correos — Ingecart")

# Leer configuración de IONOS
config_path = Path(__file__).parent / "config_email_sender.json"
if not config_path.exists():
    st.error("No se encontró config_email_sender.json. Crea el archivo y rellena tus datos de acceso.")
    st.stop()
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

TIPOS = ["Prospección", "Campaña", "Newsletter", "Seguimiento", "Otro"]
tab = st.selectbox("Tipo de envío", TIPOS)

asunto = st.text_input("Asunto del correo (de tu bandeja de borradores)")
excel_path = st.text_input("Ruta al archivo Excel con Nombre y Email", placeholder="C:/ruta/a/archivo.xlsx")

st.info("El contenido del correo se tomará del borrador seleccionado en tu cuenta de correo. El símbolo '#' será reemplazado por el nombre del destinatario.")

st.markdown(f"**Remitente configurado:** {config.get('email', '')}")
st.divider()

def cargar_destinatarios(path):
    try:
        df = pd.read_excel(path)
        if not {'Nombre', 'Email'}.issubset(df.columns):
            st.error("El Excel debe tener columnas 'Nombre' y 'Email'.")
            return None
        return df
    except Exception as e:
        st.error(f"Error cargando Excel: {e}")
        return None


def obtener_borrador(asunto, config):
    """
    Busca el borrador por asunto en la cuenta del remitente (IMAP IONOS).
    Devuelve el cuerpo del mensaje (HTML o texto).
    """
    try:
        imap = imaplib.IMAP4_SSL(config["imap_host"], config["imap_port"])
        imap.login(config["email"], config["password"])
        imap.select('Drafts')
        status, messages = imap.search(None, f'(HEADER Subject "{asunto}")')
        if status != 'OK' or not messages[0]:
            st.error("No se encontró el borrador con ese asunto.")
            return None
        for num in messages[0].split():
            status, data = imap.fetch(num, '(RFC822)')
            if status == 'OK':
                msg = email.message_from_bytes(data[0][1])
                if msg.is_multipart():
                    for part in msg.walk():
                        ctype = part.get_content_type()
                        if ctype == 'text/html':
                            return part.get_payload(decode=True).decode()
                        elif ctype == 'text/plain':
                            return part.get_payload(decode=True).decode()
                else:
                    return msg.get_payload(decode=True).decode()
        st.error("No se pudo extraer el contenido del borrador.")
        return None
    except Exception as e:
        st.error(f"Error accediendo a borradores: {e}")
        return None


def enviar_correo(config, destinatario, asunto, cuerpo, nombre):
    try:
        msg = MIMEMultipart()
        msg['From'] = formataddr(("Ingecart", config["email"]))
        msg['To'] = destinatario
        msg['Subject'] = asunto
        cuerpo_personalizado = cuerpo.replace('#', nombre)
        msg.attach(MIMEText(cuerpo_personalizado, 'html'))
        with smtplib.SMTP_SSL(config["smtp_host"], config["smtp_port"]) as server:
            server.login(config["email"], config["password"])
            server.sendmail(config["email"], destinatario, msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)


if st.button("Cargar destinatarios"):
    if excel_path:
        df = cargar_destinatarios(excel_path)
        if df is not None:
            st.session_state['df_destinatarios'] = df
            st.success(f"{len(df)} destinatarios cargados.")
            st.dataframe(df)


if 'df_destinatarios' in st.session_state:
    df = st.session_state['df_destinatarios']
    st.write("Lista de destinatarios:")
    st.dataframe(df)
    st.divider()
    if st.button("Enviar correos (uno a uno)"):
        if not asunto:
            st.error("Debes completar el asunto.")
        else:
            cuerpo = obtener_borrador(asunto, config)
            if cuerpo:
                logs = []
                with st.spinner("Enviando correos..."):
                    for idx, row in df.iterrows():
                        nombre = str(row['Nombre'])
                        email_dest = str(row['Email'])
                        ok, err = enviar_correo(config, email_dest, asunto, cuerpo, nombre)
                        if ok:
                            logs.append(f"✅ {nombre} <{email_dest}>")
                        else:
                            logs.append(f"❌ {nombre} <{email_dest}>: {err}")
                st.success("Envío finalizado. Revisa el log abajo.")
                st.text_area("Log de envíos", value='\n'.join(logs), height=200)
