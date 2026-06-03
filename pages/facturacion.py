import os
import sys
import importlib.util
from datetime import date

import pandas as pd
import streamlit as st

ERP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../erp_facturacion/erp.py"))
spec = importlib.util.spec_from_file_location("erp_module", ERP_PATH)
erp = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(erp)

erp.init_db()

st.title("Facturacion ERP Profesional")
st.caption("Dashboard, CRM clientes, facturacion multi-linea, impuestos y PDF profesional.")

menu = st.sidebar.radio(
    "Modulo",
    [
        "Dashboard",
        "Configuracion Empresa",
        "CRM Clientes",
        "Facturacion",
        "Facturas Emitidas",
        "Reporting",
    ],
)


def fmt_eur(v: float) -> str:
    return f"{float(v):,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", ".")


def clean_text(value) -> str:
    return str(value or "").strip()


def render_invoice_preview(
    invoice_number: str,
    company: dict,
    client: dict,
    invoice_date: str,
    due_date: str,
    payment_method: str,
    lines: list,
    expenses: list,
    iva_rate: float,
    irpf_rate: float,
) -> None:
    lines_total = sum(l["qty"] * l["unit_price"] for l in lines)
    expenses_total = sum(e["amount"] for e in expenses)
    subtotal = lines_total + expenses_total
    iva = subtotal * (iva_rate / 100.0)
    irpf = subtotal * (irpf_rate / 100.0)
    total = subtotal + iva - irpf

    st.markdown("### Previsualizacion profesional")
    st.markdown(f"## FACTURA {invoice_number}")

    logo_path = company.get("logo_path", "")
    if logo_path and os.path.exists(logo_path):
        st.image(logo_path, width=180)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**EMISOR**")
        st.write(company.get("fiscal_name", ""))
        st.write(f"NIF: {company.get('nif', '')}")
        st.write(company.get("address", ""))
        city_line = " ".join(
            [company.get("postal_code", ""), company.get("city", ""), company.get("province", "")]
        ).strip()
        if city_line:
            st.write(city_line)
        st.write(f"Tel: {company.get('phone', '')}")
        st.write(f"Email: {company.get('email', '')}")

    with c2:
        st.markdown("**CLIENTE**")
        st.write(client.get("company_name", ""))
        st.write(f"NIF: {client.get('nif', '')}")
        st.write(client.get("address", ""))
        client_city = " ".join(
            [client.get("postal_code", ""), client.get("city", ""), client.get("province", "")]
        ).strip()
        if client_city:
            st.write(client_city)
        if client.get("email"):
            st.write(f"Email: {client.get('email', '')}")

    c3, c4, c5 = st.columns(3)
    c3.write(f"**Fecha emision:** {invoice_date}")
    c4.write(f"**Vencimiento:** {due_date}")
    c5.write(f"**Forma de pago:** {payment_method}")

    st.markdown("**Conceptos**")
    lines_df_preview = pd.DataFrame(
        [
            {
                "Descripcion": l["description"],
                "Cantidad": l["qty"],
                "Precio unitario": l["unit_price"],
                "Total": round(l["qty"] * l["unit_price"], 2),
            }
            for l in lines
        ]
    )
    st.dataframe(lines_df_preview, width='stretch', hide_index=True)

    if expenses:
        st.markdown("**Gastos**")
        expenses_df_preview = pd.DataFrame(
            [{"Descripcion": e["description"], "Importe": e["amount"]} for e in expenses]
        )
        st.dataframe(expenses_df_preview, width='stretch', hide_index=True)

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Base", fmt_eur(subtotal))
    s2.metric(f"IVA ({iva_rate:.1f}%)", fmt_eur(iva))
    s3.metric(f"IRPF ({irpf_rate:.1f}%)", fmt_eur(irpf))
    s4.metric("TOTAL", fmt_eur(total))

    st.markdown("---")
    st.markdown("**FORMA DE PAGO**")
    st.write("Transferencia bancaria")
    st.markdown("**IBAN**")
    st.write(company.get("iban", ""))


if menu == "Dashboard":
    m = erp.dashboard_metrics()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Facturacion Mes", fmt_eur(m["facturacion_mes"]))
    c2.metric("Pendiente Cobro", fmt_eur(m["pendiente_cobro"]))
    c3.metric("IVA Acumulado", fmt_eur(m["iva_acumulado"]))
    c4.metric("Clientes Activos", m["clientes_activos"])
    c5.metric("Facturas Emitidas", m["facturas_emitidas"])

    invoices = erp.list_invoices(limit=10)
    st.subheader("Ultimas facturas")
    if invoices:
        st.dataframe(pd.DataFrame(invoices), width='stretch')
    else:
        st.info("Todavia no hay facturas emitidas.")

