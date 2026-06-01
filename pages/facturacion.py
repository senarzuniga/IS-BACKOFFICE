import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../erp_facturacion')))
import erp

st.title("🧾 Facturación y ERP")

st.sidebar.header("Gestión de Facturación")

menu = st.sidebar.radio("Acción", [
    "Crear Cliente",
    "Crear Factura",
    "Ver Cliente",
    "Ver Factura"
])

if menu == "Crear Cliente":
    st.subheader("Crear nuevo cliente")
    with st.form("add_client_form"):
        name = st.text_input("Nombre")
        nif = st.text_input("NIF")
        address = st.text_input("Dirección")
        submitted = st.form_submit_button("Guardar Cliente")
        if submitted:
            erp.add_client(name, nif, address)
            st.success(f"Cliente '{name}' guardado correctamente.")

elif menu == "Crear Factura":
    st.subheader("Crear nueva factura")
    client_id = st.number_input("ID Cliente", min_value=1, step=1)
    services = st.number_input("Servicios (€)", min_value=0.0, step=0.01)
    expenses = st.number_input("Gastos (€)", min_value=0.0, step=0.01)
    if st.button("Generar Factura"):
        invoice_id = erp.create_invoice(client_id, services, expenses)
        st.success(f"Factura generada con ID: {invoice_id}")

elif menu == "Ver Cliente":
    st.subheader("Consultar cliente")
    client_id = st.number_input("ID Cliente", min_value=1, step=1)
    if st.button("Buscar Cliente"):
        client = erp.get_client(client_id)
        if client:
            st.write({"ID": client[0], "Nombre": client[1], "NIF": client[2], "Dirección": client[3]})
        else:
            st.error("Cliente no encontrado.")

elif menu == "Ver Factura":
    st.subheader("Consultar factura")
    invoice_id = st.number_input("ID Factura", min_value=1, step=1)
    if st.button("Buscar Factura"):
        # Buscar archivo Excel generado
        invoice_path = os.path.join(os.path.dirname(__file__), "../erp_facturacion/invoices", f"Factura_{int(invoice_id)}.xlsx")
        if os.path.exists(invoice_path):
            with open(invoice_path, "rb") as f:
                st.download_button("Descargar Factura Excel", f, file_name=f"Factura_{invoice_id}.xlsx")
            st.info(f"Factura encontrada: Factura_{invoice_id}.xlsx")
        else:
            st.error("Factura no encontrada.")
