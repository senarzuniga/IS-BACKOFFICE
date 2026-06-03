import os
import sqlite3
from datetime import date, datetime
from typing import Dict, List, Optional, Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

BASE_DIR = os.path.dirname(__file__)
DB = os.path.join(BASE_DIR, "database.db")
INVOICE_DIR = os.path.join(BASE_DIR, "invoices")
LOGO_DIR = os.path.join(BASE_DIR, "logos")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, dtype: str) -> None:
    cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {dtype}")


def init_db() -> None:
    conn = _get_conn()
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS company_profile(
            id INTEGER PRIMARY KEY,
            fiscal_name TEXT,
            trade_name TEXT,
            nif TEXT,
            address TEXT,
            postal_code TEXT,
            city TEXT,
            province TEXT,
            country TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            iban TEXT,
            bic TEXT,
            invoice_prefix TEXT,
            logo_path TEXT
        )
        """
    )

    # Compatibilidad con esquema anterior de company_profile
    _ensure_column(conn, "company_profile", "trade_name", "TEXT")
    _ensure_column(conn, "company_profile", "website", "TEXT")
    _ensure_column(conn, "company_profile", "bic", "TEXT")
    _ensure_column(conn, "company_profile", "invoice_prefix", "TEXT")

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS clients(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            nif TEXT,
            address TEXT,
            city TEXT,
            province TEXT,
            postal_code TEXT,
            country TEXT,
            phone TEXT,
            email TEXT,
            contact_person TEXT
        )
        """
    )

    # Compatibilidad con versiones antiguas de la tabla clients
    _ensure_column(conn, "clients", "company_name", "TEXT")
    _ensure_column(conn, "clients", "city", "TEXT")
    _ensure_column(conn, "clients", "province", "TEXT")
    _ensure_column(conn, "clients", "postal_code", "TEXT")
    _ensure_column(conn, "clients", "country", "TEXT")
    _ensure_column(conn, "clients", "phone", "TEXT")
    _ensure_column(conn, "clients", "email", "TEXT")
    _ensure_column(conn, "clients", "contact_person", "TEXT")

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS invoice_headers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE,
            invoice_date TEXT,
            due_date TEXT,
            client_id INTEGER,
            status TEXT,
            payment_method TEXT,
            subtotal REAL,
            iva REAL,
            irpf REAL,
            total REAL,
            notes TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS invoice_lines(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            description TEXT,
            qty REAL,
            unit_price REAL,
            total REAL,
            FOREIGN KEY (invoice_id) REFERENCES invoice_headers(id)
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS invoice_expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            description TEXT,
            amount REAL,
            FOREIGN KEY (invoice_id) REFERENCES invoice_headers(id)
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS payments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            payment_date TEXT,
            amount REAL,
            method TEXT,
            reference TEXT,
            FOREIGN KEY (invoice_id) REFERENCES invoice_headers(id)
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS settings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE,
            value TEXT
        )
        """
    )

    init_company_profile(conn)

    conn.commit()
    conn.close()

    os.makedirs(INVOICE_DIR, exist_ok=True)
    os.makedirs(LOGO_DIR, exist_ok=True)


def init_company_profile(conn: Optional[sqlite3.Connection] = None) -> None:
    own_conn = False
    if conn is None:
        conn = _get_conn()
        own_conn = True
    c = conn.cursor()
    existing = c.execute("SELECT id FROM company_profile WHERE id = 1").fetchone()
    if not existing:
        c.execute(
            """
            INSERT INTO company_profile(
                id, fiscal_name, trade_name, nif, address, postal_code, city,
                province, country, phone, email, website, iban, bic,
                invoice_prefix, logo_path
            ) VALUES(1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Autónomo / Consultoría",
                "IS-BACKOFFICE",
                "PENDIENTE",
                "Dirección pendiente",
                "",
                "",
                "",
                "España",
                "",
                "",
                "",
                "",
                "",
                "REF",
                "",
            ),
        )
    if own_conn:
        conn.commit()
        conn.close()


