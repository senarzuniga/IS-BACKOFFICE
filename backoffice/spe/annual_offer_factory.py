from __future__ import annotations

from datetime import date

from backoffice.analytics.ingecart_monitoring import load_monitoring_blueprint

from .models import Proposal, ServiceItem


def build_smart_plant_annual_proposals(target_date: date | None = None) -> list[Proposal]:
    blueprint = load_monitoring_blueprint()
    proposals: list[Proposal] = []
    base_date = target_date or date.today()

    for site in blueprint["sites"]:
        equipment = site["equipment"]
        equipment_lines = [f"- {item['name']} ({item['id']})" for item in equipment]
        monthly_contract = sum(float(item["monthly_contract_eur"]) for item in equipment)
        annual_maintenance = round(monthly_contract * 12.0 * 1.18, 0)
        ingpro_annual = round(max(18000.0, len(equipment) * 3200.0), 0)
        training_ai_annual = round(9200.0 + (len(equipment) * 650.0), 0)
        spares_channel_fee = round(sum(float(item["recommended_spares_eur"]) for item in equipment) * 0.22, 0)
        total_annual = annual_maintenance + ingpro_annual + training_ai_annual + spares_channel_fee

        preventive_service = ServiceItem(
            service_id="preventive_maintenance",
            name="Programa Anual de Mantenimiento Preventivo",
            description=(
                "Cobertura preventiva por activo con inspección mecánica, eléctrica y de automatización. "
                "Incluye planificación anual, ventanas de parada y reporte técnico por visita."
            ),
            price=annual_maintenance,
            unit="year",
            frequency="4 visitas presenciales + seguimiento mensual remoto",
            persons=2,
            coverage=f"Todos los equipos de {site['name']}",
            deliverables="Plan maestro PM, checklist digital, backlog priorizado y reporte ejecutivo trimestral",
            spare_parts="Recomendación dinámica de stock crítico por riesgo y consumo",
            emergency_response="SLA 24/7 con escalado prioritario",
            enabled=True,
            optional=False,
        )
        ingpro_service = ServiceItem(
            service_id="ingpro",
            name="INGEPRO Monitoring + Predictibilidad AI",
            description=(
                "Monitorización continua de señales críticas, detección de anomalías, priorización automática "
                "de intervenciones y tableros por rol (Operarios, Mantenimiento y Management)."
            ),
            price=ingpro_annual,
            unit="year",
            frequency="24/7 continuo",
            persons=1,
            coverage="Alerting, analítica predictiva, recomendaciones y seguimiento de OEE/LPI",
            deliverables="Panel por rol, informe mensual, comité trimestral de mejora y roadmap de fiabilidad",
            enabled=True,
            optional=False,
        )
        training_service = ServiceItem(
            service_id="training",
            name="Training Operativo + Mantenimiento + Management",
            description=(
                "Formación en operación basada en datos, mantenimiento guiado por AI, gestión de alarmas y "
                "adopción del modelo predictivo en equipos de planta."
            ),
            price=training_ai_annual,
            unit="year",
            frequency="12 sesiones/año (onsite y remoto)",
            persons=3,
            coverage="Operarios, técnicos de mantenimiento y responsables de planta",
            deliverables="Playbooks por rol, simulaciones de fallo y plan de habilidades",
            enabled=True,
            optional=False,
        )
        channel_service = ServiceItem(
            service_id="spare_parts_review",
            name="Canal INGEPRO de Compras Industriales al por Mayor",
            description=(
                "Canal de solicitud directa de recambios y piezas para cualquier tipo de máquina, con gestión "
                "integrada de homologación, trazabilidad y optimización de plazo/precio."
            ),
            price=spares_channel_fee,
            unit="year",
            frequency="Servicio continuo de aprovisionamiento",
            coverage="Recambios multi-OEM con benchmark de coste/plazo tipo Tetrace",
            deliverables="Portal de pedidos, matriz de criticidad, seguimiento de lead-time y ahorros",
            enabled=True,
            optional=False,
        )

        proposal = Proposal(
            title=f"Oferta anual recomendada de mantenimiento + INGEPRO · {site['name']}",
            customer=site["name"],
            plant=f"{site['name']} ({site['country']})",
            customer_country=site["country"],
            language="es",
            currency="EUR",
            responsible="INGECART Engineering",
            project="Smart Plant Annual Maintenance Programme",
            duration="12 meses",
            validity_days=45,
            payment_terms="Facturación mensual prorrateada. Revisión semestral de alcance por criticidad.",
            date_created=base_date.isoformat(),
            services=[preventive_service, ingpro_service, training_service, channel_service],
            executive_summary=(
                f"<p>Esta propuesta anual para <strong>{site['name']}</strong> consolida mantenimiento preventivo, "
                "monitorización INGEPRO y adopción de AI predictiva para asegurar disponibilidad y continuidad "
                "operativa de los activos críticos definidos en Smart Plant Dashboard.</p>"
                f"<p>Inversión anual recomendada: <strong>EUR {total_annual:,.0f}</strong>.</p>"
            ),
            maintenance_programme=(
                "<p><strong>Programa de mantenimiento por parque instalado</strong></p>"
                + "".join(f"<p>{line}</p>" for line in equipment_lines)
                + "<p>Frecuencias: inspección semanal de condición, revisión mensual de backlog, "
                "paradas trimestrales planificadas y auditoría anual de confiabilidad.</p>"
            ),
            ingpro_section=(
                "<p>INGEPRO habilita monitorización 24/7, alertas por criticidad y recomendaciones "
                "predictivas para Operarios, Mantenimiento y Management con playbooks accionables por rol.</p>"
                "<p>Incluye entrenamiento en AI aplicada a planta, detección anticipada de fallos y "
                "gobierno de datos para decisiones de intervención y mejora.</p>"
            ),
            deliverables=(
                "<ul>"
                "<li>Panel operativo por rol con KPIs de disponibilidad, OEE, riesgo y cumplimiento PM.</li>"
                "<li>Informe técnico mensual + revisión ejecutiva trimestral.</li>"
                "<li>Lista priorizada de mejoras, repuestos y acciones de reducción de parada.</li>"
                "</ul>"
            ),
            optional_services=(
                "<p>Servicios ampliables: upgrades de automatización, ampliación de sensores y extensión "
                "multi-planta con benchmarking cruzado.</p>"
            ),
            commercial_conditions=(
                "<p>El canal INGEPRO incorpora solicitud directa de recambios y piezas de cualquier equipo, "
                "con negociación de volumen y trazabilidad de suministro para mejorar plazo y precio.</p>"
                "<p>Referencia funcional de servicio equivalente: https://www.tetrace.com/en/spare-parts.</p>"
            ),
            pricing_summary=(
                f"<p>Preventivo: EUR {annual_maintenance:,.0f} / año<br>"
                f"INGEPRO monitorización: EUR {ingpro_annual:,.0f} / año<br>"
                f"Training + AI: EUR {training_ai_annual:,.0f} / año<br>"
                f"Canal compras industriales: EUR {spares_channel_fee:,.0f} / año<br>"
                f"<strong>Total recomendado: EUR {total_annual:,.0f} / año</strong></p>"
            ),
            why_ingecart=(
                "<p>INGECART integra ingeniería de mantenimiento, monitorización industrial y ejecución de "
                "suministro en un único contrato orientado a disponibilidad real y reducción de riesgo.</p>"
            ),
            acceptance=(
                "<p>Esta propuesta puede activarse por planta con arranque en menos de 30 días desde aprobación.</p>"
            ),
            tags=["smart_plant_dashboard", "annual_maintenance", f"site_{site['id']}"],
            template_id="SPE-INGECART-SMART-PLANT-ANNUAL-V1",
            authors=["INGECART Engineering"],
        )
        proposals.append(proposal)
    return proposals