elif menu == "Configuracion Empresa":
    st.subheader("Configuracion Empresa")
    profile = erp.get_company_profile()

    with st.form("company_profile_form"):
        c1, c2 = st.columns(2)
        fiscal_name = c1.text_input("Nombre fiscal", value=profile.get("fiscal_name") or "")
        trade_name = c2.text_input("Nombre comercial", value=profile.get("trade_name") or "")

        c3, c4 = st.columns(2)
        nif = c3.text_input("NIF", value=profile.get("nif") or "")
        phone = c4.text_input("Telefono", value=profile.get("phone") or "")

        address = st.text_input("Direccion", value=profile.get("address") or "")

        c5, c6, c7 = st.columns(3)
        postal_code = c5.text_input("Codigo postal", value=profile.get("postal_code") or "")
        city = c6.text_input("Ciudad", value=profile.get("city") or "")
        province = c7.text_input("Provincia", value=profile.get("province") or "")

        c8, c9 = st.columns(2)
        country = c8.text_input("Pais", value=profile.get("country") or "Espana")
        email = c9.text_input("Email", value=profile.get("email") or "")

        c10, c11 = st.columns(2)
        website = c10.text_input("Website", value=profile.get("website") or "")
        invoice_prefix = c11.text_input("Prefijo facturas", value=profile.get("invoice_prefix") or "REF")

        c12, c13 = st.columns(2)
        iban = c12.text_input("IBAN", value=profile.get("iban") or "")
        bic = c13.text_input("SWIFT/BIC", value=profile.get("bic") or "")

        logo_file = st.file_uploader("Logo corporativo", type=["png", "jpg", "jpeg", "webp"])

        submitted = st.form_submit_button("Guardar configuracion")
        if submitted:
            logo_path = profile.get("logo_path", "")
            if logo_file is not None:
                logo_name = f"company_logo_{logo_file.name}"
                save_path = os.path.join(os.path.dirname(__file__), "../erp_facturacion/logos", logo_name)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(logo_file.getbuffer())
                logo_path = save_path

            erp.update_company_profile(
                {
                    "fiscal_name": clean_text(fiscal_name),
                    "trade_name": clean_text(trade_name),
                    "nif": clean_text(nif),
                    "address": clean_text(address),
                    "postal_code": clean_text(postal_code),
                    "city": clean_text(city),
                    "province": clean_text(province),
                    "country": clean_text(country),
                    "phone": clean_text(phone),
                    "email": clean_text(email),
                    "website": clean_text(website),
                    "iban": clean_text(iban),
                    "bic": clean_text(bic),
                    "invoice_prefix": (clean_text(invoice_prefix) or "REF"),
                    "logo_path": logo_path,
                }
            )
            st.success("Configuracion de empresa guardada correctamente.")

    current = erp.get_company_profile()
    if current.get("logo_path") and os.path.exists(current["logo_path"]):
        st.image(current["logo_path"], caption="Logo actual", width=220)

elif menu == "CRM Clientes":
    st.subheader("Alta de cliente")
    with st.form("add_client_form"):
        c1, c2 = st.columns(2)
        company_name = c1.text_input("Empresa")
        nif = c2.text_input("NIF")
        address = st.text_input("Direccion fiscal")
        c3, c4 = st.columns(2)
        city = c3.text_input("Ciudad")
        province = c4.text_input("Provincia")
        c5, c6 = st.columns(2)
        postal_code = c5.text_input("Codigo postal")
        country = c6.text_input("Pais", value="Espana")
        c7, c8 = st.columns(2)
        phone = c7.text_input("Telefono")
        email = c8.text_input("Email")
        contact_person = st.text_input("Persona de contacto")
        submitted = st.form_submit_button("Guardar cliente")
        if submitted:
            if not company_name.strip() or not nif.strip():
                st.error("Empresa y NIF son obligatorios.")
            else:
                client_id = erp.add_client(
                    company_name=company_name.strip(),
                    nif=nif.strip(),
                    address=address.strip(),
                    city=city.strip(),
                    province=province.strip(),
                    postal_code=postal_code.strip(),
                    country=country.strip(),
                    phone=phone.strip(),
                    email=email.strip(),
                    contact_person=contact_person.strip(),
                )
                st.success(f"Cliente creado con ID {client_id}.")

    st.subheader("Listado de clientes")
    clients = erp.list_clients()
    if clients:
        st.dataframe(pd.DataFrame(clients), width='stretch')
    else:
        st.info("Aun no hay clientes.")

