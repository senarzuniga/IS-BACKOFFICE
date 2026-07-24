from __future__ import annotations

from typing import List

from .models import ProductTemplate


def load_product_catalog() -> List[ProductTemplate]:
    return [
        ProductTemplate(
            key="sr1400",
            display_name="SR-1400 Scrap Management",
            status="operational",
            description="Fully implemented proportional offer template package.",
        ),
        ProductTemplate(
            key="ingetrans",
            display_name="INGETRANS",
            status="prepared",
            description="Template package scaffold prepared for next mission.",
        ),
        ProductTemplate(
            key="amr_intralogistics",
            display_name="AMR Intralogistics",
            status="prepared",
            description="Template package scaffold prepared for next mission.",
        ),
        ProductTemplate(
            key="amr_wip",
            display_name="AMR WIP Management",
            status="prepared",
            description="Template package scaffold prepared for next mission.",
        ),
        ProductTemplate(
            key="plug_play_palletizer",
            display_name="Plug & Play Palletizer",
            status="prepared",
            description="Template package scaffold prepared for next mission.",
        ),
        ProductTemplate(
            key="heavy_duty_palletizer",
            display_name="Heavy Duty Palletizer",
            status="prepared",
            description="Template package scaffold prepared for next mission.",
        ),
    ]
