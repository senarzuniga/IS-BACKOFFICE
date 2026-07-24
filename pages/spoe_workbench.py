from __future__ import annotations

from datetime import date
from pathlib import Path

import streamlit as st

from backoffice.spoe import (
    OfferInput,
    build_knowledge_package,
    calculate_sr1400_bom,
    evaluate_architecture_alternatives,
    generate_offer_documents,
    load_product_catalog,
    persist_offer_record,
    run_ame_iteration,
    supervise_offer_quality,
    update_governance_artifacts,
)


def _safe_paths(uploaded_files):
    saved = []
    out_dir = Path("reports/spoe/uploads")
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in uploaded_files or []:
        p = out_dir / f.name
        p.write_bytes(f.getbuffer())
        saved.append(str(p))
    return saved


def main():
    st.set_page_config(page_title="SPOE Workbench", page_icon="🧩", layout="wide")
    st.title("STANDARD PRODUCT OFFER ENGINE (SPOE)")
    st.caption("Commercial Engineering Workbench | Integrated into current platform baseline")

    catalog = load_product_catalog()
    selected = st.selectbox(
        "Product Selection",
        options=[p.display_name for p in catalog],
        index=0,
    )

    selected_template = next(p for p in catalog if p.display_name == selected)
    st.info(f"Template status: {selected_template.status}")
    if selected_template.key != "sr1400":
        st.warning("Prepared template package only. Implementation intentionally deferred to next missions.")

    left, right = st.columns(2)
    with left:
        st.subheader("Customer Information")
        customer = st.text_input("Customer")
        plant = st.text_input("Plant")
        country = st.text_input("Country")
        language = st.selectbox("Language", ["es", "en"], index=0)
        offer_number = st.text_input("Offer Number", value="OFF-2026-SR1400-001")
        offer_date = st.date_input("Offer Date", value=date.today())

        st.subheader("Project Information")
        project_name = st.text_input("Project Name")
        line_length = st.number_input("Total Main Line Length (m)", min_value=0.0, value=100.0, step=1.0)
        turns_90 = st.number_input("Number of 90° turns", min_value=0, value=4, step=1)
        ramps_count = st.number_input("Number of ramps", min_value=0, value=2, step=1)
        ramp_lengths_raw = st.text_input("Ramp lengths (comma separated meters)", value="8, 10")

    with right:
        st.subheader("Engineering Configuration")
        additional_notes = st.text_area("Additional Notes", height=80)
        technical_notes = st.text_area("Technical Notes", height=100)
        commercial_notes = st.text_area("Commercial Notes", height=100)

        st.subheader("Layout Upload")
        layout_image = st.file_uploader("Layout Image", type=["png", "jpg", "jpeg", "webp"])
        attachments = st.file_uploader(
            "Optional Attachments",
            accept_multiple_files=True,
            type=["png", "jpg", "jpeg", "webp", "pdf", "docx", "xlsx"],
        )
        st.subheader("Video Integration")
        local_video = Path("assets/videos/hotspots/sr1400/demo.mp4")
        if local_video.exists():
            st.video(str(local_video))
            st.caption("Official SR1400 product video loaded from platform assets.")
        else:
            st.info("Official SR1400 video reference available at INGECART website.")
            st.link_button("Open Official SR1400 Video/Page", "https://www.ingecart.eu/sistemaretal1400")

    st.markdown("---")
    st.subheader("Mission Manager")
    if st.button("Run Autonomous Engineering Iteration"):
        iteration = run_ame_iteration()
        governance = update_governance_artifacts(iteration)
        st.success("AME iteration executed and governance artifacts updated.")
        st.json(iteration)
        st.json(governance)

    if st.button("Generate Offer Package", type="primary"):
        try:
            ramp_lengths = [float(x.strip()) for x in ramp_lengths_raw.split(",") if x.strip()]
            layout_path = _safe_paths([layout_image])[0] if layout_image else ""
            attachment_paths = _safe_paths(attachments)

            offer = OfferInput(
                customer=customer,
                plant=plant,
                country=country,
                language=language,
                offer_number=offer_number,
                offer_date=offer_date,
                project_name=project_name,
                total_main_line_length_m=float(line_length),
                turns_90=int(turns_90),
                ramps_count=int(ramps_count),
                ramp_lengths_m=ramp_lengths,
                additional_notes=additional_notes,
                commercial_notes=commercial_notes,
                technical_notes=technical_notes,
                layout_image_path=layout_path,
                optional_attachment_paths=attachment_paths,
            )

            bom = calculate_sr1400_bom(offer)
            knowledge = build_knowledge_package(offer)
            generated_docs = generate_offer_documents(offer, bom, knowledge)
            quality = supervise_offer_quality(offer, bom, list(generated_docs.keys()))
            reuse_score = min(100.0, 60.0 + (len(bom) * 2.5))
            kh_path = persist_offer_record(offer, bom, generated_docs, quality, reuse_score)

            st.success(f"Offer generated. Executive Quality Score: {quality.quality_score}")

            st.subheader("Live BOM")
            st.json(bom)

            live_cost = sum(v * 145.0 for v in bom.values())
            st.subheader("Live Cost")
            st.metric("Estimated Cost", f"{live_cost:,.2f}")

            st.subheader("AI Recommendations")
            if quality.suggestions:
                for rec in quality.suggestions:
                    st.write(f"- {rec}")
            else:
                st.write("No recommendations. Offer is complete.")

            st.subheader("Document Generation")
            st.json(generated_docs)

            st.subheader("Knowledge")
            st.write(f"Knowledge Hub record: {kh_path}")

            st.subheader("Offer History")
            hist = Path("knowledge_hub/spoe/offers_history.jsonl")
            if hist.exists():
                lines = hist.read_text(encoding="utf-8").splitlines()[-5:]
                st.code("\n".join(lines), language="json")

            st.subheader("Architecture Alternatives")
            arch = evaluate_architecture_alternatives()
            st.json(arch)

            st.subheader("Live Preview")
            summary_lang = knowledge["executive"]["es"] if language == "es" else knowledge["executive"]["en"]
            st.write(summary_lang)
        except Exception as e:
            st.error(f"Failed to generate offer: {e}")


if __name__ == "__main__":
    main()
