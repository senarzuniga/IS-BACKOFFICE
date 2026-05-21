"""AI conversational agent for plant configuration.

Works with OpenAI GPT-4o when an API key is available,
falls back to a deterministic guided wizard otherwise.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    ConverterLine,
    CorrugatorConfig,
    MachineType,
    PlantConfig,
    PlantType,
    ShiftConfig,
    StorageConfig,
    TransportConfig,
    TransportType,
)

# ---------------------------------------------------------------------------
# Conversation step definitions
# ---------------------------------------------------------------------------

STEPS = [
    {
        "id": "plant_type",
        "question": "¿Qué tipo de planta quieres simular?",
        "type": "select",
        "options": [
            ("corrugator_converter", "🏭 Corrugadora + Conversión (planta completa)"),
            ("corrugator_only", "📦 Solo Corrugadora"),
            ("converter_only", "✂️ Solo Conversión"),
        ],
        "key": "plant_type",
        "always": True,
    },
    {
        "id": "plant_name",
        "question": "¿Cómo quieres llamar a esta simulación?",
        "type": "text",
        "default": "Mi Planta Corrugado",
        "key": "plant_name",
        "always": True,
    },
    # --- Corrugator branch ---
    {
        "id": "corrug_speed",
        "question": "Velocidad de producción de la corrugadora (m/min):",
        "type": "number",
        "min": 50, "max": 500, "default": 250, "step": 10,
        "key": "corrug_speed",
        "requires": ["corrugator_converter", "corrugator_only"],
        "unit": "m/min",
    },
    {
        "id": "corrug_width",
        "question": "Ancho útil de la corrugadora (mm):",
        "type": "select",
        "options": [
            (1800, "1800 mm — pequeña"),
            (2200, "2200 mm — media"),
            (2500, "2500 mm — estándar europea"),
            (2800, "2800 mm — alta capacidad"),
        ],
        "default": 2500,
        "key": "corrug_width",
        "requires": ["corrugator_converter", "corrugator_only"],
    },
    {
        "id": "roll_store",
        "question": "Capacidad del almacén de bobinas (nº de bobinas):",
        "type": "number",
        "min": 20, "max": 500, "default": 100, "step": 10,
        "key": "roll_store_capacity",
        "requires": ["corrugator_converter", "corrugator_only"],
        "unit": "bobinas",
    },
    # --- Converter branch ---
    {
        "id": "num_converters",
        "question": "¿Cuántas líneas de conversión tiene la planta?",
        "type": "number",
        "min": 1, "max": 8, "default": 2, "step": 1,
        "key": "num_converters",
        "requires": ["corrugator_converter", "converter_only"],
        "unit": "líneas",
    },
    {
        "id": "converter_type",
        "question": "Tipo de máquina predominante en conversión:",
        "type": "select",
        "options": [
            ("flexografica", "🖨️ Flexográfica (cajas estándar, RSC)"),
            ("troqueladora", "✂️ Troqueladora (cajas especiales, displays)"),
            ("rotativa", "⚙️ Rotativa (altos volúmenes, RSC)"),
            ("mixed", "🔀 Mixta (flexo + troquel)"),
        ],
        "key": "converter_type",
        "requires": ["corrugator_converter", "converter_only"],
    },
    {
        "id": "converter_speed",
        "question": "Velocidad media de las convertidoras (uds/hora):",
        "type": "number",
        "min": 200, "max": 3000, "default": 1000, "step": 50,
        "key": "converter_speed",
        "requires": ["corrugator_converter", "converter_only"],
        "unit": "uds/hora",
    },
    # --- Transport ---
    {
        "id": "transport_type",
        "question": "¿Cómo se transporta el material entre zonas?",
        "type": "select",
        "options": [
            ("carretillas", "🚛 Carretillas manuales"),
            ("tracks", "🔀 Tracks guiados automáticos"),
            ("conveyors", "➡️ Conveyors automáticos"),
            ("mixed", "🔀 Sistema mixto"),
        ],
        "key": "transport_type",
        "always": True,
    },
    {
        "id": "num_forklifts",
        "question": "Número de carretillas / vehículos de transporte:",
        "type": "number",
        "min": 1, "max": 10, "default": 3, "step": 1,
        "key": "num_forklifts",
        "always": True,
        "unit": "unidades",
    },
    # --- Storage ---
    {
        "id": "buffer_capacity",
        "question": "Capacidad del almacén intermedio (palets de plano):",
        "type": "number",
        "min": 20, "max": 500, "default": 150, "step": 10,
        "key": "buffer_capacity",
        "requires": ["corrugator_converter", "converter_only"],
        "unit": "palets",
    },
    # --- Simulation params ---
    {
        "id": "sim_duration",
        "question": "Duración de la simulación:",
        "type": "select",
        "options": [
            (4, "4 horas (medio turno)"),
            (8, "8 horas (1 turno)"),
            (16, "16 horas (2 turnos)"),
            (24, "24 horas (3 turnos)"),
        ],
        "default": 8,
        "key": "sim_duration",
        "always": True,
        "unit": "horas",
    },
    {
        "id": "sim_speed",
        "question": "Velocidad de simulación (segundos simulados por segundo real):",
        "type": "select",
        "options": [
            (1, "1x — Tiempo real (demo técnica)"),
            (5, "5x — Acelerado (presentación cliente)"),
            (10, "10x — Rápido (análisis rápido)"),
            (30, "30x — Muy rápido (evaluación paramétrica)"),
        ],
        "default": 10,
        "key": "sim_speed",
        "always": True,
    },
]


# ---------------------------------------------------------------------------
# ConfigAgent
# ---------------------------------------------------------------------------

class ConfigAgent:
    """
    Guided conversational agent for building a PlantConfig.

    Usage:
        agent = ConfigAgent()
        for step in agent.get_visible_steps(answers):
            # render step in UI and capture answer
        config = agent.build_config(answers)
    """

    def __init__(self) -> None:
        self._openai_available = bool(os.getenv("OPENAI_API_KEY"))

    # ------------------------------------------------------------------ #
    # Step management                                                       #
    # ------------------------------------------------------------------ #

    def get_visible_steps(self, answers: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return steps that should be shown given current answers."""
        plant_type = answers.get("plant_type", "corrugator_converter")
        visible = []
        for step in STEPS:
            if step.get("always"):
                visible.append(step)
            elif "requires" in step and plant_type in step["requires"]:
                visible.append(step)
        return visible

    def step_count(self, answers: Dict[str, Any]) -> int:
        return len(self.get_visible_steps(answers))

    # ------------------------------------------------------------------ #
    # AI hint generation (OpenAI if available, else rule-based)            #
    # ------------------------------------------------------------------ #

    def get_hint(self, step_id: str, answers: Dict[str, Any]) -> Optional[str]:
        """Return a contextual hint for the current step."""
        hints = {
            "corrug_speed": (
                "💡 Las corrugadoras modernas europeas operan entre 200-300 m/min en producción estable. "
                "A mayor velocidad, mayor exigencia de almacén de bobinas y gestión de plano."
            ),
            "num_converters": (
                "💡 Regla de oro: una corrugadora a 250 m/min produce ~15,000 m²/hora. "
                "Si tus convertidoras procesan ~5,000 m²/h c/u, necesitas mínimo 3 para equilibrar el flujo."
            ),
            "buffer_capacity": (
                "💡 El buffer óptimo absorbe ~2 horas de producción de la corrugadora. "
                "Demasiado pequeño = corrugadora bloqueada. Demasiado grande = caída FIFO y scrap por humedad."
            ),
            "transport_type": (
                "💡 Para plantas >100,000 m²/día, los tracks guiados reducen el coste de transporte interno "
                "en un 40% vs carretillas y eliminan incidentes de seguridad."
            ),
            "num_forklifts": (
                "💡 Cálculo estándar: 1 carretilla por cada 2 líneas de conversión, más 1 para expedición. "
                "Ejemplo: 3 convertidoras = 2 carretillas mínimo."
            ),
        }
        return hints.get(step_id)

    def get_ai_recommendation(self, answers: Dict[str, Any]) -> str:
        """
        Generate a smart recommendation based on current answers.
        Uses OpenAI if available, else rule-based.
        """
        if self._openai_available:
            try:
                return self._openai_recommendation(answers)
            except Exception:
                pass
        return self._rule_based_recommendation(answers)

    def _rule_based_recommendation(self, answers: Dict[str, Any]) -> str:
        """Deterministic recommendation logic."""
        issues: List[str] = []
        suggestions: List[str] = []

        plant_type = answers.get("plant_type", "corrugator_converter")
        corrug_speed = answers.get("corrug_speed", 250)
        num_conv = answers.get("num_converters", 2)
        conv_speed = answers.get("converter_speed", 1000)
        buffer = answers.get("buffer_capacity", 150)
        num_flt = answers.get("num_forklifts", 3)
        transport = answers.get("transport_type", "carretillas")
        corrug_width = answers.get("corrug_width", 2500)

        # Flow balance check
        if plant_type in ("corrugator_converter", "corrugator_only"):
            m2_corrug_h = corrug_speed * 60 * (corrug_width / 1000)
            m2_conv_h = num_conv * conv_speed * 0.35  # ~0.35 m² per unit avg
            ratio = m2_corrug_h / max(m2_conv_h, 1)
            if ratio > 1.3:
                issues.append(
                    f"⚠️ **Desbalance de flujo detectado**: La corrugadora produce ~{m2_corrug_h:,.0f} m²/h "
                    f"pero las {num_conv} convertidoras solo absorben ~{m2_conv_h:,.0f} m²/h "
                    f"({ratio:.1f}x). El buffer se llenará en pocas horas."
                )
                suggestions.append(
                    f"➕ Añadir {int(ratio - 1)} convertidoras adicionales, o reducir velocidad de corrugadora "
                    f"al {100/ratio:.0f}% ({corrug_speed/ratio:.0f} m/min)."
                )
            elif ratio < 0.8:
                issues.append(
                    f"⚠️ **Corrugadora como cuello de botella**: Las convertidoras necesitan "
                    f"~{m2_conv_h:,.0f} m²/h pero la corrugadora solo produce {m2_corrug_h:,.0f} m²/h."
                )
                suggestions.append(
                    "⚡ Considerar aumentar velocidad de corrugadora o añadir turno extra de corrugación."
                )

        # Buffer size check
        if plant_type in ("corrugator_converter",) and plant_type != "corrugator_only":
            buffer_hours = buffer / max(num_conv * 15, 1)  # ~15 palets/hora/convertidora
            if buffer_hours < 1.0:
                issues.append(
                    f"⚠️ **Buffer pequeño**: Con {buffer} palets y {num_conv} convertidoras, "
                    f"el buffer solo aguanta ~{buffer_hours*60:.0f} min de producción."
                )
                suggestions.append(f"📦 Ampliar buffer a mínimo {num_conv * 20} palets para absorber micro-paradas.")

        # Transport check
        min_flt = max(2, num_conv // 2 + 1)
        if num_flt < min_flt and transport == "carretillas":
            issues.append(
                f"⚠️ **Transporte insuficiente**: Con {num_conv} convertidoras necesitas al menos "
                f"{min_flt} carretillas para evitar esperas."
            )
            suggestions.append(f"🚛 Añadir {min_flt - num_flt} carretilla(s) adicional(es).")

        if not issues:
            return (
                "✅ **Configuración equilibrada.** Los parámetros introducidos muestran un flujo "
                "coherente. La simulación calculará los KPIs exactos y detectará micro-cuellos de botella."
            )

        text = "### Análisis previo a la simulación\n\n"
        text += "\n\n".join(issues)
        if suggestions:
            text += "\n\n**Sugerencias de optimización:**\n" + "\n".join(suggestions)
        return text

    def _openai_recommendation(self, answers: Dict[str, Any]) -> str:
        """Use OpenAI to generate a richer recommendation."""
        import openai

        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        prompt = (
            "Eres un experto en plantas de cartón corrugado. Analiza esta configuración de planta "
            "y da 2-3 observaciones concretas sobre posibles cuellos de botella y mejoras:\n\n"
            f"{answers}\n\n"
            "Responde en español, de forma concisa (máximo 150 palabras). "
            "Usa emojis para los puntos clave."
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.3,
        )
        return resp.choices[0].message.content or ""

    # ------------------------------------------------------------------ #
    # Config building                                                       #
    # ------------------------------------------------------------------ #

    def build_config(self, answers: Dict[str, Any]) -> PlantConfig:
        """Convert a flat answers dict into a structured PlantConfig."""
        plant_type = PlantType(answers.get("plant_type", "corrugator_converter"))

        # Corrugator
        corrugator = None
        if plant_type in (PlantType.CORRUGATOR_CONVERTER, PlantType.CORRUGATOR_ONLY):
            corrugator = CorrugatorConfig(
                speed_m_min=float(answers.get("corrug_speed", 250)),
                width_mm=int(answers.get("corrug_width", 2500)),
                roll_store_capacity=int(answers.get("roll_store_capacity", 100)),
            )

        # Converters
        converters: List[ConverterLine] = []
        if plant_type in (PlantType.CORRUGATOR_CONVERTER, PlantType.CONVERTER_ONLY):
            n = int(answers.get("num_converters", 2))
            conv_type_raw = answers.get("converter_type", "flexografica")
            speed = int(answers.get("converter_speed", 1000))
            for i in range(n):
                # Alternate types for mixed
                if conv_type_raw == "mixed":
                    ct = MachineType.FLEXO if i % 2 == 0 else MachineType.DIE_CUTTER
                else:
                    try:
                        ct = MachineType(conv_type_raw)
                    except ValueError:
                        ct = MachineType.FLEXO
                converters.append(
                    ConverterLine(
                        id=f"C{i+1}",
                        machine_type=ct,
                        speed_units_per_hour=speed,
                        availability=0.90 + (i % 3) * 0.01,
                    )
                )

        # Transport
        try:
            tt = TransportType(answers.get("transport_type", "carretillas"))
        except ValueError:
            tt = TransportType.FORKLIFTS
        transport = TransportConfig(
            type=tt,
            num_forklifts=int(answers.get("num_forklifts", 3)),
        )

        # Storage
        storage = StorageConfig(
            buffer_capacity_pallets=int(answers.get("buffer_capacity", 150)),
        )

        return PlantConfig(
            name=answers.get("plant_name", "Mi Planta"),
            plant_type=plant_type,
            corrugator=corrugator,
            converters=converters,
            transport=transport,
            storage=storage,
            simulation_duration_hours=float(answers.get("sim_duration", 8)),
            simulation_speed=float(answers.get("sim_speed", 10)),
        )

    # ------------------------------------------------------------------ #
    # Pre-built scenarios (demo / quick start)                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def demo_scenarios() -> List[Tuple[str, Dict[str, Any]]]:
        """Return a list of (label, answers_dict) for quick-start demos."""
        return [
            (
                "🏭 Planta grande — 3 convertidoras (corrugadora+conversión)",
                {
                    "plant_name": "Planta Ref. Grande",
                    "plant_type": "corrugator_converter",
                    "corrug_speed": 280,
                    "corrug_width": 2500,
                    "roll_store_capacity": 120,
                    "num_converters": 3,
                    "converter_type": "mixed",
                    "converter_speed": 1000,
                    "transport_type": "carretillas",
                    "num_forklifts": 4,
                    "buffer_capacity": 200,
                    "sim_duration": 8,
                    "sim_speed": 10,
                },
            ),
            (
                "✂️ Planta mediana — 2 convertidoras (solo conversión)",
                {
                    "plant_name": "Planta Conversión Mediana",
                    "plant_type": "converter_only",
                    "num_converters": 2,
                    "converter_type": "flexografica",
                    "converter_speed": 900,
                    "transport_type": "carretillas",
                    "num_forklifts": 2,
                    "buffer_capacity": 100,
                    "sim_duration": 8,
                    "sim_speed": 10,
                },
            ),
            (
                "📦 Corrugadora sola — análisis cuello de botella plano",
                {
                    "plant_name": "Corrugadora Solo",
                    "plant_type": "corrugator_only",
                    "corrug_speed": 300,
                    "corrug_width": 2500,
                    "roll_store_capacity": 80,
                    "transport_type": "tracks",
                    "num_forklifts": 2,
                    "sim_duration": 8,
                    "sim_speed": 10,
                },
            ),
            (
                "⚡ Escenario optimizado — tracks + 4 convertidoras",
                {
                    "plant_name": "Planta Optimizada Tracks",
                    "plant_type": "corrugator_converter",
                    "corrug_speed": 300,
                    "corrug_width": 2500,
                    "roll_store_capacity": 150,
                    "num_converters": 4,
                    "converter_type": "flexografica",
                    "converter_speed": 1100,
                    "transport_type": "tracks",
                    "num_forklifts": 2,
                    "buffer_capacity": 250,
                    "sim_duration": 8,
                    "sim_speed": 10,
                },
            ),
        ]
