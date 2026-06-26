# 00_FIDELITY_FRAMEWORK

Propósito: Definir de forma explícita las decisiones de fidelidad y normas del framework para el "Reel Loading Simulator V4" (instancia independiente y paralela de la V3).

Entradas: Prompt maestro, especificación de planta (Plant Geometry & Layout), parámetros de V3 que se reutilizan (barra lateral de configuración), requisitos de stakeholder.

Salidas: Documento de fidelidad definitivo que autoriza la generación de la estructura del simulador (FASE 1+).

Configuración: Sistema métrico decimal (m, kg, s). Internamente los YAML usarán el punto decimal (.) para evitar problemas de parsing; la presentación puede formatearse con coma decimal para reporting en formato europeo.

Dependencias: Ninguna (FASE 0 es prerequisito de todas las demás fases).

Validación: Revisión por el equipo de simulación + comprobación automática de unidades y límites en los YAML generados.

KPIs afectados: Exactitud temporal, coherencia de inventarios, reproducibilidad de escenarios.

Riesgo: Decisiones de fidelidad incompletas causan retrabajo extensivo en fases posteriores.

Prioridad: Alta

## FASE 0 – FIDELITY & FRAMEWORK DEFINITION (RESPUESTAS EXPLÍCITAS)

### 1. Nivel de detalle de la simulación
- ¿Cada reel es una entidad individual? → **SÍ** (cada `Reel` tiene ID, dimensiones, masa, estado y trazabilidad histórica).
- ¿Cada movimiento se simula segundo a segundo? → **SÍ (tick = 1s)**. El motor usa ticks de 1s; entre ticks se procesan eventos discretos.
- ¿Cada orden de fabricación genera consumo real de papel? → **SÍ** (consumo modelado por longitud en m × gramaje → masa consumida).
- ¿Cada cambio de bobina dispara eventos logísticos? → **SÍ** (evento `ReelChange` que lanza asignación/transferencias).

Notas: El tick de 1s permite balance entre precisión y coste computacional; eventos de alta frecuencia agregan a nivel subsegundo por estadísticos cuando haga falta (modelado estocástico en Motor de Eventos Aleatorios).

### 2. Clasificación: Entidades vs Parámetros

Entidades dinámicas (clases con estado):
- `Reel`, `Forklift`, `Transfer`, `Track`, `RollStand`, `Corrugator`, `ProductionOrder`, `Warehouse`, `Operator`, `MaintenanceCrew`, `AGV` (preparado), `ReelLifter`, `StretchWrapper`, `Slitter`, `Exchange`, `SimulationClock`, `EventQueue`, `KPIEngine`, `FinancialEngine`, `AnimationEngine`, `ScenarioManager`, `Failure`

Parámetros estáticos (constantes configurables):
- Distancias (m), velocidades (m/s), aceleraciones (m/s²), MTBF (h), MTTR (min), costes (€/h, €/m, €/ud), dimensiones (mm), calendarios/turnos, capacidades (kg, ud), gramajes (g/m²), anchos (mm), tolerancias operativas.

### 3. Resolución temporal
- Tick del motor: **1 segundo**.
- Eventos discretos: cola de eventos con prioridad FIFO; tie-breaker por timestamp y por ID de entidad.
- Resolución de conflictos: `priority` explícita > `timestamp` (menor primero) > `entity_id`.

### 4. Motores de decisión (módulos separados)
- Motor físico: trayectorias, velocidades, colisiones.
- Motor logístico: asignación de recursos, dispatching, rutas.
- Motor de producción: consumo, cadencia corrugadora, órdenes.
- Motor financiero: CAPEX/OPEX/ROI/payback.
- Motor de KPIs: cálculo y agregación OEE, MTBF, utilización.
- Motor de eventos aleatorios: fallos, retrasos, mermas.

### 5. Escenarios autogenerables
- Baseline: planta con carretillas (Forklift).
- INGETRANS 1 transfer.
- INGETRANS 2 transfers.
- Híbrido: carretillas + INGETRANS.
- AGV / almacén automático.
- Multi-corrugadora.

### Unidad y formato de datos
- Unidad base: Sistema Internacional (m, kg, s, mm, g/m²). YAML internamente usa `.` como separador decimal.
- Input legacy (con coma decimal) será normalizado al parsear (preprocesado automático).

### Criterios de aceptación de FASE 0
- Documento `00_FIDELITY_FRAMEWORK.md` aprobado por el equipo de simulación.
- Reglas de unidades y formatos definidas y automatizables.

---

Siguiente paso: Generar `01_ARCHITECTURE_REPORT.md` y, tras su revisión, iniciar FASE 2 (generación de entidades).