def save_company_profile(profile: Dict) -> None:
    init_db()
    conn = _get_conn()
    c = conn.cursor()
    c.execute(
        """
        INSERT OR REPLACE INTO company_profile(
            id, fiscal_name, trade_name, nif, address, postal_code, city,
            province, country, phone, email, website, iban, bic,
            invoice_prefix, logo_path
        ) VALUES(1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            profile.get("fiscal_name", ""),
            profile.get("trade_name", ""),
            profile.get("nif", ""),
            profile.get("address", ""),
            profile.get("postal_code", ""),
            profile.get("city", ""),
            profile.get("province", ""),
            profile.get("country", ""),
            profile.get("phone", ""),
            profile.get("email", ""),
            profile.get("website", ""),
            profile.get("iban", ""),
            profile.get("bic", ""),
            profile.get("invoice_prefix", "REF"),
            profile.get("logo_path", ""),
        ),
    )
    conn.commit()
    conn.close()


def add_client(
    company_name: str,
    nif: str,
    address: str,
    city: str = "",
    province: str = "",
    postal_code: str = "",
    country: str = "España",
    phone: str = "",
    email: str = "",
    contact_person: str = "",
) -> int:
    init_db()
    conn = _get_conn()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO clients(
            company_name, nif, address, city, province, postal_code,
            country, phone, email, contact_person
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            company_name,
            nif,
            address,
            city,
            province,
            postal_code,
            country,
            phone,
            email,
            contact_person,
        ),
    )
    client_id = c.lastrowid
    conn.commit()
    conn.close()
    return int(client_id)


def list_clients() -> List[Dict]:
    init_db()
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, company_name, nif, email, city FROM clients ORDER BY company_name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_client(client_id: int) -> Optional[Dict]:
    init_db()
    conn = _get_conn()
    row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_company_profile() -> Dict:
    init_db()
    conn = _get_conn()
    row = conn.execute("SELECT * FROM company_profile WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else {}


def update_company_profile(profile: Dict) -> None:
    current = get_company_profile()
    merged = {
        **current,
        **{k: v for k, v in profile.items() if v is not None},
    }
    save_company_profile(merged)


def next_invoice_number() -> str:
    init_db()
    year = datetime.now().year
    company = get_company_profile()
    invoice_prefix = (company.get("invoice_prefix") or "REF").strip() or "REF"
    prefix = f"{invoice_prefix}-{year}-"
    conn = _get_conn()
    rows = conn.execute(
        "SELECT invoice_number FROM invoice_headers WHERE invoice_number LIKE ? ORDER BY invoice_number DESC",
        (f"{prefix}%",),
    ).fetchall()
    conn.close()

    max_seq = 0
    for row in rows:
        val = row["invoice_number"]
        try:
            seq = int(val.split("-")[-1])
            if seq > max_seq:
                max_seq = seq
        except Exception:
            continue
    return f"{invoice_prefix}-{year}-{max_seq + 1:03d}"


def _calc_totals(
    lines: Sequence[Dict], expenses: Sequence[Dict], iva_rate: float, irpf_rate: float
) -> Dict[str, float]:
    lines_total = sum(float(item["qty"]) * float(item["unit_price"]) for item in lines)
    expenses_total = sum(float(item["amount"]) for item in expenses)
    subtotal = round(lines_total + expenses_total, 2)
    iva = round(subtotal * iva_rate, 2)
    irpf = round(subtotal * irpf_rate, 2)
    total = round(subtotal + iva - irpf, 2)
    return {
        "subtotal": subtotal,
        "iva": iva,
        "irpf": irpf,
        "total": total,
    }


def create_invoice(
    client_id: int,
    invoice_date: str,
    due_date: str,
    payment_method: str,
    lines: Sequence[Dict],
    expenses: Sequence[Dict],
    iva_rate: float = 0.21,
    irpf_rate: float = 0.07,
    notes: str = "",
    status: str = "Pendiente",
) -> Dict:
    init_db()
    if not lines:
        raise ValueError("La factura debe tener al menos una linea.")

    totals = _calc_totals(lines, expenses, iva_rate, irpf_rate)
    invoice_number = next_invoice_number()

    conn = _get_conn()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO invoice_headers(
            invoice_number, invoice_date, due_date, client_id, status,
            payment_method, subtotal, iva, irpf, total, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            invoice_number,
            invoice_date,
            due_date,
            client_id,
            status,
            payment_method,
            totals["subtotal"],
            totals["iva"],
            totals["irpf"],
            totals["total"],
            notes,
        ),
    )
    invoice_id = c.lastrowid

    for item in lines:
        qty = float(item["qty"])
        unit_price = float(item["unit_price"])
        line_total = round(qty * unit_price, 2)
        c.execute(
            """
            INSERT INTO invoice_lines(invoice_id, description, qty, unit_price, total)
            VALUES (?, ?, ?, ?, ?)
            """,
            (invoice_id, item["description"], qty, unit_price, line_total),
        )

    for item in expenses:
        amount = float(item["amount"])
        c.execute(
            """
            INSERT INTO invoice_expenses(invoice_id, description, amount)
            VALUES (?, ?, ?)
            """,
            (invoice_id, item["description"], amount),
        )

    conn.commit()
    conn.close()

    pdf_path = generate_invoice_pdf(int(invoice_id))
    return {
        "invoice_id": int(invoice_id),
        "invoice_number": invoice_number,
        "pdf_path": pdf_path,
        **totals,
    }


def get_invoice(invoice_id: int) -> Optional[Dict]:
    init_db()
    conn = _get_conn()
    header = conn.execute(
        "SELECT * FROM invoice_headers WHERE id = ?", (invoice_id,)
    ).fetchone()
    if not header:
        conn.close()
        return None

    client = conn.execute("SELECT * FROM clients WHERE id = ?", (header["client_id"],)).fetchone()
    lines = conn.execute(
        "SELECT * FROM invoice_lines WHERE invoice_id = ? ORDER BY id", (invoice_id,)
    ).fetchall()
    expenses = conn.execute(
        "SELECT * FROM invoice_expenses WHERE invoice_id = ? ORDER BY id", (invoice_id,)
    ).fetchall()
    conn.close()

    return {
        "header": dict(header),
        "client": dict(client) if client else None,
        "lines": [dict(r) for r in lines],
        "expenses": [dict(r) for r in expenses],
        "company": get_company_profile(),
    }


def list_invoices(limit: int = 100) -> List[Dict]:
    init_db()
    conn = _get_conn()
    rows = conn.execute(
        """
        SELECT h.id, h.invoice_number, h.invoice_date, h.due_date, h.status, h.total,
               c.company_name AS client_name
        FROM invoice_headers h
        LEFT JOIN clients c ON c.id = h.client_id
        ORDER BY h.id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def dashboard_metrics() -> Dict[str, float]:
    init_db()
    today = date.today()
    month_prefix = f"{today.year}-{today.month:02d}"
    conn = _get_conn()
    month_fact = conn.execute(
        "SELECT COALESCE(SUM(total), 0) AS v FROM invoice_headers WHERE invoice_date LIKE ?",
        (f"{month_prefix}%",),
    ).fetchone()["v"]
    pending = conn.execute(
        "SELECT COALESCE(SUM(total), 0) AS v FROM invoice_headers WHERE status = 'Pendiente'"
    ).fetchone()["v"]
    iva_acc = conn.execute(
        "SELECT COALESCE(SUM(iva), 0) AS v FROM invoice_headers WHERE invoice_date LIKE ?",
        (f"{today.year}-%",),
    ).fetchone()["v"]
    active_clients = conn.execute("SELECT COUNT(*) AS c FROM clients").fetchone()["c"]
    invoices_count = conn.execute(
        "SELECT COUNT(*) AS c FROM invoice_headers WHERE invoice_date LIKE ?",
        (f"{today.year}-%",),
    ).fetchone()["c"]
    conn.close()
    return {
        "facturacion_mes": round(float(month_fact), 2),
        "pendiente_cobro": round(float(pending), 2),
        "iva_acumulado": round(float(iva_acc), 2),
        "clientes_activos": int(active_clients),
        "facturas_emitidas": int(invoices_count),
    }


def yearly_reporting(year: int) -> Dict[str, float]:
    init_db()
    conn = _get_conn()
    row = conn.execute(
        """
        SELECT
            COALESCE(SUM(total), 0) AS facturado,
            COALESCE(SUM(iva), 0) AS iva_repercutido,
            COALESCE(SUM(irpf), 0) AS irpf_retenido,
            COALESCE(SUM(CASE WHEN status = 'Pendiente' THEN total ELSE 0 END), 0) AS pendiente
        FROM invoice_headers
        WHERE invoice_date LIKE ?
        """,
        (f"{year}-%",),
    ).fetchone()
    conn.close()
    return {
        "facturado": round(float(row["facturado"]), 2),
        "iva_repercutido": round(float(row["iva_repercutido"]), 2),
        "irpf_retenido": round(float(row["irpf_retenido"]), 2),
        "pendiente_cobro": round(float(row["pendiente"]), 2),
    }


def generate_invoice_pdf(invoice_id: int) -> str:
    data = get_invoice(invoice_id)
    if not data:
        raise ValueError("Factura no encontrada")

    header = data["header"]
    company = data["company"]
    client = data["client"]
    lines = data["lines"]
    expenses = data["expenses"]

    pdf_name = f"{header['invoice_number']}.pdf"
    pdf_path = os.path.join(INVOICE_DIR, pdf_name)

    c = canvas.Canvas(pdf_path, pagesize=A4)
    w, h = A4

    # Cabecera emisor
    c.setFillColor(colors.HexColor("#0F172A"))
    c.rect(20 * mm, h - 45 * mm, 80 * mm, 30 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(24 * mm, h - 24 * mm, company.get("fiscal_name") or "Empresa")
    c.setFont("Helvetica", 9)
    c.drawString(24 * mm, h - 30 * mm, f"NIF: {company.get('nif', '')}")
    c.drawString(24 * mm, h - 35 * mm, company.get("address", ""))
    city_line = " ".join([company.get("postal_code", ""), company.get("city", "")]).strip()
    c.drawString(24 * mm, h - 40 * mm, city_line)
    c.drawString(24 * mm, h - 45 * mm, f"Tel: {company.get('phone', '')}  Email: {company.get('email', '')}")

    # Titulo factura
    c.setFillColor(colors.HexColor("#111827"))
    c.setFont("Helvetica-Bold", 20)
    c.drawRightString(w - 20 * mm, h - 25 * mm, f"FACTURA {header['invoice_number']}")
    c.setFont("Helvetica", 10)
    c.drawRightString(w - 20 * mm, h - 32 * mm, f"Fecha: {header['invoice_date']}")
    c.drawRightString(w - 20 * mm, h - 38 * mm, f"Vencimiento: {header['due_date']}")

    # Cliente
    c.setStrokeColor(colors.HexColor("#D1D5DB"))
    c.roundRect(20 * mm, h - 80 * mm, 170 * mm, 25 * mm, 3 * mm, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(24 * mm, h - 64 * mm, "CLIENTE")
    c.setFont("Helvetica", 9)
    c.drawString(24 * mm, h - 70 * mm, client.get("company_name", ""))
    c.drawString(24 * mm, h - 75 * mm, f"NIF: {client.get('nif', '')}")
    client_addr = " | ".join(
        p for p in [client.get("address", ""), client.get("city", ""), client.get("postal_code", "")] if p
    )
    c.drawString(90 * mm, h - 75 * mm, client_addr[:70])

    y = h - 95 * mm

    # Tabla conceptos
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#1F2937"))
    c.rect(20 * mm, y, 170 * mm, 8 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.drawString(23 * mm, y + 2.5 * mm, "Descripcion")
    c.drawString(120 * mm, y + 2.5 * mm, "Cant.")
    c.drawString(138 * mm, y + 2.5 * mm, "Precio")
    c.drawString(168 * mm, y + 2.5 * mm, "Total")

    y -= 7 * mm
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    for line in lines:
        y -= 6 * mm
        c.drawString(23 * mm, y, str(line.get("description", ""))[:55])
        c.drawRightString(132 * mm, y, f"{line.get('qty', 0):.2f}")
        c.drawRightString(160 * mm, y, f"{line.get('unit_price', 0):.2f} EUR")
        c.drawRightString(188 * mm, y, f"{line.get('total', 0):.2f} EUR")

    if expenses:
        y -= 9 * mm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(23 * mm, y, "Gastos")
        c.setFont("Helvetica", 9)
        for expense in expenses:
            y -= 6 * mm
            c.drawString(23 * mm, y, str(expense.get("description", ""))[:55])
            c.drawRightString(188 * mm, y, f"{expense.get('amount', 0):.2f} EUR")

    # Resumen
    y -= 12 * mm
    c.setStrokeColor(colors.HexColor("#D1D5DB"))
    c.roundRect(120 * mm, y - 22 * mm, 70 * mm, 24 * mm, 2 * mm, stroke=1, fill=0)
    c.setFont("Helvetica", 9)
    c.drawString(124 * mm, y - 2 * mm, "Base imponible")
    c.drawRightString(186 * mm, y - 2 * mm, f"{header['subtotal']:.2f} EUR")
    c.drawString(124 * mm, y - 8 * mm, "IVA")
    c.drawRightString(186 * mm, y - 8 * mm, f"{header['iva']:.2f} EUR")
    c.drawString(124 * mm, y - 14 * mm, "IRPF")
    c.drawRightString(186 * mm, y - 14 * mm, f"-{header['irpf']:.2f} EUR")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(124 * mm, y - 20 * mm, "TOTAL")
    c.drawRightString(186 * mm, y - 20 * mm, f"{header['total']:.2f} EUR")

    # Pie legal
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, 25 * mm, "Forma de pago: Transferencia bancaria")
    c.drawString(20 * mm, 20 * mm, f"IBAN: {company.get('iban', '')}")
    c.drawString(20 * mm, 15 * mm, f"Vencimiento: {header.get('due_date', '')}")

    c.save()
    return pdf_path


if __name__ == "__main__":
    init_db()