elif menu == "Facturacion":
    clients = erp.list_clients()
    if not clients:
        st.warning("Primero debes crear al menos un cliente en CRM Clientes.")
        st.stop()

    st.subheader("Crear factura profesional")
    next_number = erp.next_invoice_number()
    st.info(f"Proxima factura: {next_number}")

    client_options = {f"{c['company_name']} ({c['nif']})": c["id"] for c in clients}
    selected_client_label = st.selectbox("Cliente", list(client_options.keys()))
    selected_client_id = client_options[selected_client_label]

    c1, c2, c3 = st.columns(3)
    invoice_date = c1.date_input("Fecha emision", value=date.today())
    due_date = c2.date_input("Fecha vencimiento", value=date.today())
    payment_method = c3.selectbox("Forma de pago", ["Transferencia bancaria", "Bizum", "Tarjeta", "Efectivo"])

    c4, c5 = st.columns(2)
    iva_rate = c4.number_input("IVA (%)", min_value=0.0, max_value=50.0, value=21.0, step=0.5)
    irpf_rate = c5.number_input("IRPF (%)", min_value=0.0, max_value=50.0, value=7.0, step=0.5)

    st.markdown("### Conceptos")
    lines_df = st.data_editor(
        pd.DataFrame(
            [
                {"description": "Prospeccion comercial", "qty": 1.0, "unit_price": 4500.0},
            ]
        ),
        num_rows="dynamic",
        width='stretch',
        key="invoice_lines_editor",
    )

    st.markdown("### Gastos")
    expenses_df = st.data_editor(
        pd.DataFrame([
            {"description": "Kilometraje", "amount": 0.0},
        ]),
        num_rows="dynamic",
        width='stretch',
        key="invoice_expenses_editor",
    )

    notes = st.text_area("Notas / pie legal", value="")

    # Preview
    clean_lines = []
    for _, row in lines_df.iterrows():
        desc = str(row.get("description", "")).strip()
        qty = float(row.get("qty", 0) or 0)
        price = float(row.get("unit_price", 0) or 0)
        if desc and qty > 0 and price >= 0:
            clean_lines.append({"description": desc, "qty": qty, "unit_price": price})

    clean_expenses = []
    for _, row in expenses_df.iterrows():
        desc = str(row.get("description", "")).strip()
        amount = float(row.get("amount", 0) or 0)
        if desc and amount > 0:
            clean_expenses.append({"description": desc, "amount": amount})

    if clean_lines:
        selected_client = erp.get_client(selected_client_id) or {}
        company_profile = erp.get_company_profile()
        render_invoice_preview(
            invoice_number=next_number,
            company=company_profile,
            client=selected_client,
            invoice_date=invoice_date.isoformat(),
            due_date=due_date.isoformat(),
            payment_method=payment_method,
            lines=clean_lines,
            expenses=clean_expenses,
            iva_rate=iva_rate,
            irpf_rate=irpf_rate,
        )

    if st.button("Emitir factura y generar PDF", type="primary"):
        if not clean_lines:
            st.error("Debes incluir al menos una linea valida.")
        else:
            result = erp.create_invoice(
                client_id=selected_client_id,
                invoice_date=invoice_date.isoformat(),
                due_date=due_date.isoformat(),
                payment_method=payment_method,
                lines=clean_lines,
                expenses=clean_expenses,
                iva_rate=iva_rate / 100.0,
                irpf_rate=irpf_rate / 100.0,
                notes=notes,
            )
            st.success(f"Factura {result['invoice_number']} creada correctamente.")
            with open(result["pdf_path"], "rb") as f:
                st.download_button(
                    "Descargar PDF profesional",
                    data=f,
                    file_name=os.path.basename(result["pdf_path"]),
                    mime="application/pdf",
                )

elif menu == "Facturas Emitidas":
    st.subheader("Facturas emitidas")
    invoices = erp.list_invoices(limit=500)
    if not invoices:
        st.info("No hay facturas emitidas.")
    else:
        df = pd.DataFrame(invoices)
        st.dataframe(df, width='stretch')
        invoice_id = st.number_input("Abrir factura por ID", min_value=1, step=1)
        if st.button("Descargar PDF"):
            inv = erp.get_invoice(int(invoice_id))
            if not inv:
                st.error("Factura no encontrada")
            else:
                pdf_path = os.path.join(
                    os.path.dirname(__file__),
                    "../erp_facturacion/invoices",
                    f"{inv['header']['invoice_number']}.pdf",
                )
                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            "Descargar PDF",
                            data=f,
                            file_name=os.path.basename(pdf_path),
                            mime="application/pdf",
                        )
                else:
                    st.error("No existe PDF para esta factura.")

elif menu == "Reporting":
    st.subheader("Reporting anual")
    year = st.number_input("Ano", min_value=2020, max_value=2100, value=date.today().year, step=1)
    r = erp.yearly_reporting(int(year))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Facturado", fmt_eur(r["facturado"]))
    c2.metric("IVA repercutido", fmt_eur(r["iva_repercutido"]))
    c3.metric("IRPF retenido", fmt_eur(r["irpf_retenido"]))
    c4.metric("Pendiente cobro", fmt_eur(r["pendiente_cobro"]))
