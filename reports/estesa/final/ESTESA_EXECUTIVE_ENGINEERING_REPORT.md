# ESTESA Executive Engineering Report

Project: ESTESA x INGECART industrial engineering portfolio review
Date: 2026-07-24

**Prepared for ESTESA**

This report consolidates the INGECART product portfolio into a single engineering publication for executive and technical review. The objective is to explain what industrial problems each solution solves, how the systems operate, how they integrate into existing corrugated plants, and where each technology creates measurable operational value.

---

**Preparado para ESTESA**

Este informe consolida el portfolio de soluciones de INGECART en una única publicación de ingeniería para revisión ejecutiva y técnica. El objetivo es explicar qué problemas industriales resuelve cada solución, cómo operan los sistemas, cómo se integran en plantas de cartón ondulado ya existentes y dónde genera cada tecnología valor operativo medible.

---

## 1. Executive Summary / Resumen Ejecutivo

### EN
Corrugated plants do not usually lose performance because of a single machine. They lose performance because material flow, internal logistics, waste evacuation, end-of-line handling, and operational visibility are not synchronized. The engineering value of the INGECART portfolio is that it addresses those failure points as a connected industrial system rather than as isolated equipment packages.

The portfolio can be read in four technical layers. First, reel logistics and warehouse traceability stabilize the feed to the corrugator. Second, waste, WIP, and residual-material flows are controlled so they stop interfering with production. Third, palletizing and robotic end-of-line systems convert unstable manual output handling into repeatable industrial flow. Fourth, digital systems such as RTLS, Digital Warehouse, and the Industrial Digital Twin convert plant events into engineering decisions.

For ESTESA, the key technical conclusion is straightforward: INGECART should be understood not as a catalog of unrelated machines, but as an engineering portfolio for throughput stability, safer operation, traceability, and plant-wide modernization. The strongest portfolio anchors are INGETRANS for reel logistics, SR-1400 for engineered waste evacuation, Plug and Play Palletizer for fast-entry automation, Heavy Duty Palletizer for high-duty robotic end-of-line cells, and the Digital Warehouse plus RTLS stack for location and material governance.

### ES
Las plantas de corrugado no pierden rendimiento normalmente por una sola máquina. Lo pierden porque el flujo de material, la logística interna, la evacuación de retal, la manipulación de fin de línea y la visibilidad operativa no están sincronizados. El valor de ingeniería del portfolio de INGECART es que ataca esos puntos de fallo como un sistema industrial conectado y no como paquetes aislados de equipos.

El portfolio puede leerse en cuatro capas técnicas. Primero, la logística de bobinas y la trazabilidad de almacén estabilizan la alimentación de la corrugadora. Segundo, los flujos de retal, WIP y material residual se controlan para que dejen de interferir con la producción. Tercero, los paletizadores y sistemas robotizados de fin de línea convierten una salida manual inestable en un flujo industrial repetible. Cuarto, sistemas digitales como RTLS, Digital Warehouse e Industrial Digital Twin convierten eventos de planta en decisiones de ingeniería.

Para ESTESA, la conclusión técnica clave es directa: INGECART no debe leerse como un catálogo de máquinas inconexas, sino como un portfolio de ingeniería para estabilidad de throughput, operación más segura, trazabilidad y modernización global de planta. Los anclajes más fuertes del portfolio son INGETRANS para logística de bobinas, SR-1400 para evacuación de retal, Plug and Play Palletizer para automatización de entrada rápida, Heavy Duty Palletizer para células robotizadas de fin de línea de alto servicio, y la combinación Digital Warehouse + RTLS para gobierno de localización y material.

---

## 2. Engineering Context and Plant Bottlenecks / Contexto de Ingeniería y Cuellos de Botella

### EN
In corrugated production, the highest-cost operational losses usually appear at interfaces rather than inside nominal machine speed. Reel supply is interrupted because forklifts compete with production traffic. Scrap evacuation becomes a hidden bottleneck because conveyors, ramps, and operator routines were not designed as one logistics system. Work in progress accumulates because transfer logic does not adapt to changing priorities. Finished packs create unstable downstream flow because palletizing remains labor dependent. Traceability weakens because location, identity, and production status live in separate systems.

The relevant engineering question is therefore not whether each machine works individually. It is whether the plant can maintain continuous material flow, reconcile inventory and scrap, and preserve operational control under real shift conditions.

### ES
En producción de cartón ondulado, las pérdidas operativas de mayor coste suelen aparecer en las interfaces y no dentro de la velocidad nominal de una máquina. El suministro de bobinas se interrumpe porque las carretillas compiten con el tráfico productivo. La evacuación de retal se convierte en un cuello de botella oculto porque transportadores, rampas y rutinas de operario no fueron diseñados como un único sistema logístico. El trabajo en curso se acumula porque la lógica de transferencia no se adapta a prioridades cambiantes. Los paquetes terminados crean una salida inestable porque el paletizado sigue dependiendo de mano de obra. La trazabilidad se debilita porque ubicación, identidad y estado de producción viven en sistemas separados.

La pregunta de ingeniería relevante no es, por tanto, si cada máquina funciona individualmente. Es si la planta puede mantener flujo continuo de material, reconciliar inventario y retal, y conservar control operativo bajo condiciones reales de turno.

---

## 3. INGECART Engineering Model / Modelo de Ingeniería de INGECART

### EN
The portfolio logic is based on industrial integration rather than isolated machine placement. The same customer problem may require a reel logistics intervention, a waste-flow intervention, a traceability layer, or a combined solution with shared event logic. Across the source base, INGECART appears as an engineering-led organization that diagnoses plant bottlenecks, selects the appropriate mechanical and digital layers, and commissions a plant-specific configuration.

### ES
La lógica del portfolio se basa en integración industrial y no en colocación aislada de máquinas. Un mismo problema de cliente puede requerir una intervención sobre la logística de bobinas, una intervención sobre el flujo de retal, una capa de trazabilidad o una solución combinada con lógica compartida de eventos. En toda la base documental, INGECART aparece como una organización liderada por ingeniería que diagnostica cuellos de botella, selecciona las capas mecánicas y digitales adecuadas y pone en marcha una configuración específica de planta.

---

## 4. Portfolio Architecture and Integration Model / Arquitectura del Portfolio e Integración

### EN
The portfolio can be mapped to a reference architecture for an existing corrugated plant.

1. Material movement backbone.
- INGETRANS supplies reels to the corrugator and returns residual reels to controlled storage positions.
- AMR layers move scrap, support materials, or WIP when route flexibility is more valuable than fixed infrastructure.
- SR-1400 evacuates waste continuously so scrap no longer competes with productive floor space.

2. End-of-line stabilization layer.
- Heavy Duty Palletizer handles demanding multi-out or high-duty robotic palletizing.
- Plug and Play Palletizer creates a faster path for standardized palletizing automation.

3. Traceability and control layer.
- Digital Warehouse governs location, status, and transaction continuity for paper rolls.
- RFID and RTLS link identity, checkpoints, and indoor positioning confidence.
- Full Waste Control connects reel entry, reel exit, residual material, and transfer events into one accountability chain.

4. Decision and optimization layer.
- Industrial Digital Twin validates future-state logistics and capex alternatives.
- Digital control and traceability layers convert plant events into engineering support for operations.

### ES
El portfolio puede mapearse sobre una arquitectura de referencia para una planta corrugada existente.

1. Backbone de movimiento de material.
- INGETRANS abastece la corrugadora y devuelve bobinas residuales a posiciones controladas de almacén.
- Las capas AMR mueven retal, materiales de apoyo o WIP cuando la flexibilidad de ruta aporta más valor que la infraestructura fija.
- SR-1400 evacua retal de forma continua para que el desperdicio deje de competir con el espacio productivo.

2. Capa de estabilización de fin de línea.
- Heavy Duty Palletizer resuelve paletizado robotizado exigente en líneas múltiples o de alto servicio.
- Plug and Play Palletizer crea una vía más rápida para automatización estandarizada de paletizado.

3. Capa de trazabilidad y control.
- Digital Warehouse gobierna ubicación, estado y continuidad transaccional de bobinas.
- RFID y RTLS unen identidad, checkpoints y confianza de posicionamiento indoor.
- Full Waste Control conecta entrada de bobina, salida de bobina, material residual y eventos de transferencia en una sola cadena de accountability.

4. Capa de decisión y optimización.
- Industrial Digital Twin valida estados futuros de logística y alternativas de capex.
- Las capas de control y trazabilidad convierten eventos de planta en soporte operativo de ingeniería.

---

## 5. INGECART PRODUCTS / PRODUCTOS INGECART

### 5.1 Executive Product Summary / Resumen Ejecutivo de Producto

#### EN

| Product | Technical Description | Customer Benefits |
|---|---|---|
| INGETRANS | Rail-based automated reel logistics system that synchronizes supply, return, warehouse dispatch, and corrugator demand under controlled plant-flow rules. | Lower forklift exposure, stronger corrugator continuity, fewer internal logistics delays, and more stable reel governance. |
| AMR Intralogistics Waste Management | Scalable autonomous intralogistics platform that manages waste collection, waste weighing, traceability, and production-support material flows through coordinated missions and MES-linked routing logic. | Cleaner and traceable waste flow, lower manual logistics effort, autonomous replenishment support, and flexible expansion toward broader internal transport tasks. |
| AMR Intralogistics WIP Management | Autonomous transfer layer for moving work in progress between stages without fixed routing lock-in. | Lower congestion, smoother internal flow, less dependence on manual transport. |
| Full Waste Control with AMR Intralogistics and Weighing Stations for Reels In and Reels Out | Closed-loop material accountability system linking weight, identity, transport, and residual-material events. | Better reconciliation, lower unaccounted loss, stronger production control and auditability. |
| Heavy Duty Palletizer | Robotic high-duty palletizing architecture for demanding converting lines and heavy output patterns. | Higher end-of-line stability, lower ergonomic risk, industrial repeatability at sustained cadence. |
| Plug and Play Palletizer | Standardized palletizing cell for rapid deployment with limited integration burden. | Faster automation entry, shorter commissioning horizon, predictable scope and payback. |
| SR-1400 | Engineered continuous scrap evacuation system with sealed chain logic and plant-specific integration. | Lower energy demand, cleaner floor conditions, fewer waste-related interruptions. |
| Digital Warehouse | Real-time roll governance layer for non-automated warehouses, linking location, status, and transactions. | Better inventory accuracy, lower search times, stronger warehouse discipline. |
| Industrial Digital Twin | Simulation and validation environment for logistics, process, and capex decision support. | Lower implementation risk, stronger ROI justification, earlier design error detection. |
| RFID / GPS / RTLS Positioning | Hybrid material-traceability architecture with RFID identity continuity and UWB-first indoor positioning. | Stronger traceability, reduced search ambiguity, more reliable location intelligence. |

#### ES

| Producto | Descripción técnica | Beneficios para el cliente |
|---|---|---|
| INGETRANS | Sistema automatizado por rail para logística de bobinas que sincroniza suministro, retorno, despacho desde almacén y demanda de corrugadora bajo reglas controladas de flujo de planta. | Menor exposición a carretillas, mayor continuidad de corrugadora, menos demoras logísticas internas y gobierno más estable de bobinas. |
| AMR Intralogistics Waste Management | Plataforma autónoma e intralogística escalable que gestiona recogida de residuos, pesaje automático, trazabilidad de retal y transporte de materiales de apoyo mediante misiones coordinadas y lógica enlazada con MES. | Flujo de retal más limpio y trazable, menor esfuerzo logístico manual, soporte autónomo de reposición y expansión flexible hacia más tareas internas. |
| AMR Intralogistics WIP Management | Capa autónoma de transferencia para mover WIP entre etapas sin quedar atado a rutas fijas. | Menor congestión, flujo interno más suave y menos dependencia del transporte manual. |
| Full Waste Control with AMR Intralogistics and Weighing Stations for Reels In and Reels Out | Sistema de accountability en bucle cerrado que conecta peso, identidad, transporte y eventos de material residual. | Mejor conciliación, menos pérdida no contabilizada y mayor control productivo auditable. |
| Heavy Duty Palletizer | Arquitectura robotizada de paletizado de alto servicio para líneas exigentes y patrones de salida pesados. | Mayor estabilidad de fin de línea, menor riesgo ergonómico y repetibilidad industrial sostenida. |
| Plug and Play Palletizer | Célula estandarizada de paletizado para despliegue rápido con baja carga de integración. | Entrada más rápida a la automatización, menor tiempo de puesta en marcha y alcance más predecible. |
| SR-1400 | Sistema continuo de evacuación de retal con lógica de cadena sellada e integración específica por planta. | Menor demanda energética, mejor orden operativo y menos interrupciones por residuos. |
| Digital Warehouse | Capa de gobierno en tiempo real para bobinas en almacenes no automatizados, uniendo ubicación, estado y transacciones. | Más precisión de inventario, menos tiempo de búsqueda y mayor disciplina de almacén. |
| Industrial Digital Twin | Entorno de simulación y validación para soporte a decisiones logísticas, de proceso y capex. | Menor riesgo de implantación, mejor justificación ROI y detección temprana de errores de diseño. |
| RFID / GPS / RTLS Positioning | Arquitectura híbrida de trazabilidad con continuidad RFID y posicionamiento indoor UWB-first. | Trazabilidad más fuerte, menor ambigüedad de búsqueda y localización más fiable. |

### 5.2 Reel Logistics, Warehouse Control, and Traceability / Logística de Bobinas, Control de Almacén y Trazabilidad

#### EN
The strongest technical cluster in the portfolio is the reel-flow family built around INGETRANS, Digital Warehouse, RFID/RTLS, and the Industrial Digital Twin. These systems solve the same industrial problem from different angles: keeping the corrugator continuously supplied while maintaining traceability and reducing uncontrolled traffic.

INGETRANS addresses the physical logistics problem. The available technical material describes rail-based movement of reels from warehouse to consumption points, automatic return of unused or partially used reels, and plant-specific adaptation of supply logic to corrugator demand. The important engineering point is that the system is not merely a transfer device. It is a controlled internal logistics architecture that reduces conflict between production speed and manual transport routines.

Digital Warehouse and RTLS/RFID address the information problem around the same physical flow. Digital Warehouse provides the inventory and location governance plane, while RTLS and RFID strengthen identity continuity and station-level confirmation. Together they reduce search time, improve stock accuracy, and make exception handling more deterministic. The Industrial Digital Twin closes the loop by validating layouts, routes, and operational alternatives before physical implementation.

#### ES
El clúster técnico más fuerte del portfolio es la familia de flujo de bobinas construida alrededor de INGETRANS, Digital Warehouse, RFID/RTLS e Industrial Digital Twin. Estos sistemas resuelven el mismo problema industrial desde ángulos distintos: mantener la corrugadora abastecida de forma continua conservando trazabilidad y reduciendo tráfico no controlado.

INGETRANS resuelve el problema físico de la logística. El material técnico disponible describe movimiento por rail desde almacén a puntos de consumo, retorno automático de bobinas no consumidas o parcialmente utilizadas y adaptación específica de la lógica de suministro a la demanda de la corrugadora. El punto de ingeniería importante es que no se trata solo de un transfer. Es una arquitectura controlada de logística interna que reduce el conflicto entre velocidad de producción y rutinas manuales de transporte.

Digital Warehouse y RTLS/RFID resuelven el problema de información alrededor del mismo flujo físico. Digital Warehouse aporta el plano de gobierno de inventario y localización, mientras RTLS y RFID refuerzan continuidad de identidad y confirmación a nivel de estación. Juntos reducen tiempo de búsqueda, mejoran precisión de stock y hacen el tratamiento de excepciones más determinista. El Industrial Digital Twin cierra el ciclo validando layouts, rutas y alternativas operativas antes de la implantación física.

### 5.3 AMR Intralogistics Waste Management / AMR Intralogistics Waste Management

#### EN
AMR Intralogistics Waste Management must be understood as a multi-mission autonomous intralogistics platform rather than a single-purpose waste collection system. The available engineering material supports a broader operating model in which the same mobile architecture can remove waste, carry it to weighing positions, preserve waste traceability, and support other internal logistics missions that protect production continuity.

In practical plant terms, the platform can execute automatic waste collection, automatic waste weighing, and closed traceability of residual material. It can also transport production-support materials, replenish palletizer interlayers, move and position mandrels, move and position printing cliches, and transfer empty pallets where the line architecture requires it. These tasks are not disconnected add-ons. They are coordinated through the same autonomous routing and fleet-management logic.

The engineering value comes from coordinated internal logistics. Missions can be synchronized with production requirements, prioritized through MES interaction, reassigned dynamically, and expanded modularly when additional plant logistics tasks are incorporated. This means the platform is structurally useful not only for waste control but also for internal supply, support handling, and route resilience in changing factory conditions.

#### ES
AMR Intralogistics Waste Management debe entenderse como una plataforma intralogística autónoma y multimisión, y no como un simple sistema de recogida de residuos. La base documental de ingeniería soporta un modelo operativo más amplio en el que la misma arquitectura móvil puede retirar retal, llevarlo a posiciones de pesaje, mantener la trazabilidad del desperdicio y atender otras misiones internas que protegen la continuidad productiva.

En términos prácticos de planta, la plataforma puede ejecutar recogida automática de residuos, pesaje automático, y trazabilidad cerrada del material residual. También puede transportar materiales de apoyo a producción, reponer interlayers del paletizador, mover y posicionar mandriles, mover y posicionar clichés de impresión y trasladar pallets vacíos cuando la arquitectura de línea lo requiere. Estas tareas no son extensiones desconectadas. Se coordinan bajo la misma lógica de ruteo autónomo y gestión de flota.

El valor de ingeniería proviene de la coordinación logística interna. Las misiones pueden sincronizarse con necesidades de producción, priorizarse mediante interacción con MES, reasignarse dinámicamente y ampliarse de forma modular cuando se incorporan nuevas tareas logísticas de planta. Esto significa que la plataforma no solo es útil para control de retal, sino también para suministro interno, manipulación de materiales de apoyo y resiliencia de rutas bajo condiciones cambiantes de fábrica.

### 5.4 End-of-Line Automation / Automatización de Fin de Línea

#### EN
Heavy Duty Palletizer and Plug and Play Palletizer should be read as two different engineering responses rather than as two variants of the same offer. Heavy Duty Palletizer is the solution for demanding converting lines where cadence, load stability, and robotic duty cycle dominate the design. Plug and Play Palletizer is the accelerated-entry architecture for customers who need repeatable palletizing without the integration overhead of a fully custom cell.

#### ES
Heavy Duty Palletizer y Plug and Play Palletizer deben leerse como dos respuestas de ingeniería diferentes y no como dos variantes de la misma oferta. Heavy Duty Palletizer es la solución para líneas de converting exigentes donde la cadencia, la estabilidad de carga y el duty cycle robotizado dominan el diseño. Plug and Play Palletizer es la arquitectura de entrada acelerada para clientes que necesitan paletizado repetible sin la carga de integración de una célula totalmente a medida.

### 5.5 Operational Impact Examples / Operational Impact Examples

#### EN
The following indicators summarize measurable operational changes supported by the INGETRANS digital-twin comparative documentation and by documented INGECART case material for reel-handling modernization.

- Forklift traffic reduction: documented case material for Ingetrans 2800 reports an approximately 65% reduction of forklift traffic in the production area, while broader portfolio material consistently frames the solution in a 40% to 70% reduction range in critical internal circulation.
- Corrugator availability: the digital-twin comparative report shows OEE improvement from 83% to 89% and a reduction of reel starvation or stock-out events from 264 to 33 in the quarterly simulation window.
- Production continuity: the same simulation set shows quarterly output rising from 14.46 million meters to 15.51 million meters, while annual production increases from 57.84 million meters to 62.04 million meters.
- Logistics efficiency: the annual model shows 3,820 additional completed orders, 2,120 additional reel deliveries, and 1,900 additional reel returns, indicating lower waiting time, fewer logistics bottlenecks, and better warehouse circulation discipline.

#### ES
Los siguientes indicadores resumen cambios operativos medibles soportados por la documentación comparativa de gemelo digital de INGETRANS y por material documentado de modernización del manejo de bobinas.

- Reducción de tráfico de carretillas: el material de caso documentado para Ingetrans 2800 reporta una reducción aproximada del 65% del tráfico de carretillas en el área de producción, mientras que el material de portfolio encuadra de forma consistente la mejora en un rango del 40% al 70% en circulación interna crítica.
- Disponibilidad de corrugadora: el informe comparativo de gemelo digital muestra mejora de OEE desde 83% hasta 89% y una reducción de eventos de desabastecimiento desde 264 hasta 33 en la ventana trimestral simulada.
- Continuidad de producción: el mismo conjunto de simulaciones muestra que la producción trimestral pasa de 14,46 millones de metros a 15,51 millones de metros, mientras la producción anual sube de 57,84 millones a 62,04 millones.
- Eficiencia logística: el modelo anual muestra 3.820 pedidos completados adicionales, 2.120 entregas adicionales de bobinas y 1.900 retornos adicionales, reflejando menos tiempos de espera, menos cuellos logísticos y mejor disciplina de circulación en almacén.

---

## 6. Integration in Existing Factories / Integración en Fábricas Existentes

### EN
The portfolio is clearly retrofit-oriented. Multiple sources position the systems as plant-specific solutions rather than greenfield-only packages. That means layout adaptation is part of the solution, digital layers must ingest real plant events, modernization can be phased by area, and coexistence between forklifts, AMRs, and staff must be designed at interface level.

The practical integration sequence is normally: map the bottleneck, define the event model, isolate interfaces, validate with digital analysis when available, then commission by area without destabilizing the whole plant.

### ES
El portfolio está claramente orientado a retrofit. Múltiples fuentes posicionan los sistemas como soluciones específicas para planta y no como paquetes solo para greenfield. Esto significa que la adaptación al layout forma parte de la solución, las capas digitales deben ingerir eventos reales, la modernización puede hacerse por áreas y la convivencia entre carretillas, AMRs y personal debe diseñarse al nivel de interfaz.

La secuencia práctica suele ser: mapear el cuello de botella, definir el modelo de eventos, aislar interfaces, validar con análisis digital cuando esté disponible y después poner en marcha por áreas sin desestabilizar la planta completa.

---

## 7. Engineering Conclusions / Conclusiones de Ingeniería

### EN
The technical value of the portfolio is strongest when read as a modernization architecture rather than as individual products. INGETRANS, Digital Warehouse, and RTLS stabilize reel availability and traceability. SR-1400 and the AMR family govern residual and in-process flows that otherwise compete with production. The palletizing family stabilizes end-of-line output with differentiated entry points for high-duty and fast-deployment cases. The Industrial Digital Twin strengthens the portfolio by turning plant change into an analyzable engineering decision rather than a trial-and-error intervention.

The portfolio is technically coherent, retrofit-relevant, and differentiated by integration depth. Its engineering advantage does not rest on one isolated machine claim. It rests on the ability to connect material flow, traceability, and decision support into one plant system.

### ES
El valor técnico del portfolio es más fuerte cuando se lee como una arquitectura de modernización y no como productos individuales. INGETRANS, Digital Warehouse y RTLS estabilizan disponibilidad y trazabilidad de bobinas. SR-1400 y la familia AMR gobiernan flujos residuales y en proceso que, de otro modo, compiten con producción. La familia de paletizado estabiliza la salida de fin de línea con puntos de entrada diferenciados para casos de alto servicio y despliegue rápido. Industrial Digital Twin refuerza el portfolio al convertir el cambio de planta en una decisión de ingeniería analizable y no en una intervención por prueba y error.

El portfolio es técnicamente coherente, relevante para retrofit y diferenciado por profundidad de integración. Su ventaja de ingeniería no descansa en una única claim de máquina, sino en la capacidad de conectar flujo de material, trazabilidad y soporte a la decisión en un único sistema de planta.

---

## 8. Executive Product Annex / Anexo Ejecutivo de Producto

### 8.1 INGETRANS

#### Overview / Overview
Rail-based reel-feeding and internal transport architecture for corrugated plants, designed to replace unstable forklift-dependent supply with synchronized delivery and return logic.

#### Industrial problem solved / Problema industrial resuelto
Interruptions in corrugator reel supply, excessive forklift circulation, and weak coordination between warehouse and production demand.

#### Engineering solution / Solución de ingeniería
Automated rail-guided internal logistics linked to warehouse status, exchange zones, and dispatch logic.

#### Main functionalities / Funcionalidades principales
- Automatic reel delivery and return.
- Exchange and track coordination.
- Integration with warehouse logic.

#### Operational benefits / Beneficios operativos
- Less forklift traffic.
- More stable corrugator supply.
- Improved safety and lower manual handling exposure.

#### Typical applications / Aplicaciones típicas
- Corrugator reel rooms.
- Non-automated roll warehouses.

#### Integration possibilities / Posibilidades de integración
- Digital Warehouse
- RFID / RTLS Positioning
- Industrial Digital Twin
- Full Waste Control

#### Related products / Productos relacionados
- Digital Warehouse
- RFID / GPS / RTLS Positioning
- Industrial Digital Twin

### 8.2 AMR Intralogistics Waste Management

#### Overview / Overview
Scalable autonomous intralogistics platform for waste collection and plant-support logistics under coordinated fleet control.

#### Industrial problem solved / Problema industrial resuelto
Manual and fragmented internal logistics around waste, support materials, and repetitive low-value transport tasks that interfere with production continuity.

#### Engineering solution / Solución de ingeniería
Mission-based AMR fleet architecture connected to production requirements and capable of serving several internal logistics functions through the same routing and dispatch model.

#### Main functionalities / Funcionalidades principales
- Automatic waste collection.
- Automatic waste weighing.
- Waste traceability.
- Transport of production support materials.
- Automatic replenishment of palletizer interlayers.
- Transport and positioning of mandrels.
- Transport and positioning of printing cliches.
- Movement of empty pallets where applicable.
- Synchronization with production requirements.
- Interaction with MES.
- Autonomous routing and fleet coordination.
- Modular expansion for additional logistics tasks.

#### Operational benefits / Beneficios operativos
- Less manual transport effort.
- Cleaner and more traceable internal flow.
- Better logistics response to changing production priorities.
- Easier expansion toward additional autonomous internal missions.

#### Typical applications / Aplicaciones típicas
- Corrugated plants with changing route priorities.
- Plants where one AMR fleet must support multiple repetitive logistics tasks.

#### Integration possibilities / Posibilidades de integración
- SR-1400
- Full Waste Control
- RFID / RTLS Positioning
- Palletizing systems

#### Related products / Productos relacionados
- AMR Intralogistics WIP Management
- Full Waste Control
- SR-1400

### 8.3 AMR Intralogistics WIP Management

#### Overview / Overview
Dispatchable WIP transfer architecture for inter-stage movement, temporary buffers, and staged flow balancing.

#### Industrial problem solved / Problema industrial resuelto
Manual transfer of intermediate loads creates congestion, variable response times, and unstable staging between process steps.

#### Engineering solution / Solución de ingeniería
Autonomous mission-based transport between stages, buffers, and handoff points.

#### Main functionalities / Funcionalidades principales
- Dynamic routing.
- Buffer-to-stage transfer.
- Temporary staging support.

#### Operational benefits / Beneficios operativos
- Lower congestion.
- Improved stage-to-stage synchronization.
- Reduced dependence on manual transport.

#### Typical applications / Aplicaciones típicas
- Inter-stage transfer.
- Pre-palletizing staging.

#### Integration possibilities / Posibilidades de integración
- Plug and Play Palletizer
- Heavy Duty Palletizer
- Digital Warehouse

#### Related products / Productos relacionados
- AMR Intralogistics Waste Management
- Full Waste Control

### 8.4 Full Waste Control with AMR Intralogistics and Weighing Stations for Reels In and Reels Out

#### Overview / Overview
Closed-loop material accountability architecture linking reel entry, reel exit, weight, identity, and movement events.

#### Industrial problem solved / Problema industrial resuelto
Weak reconciliation between consumed material, residual material, and route events creates unexplained loss and poor yield visibility.

#### Engineering solution / Solución de ingeniería
Combined weighing, transport-event, and identity architecture for material reconciliation.

#### Main functionalities / Funcionalidades principales
- Reel-in and reel-out weighing points.
- Identity continuity.
- Event-linked transport records.

#### Operational benefits / Beneficios operativos
- Lower unaccounted material loss.
- Better yield control.
- More defensible reporting.

#### Typical applications / Aplicaciones típicas
- Plants with trim-loss uncertainty.
- Auditable material-governance environments.

#### Integration possibilities / Posibilidades de integración
- Digital Warehouse
- RFID / GPS / RTLS Positioning
- SR-1400
- AMR Intralogistics

#### Related products / Productos relacionados
- AMR Waste Management
- Digital Warehouse
- RFID / GPS / RTLS Positioning

### 8.5 Heavy Duty Palletizer

#### Overview / Overview
Robotic high-duty palletizing cell for demanding converting lines requiring stable load formation and industrial repeatability.

#### Industrial problem solved / Problema industrial resuelto
Manual or low-spec end-of-line handling cannot maintain stable cadence in demanding converting environments.

#### Engineering solution / Solución de ingeniería
Robotic palletizing cell with infeed, load-formation logic, and pallet-handling architecture.

#### Main functionalities / Funcionalidades principales
- Robotic palletizing.
- Load forming.
- High-duty conveyor integration.

#### Operational benefits / Beneficios operativos
- Higher end-of-line cadence consistency.
- Lower ergonomic exposure.
- Standardized robotic operation.

#### Typical applications / Aplicaciones típicas
- Multi-out converting lines.
- Heavy load patterns.

#### Integration possibilities / Posibilidades de integración
- Plug and Play Palletizer family
- AMR WIP systems

#### Related products / Productos relacionados
- Plug and Play Palletizer
- KUKA robotic ecosystem

### 8.6 Plug and Play Palletizer

#### Overview / Overview
Pre-engineered palletizing cell for rapid deployment, standardized commissioning, and broad bundle-format flexibility.

#### Industrial problem solved / Problema industrial resuelto
Customers need palletizing automation without the integration burden of a fully bespoke robotic project.

#### Engineering solution / Solución de ingeniería
Standardized palletizing cell with servo-driven gripping and low-overhead deployment model.

#### Main functionalities / Funcionalidades principales
- 12 bundles/minute stable production.
- 2300 mm pallet height.
- 1200 x 1200 mm area.
- More than 50 bundle formats.

#### Operational benefits / Beneficios operativos
- Faster time to production.
- Easier project scoping.
- Format flexibility.

#### Typical applications / Aplicaciones típicas
- Standardized packaging environments.
- Projects with strict commissioning windows.

#### Integration possibilities / Posibilidades de integración
- AMR WIP Management
- Digital Twin validation
- End-of-line conveyor take-offs

#### Related products / Productos relacionados
- Heavy Duty Palletizer

### 8.7 SR-1400

#### Overview / Overview
Continuous engineered scrap evacuation system with sealed-chain logic, variable-speed control, and process-layout integration.

#### Industrial problem solved / Problema industrial resuelto
Scrap accumulation, energy-intensive waste management, and manual intervention degrade line continuity and housekeeping.

#### Engineering solution / Solución de ingeniería
Plant-specific continuous waste-evacuation architecture with sealed transport logic and regulated flow.

#### Main functionalities / Funcionalidades principales
- Continuous evacuation.
- Sealed ramp-chain path.
- Variable-speed control.

#### Operational benefits / Beneficios operativos
- Lower energy burden.
- Cleaner process environment.
- Less manual waste handling.

#### Typical applications / Aplicaciones típicas
- Conversion and finishing lines.
- Plants with sustained scrap generation.

#### Integration possibilities / Posibilidades de integración
- AMR Waste Management
- Full Waste Control

#### Related products / Productos relacionados
- AMR Waste Management
- Full Waste Control

### 8.8 Digital Warehouse

#### Overview / Overview
Real-time roll governance layer for location, status, and transaction continuity in non-automated stock areas.

#### Industrial problem solved / Problema industrial resuelto
Manual warehouse routines create weak inventory accuracy, search delays, and low confidence in location status.

#### Engineering solution / Solución de ingeniería
Real-time roll-state and event-governance layer for warehouse operations.

#### Main functionalities / Funcionalidades principales
- Real-time location visibility.
- Full traceability of movements.
- Exception and search logic.

#### Operational benefits / Beneficios operativos
- Better stock accuracy.
- Lower search time.
- Stronger warehouse discipline.

#### Typical applications / Aplicaciones típicas
- Roll warehouses.
- Intermediate stock zones.

#### Integration possibilities / Posibilidades de integración
- INGETRANS
- RFID / GPS / RTLS Positioning
- Full Waste Control

#### Related products / Productos relacionados
- INGETRANS
- RFID / GPS / RTLS Positioning
- Industrial Digital Twin

### 8.9 Industrial Digital Twin

#### Overview / Overview
Simulation-based engineering environment for layout, route, KPI, and capex validation before physical implementation.

#### Industrial problem solved / Problema industrial resuelto
Plants often commit to logistics and automation changes before understanding flow consequences, interface failure modes, and ROI sensitivity.

#### Engineering solution / Solución de ingeniería
Discrete-event, scenario-driven validation environment for future-state logistics and modernization alternatives.

#### Main functionalities / Funcionalidades principales
- Scenario comparison.
- KPI generation.
- Route and layout validation.
- Financial and event-engine integration.

#### Operational benefits / Beneficios operativos
- Lower decision risk.
- Better capex prioritization.
- Earlier visibility into bottlenecks.

#### Typical applications / Aplicaciones típicas
- Layout redesign.
- Manual versus automated logistics comparison.
- Future-state validation.

#### Integration possibilities / Posibilidades de integración
- INGETRANS
- Digital Warehouse
- AMR flows
- Palletizing cells

#### Related products / Productos relacionados
- INGETRANS
- Digital Warehouse

### 8.10 RFID / GPS / RTLS Positioning

#### Overview / Overview
Hybrid traceability architecture with UWB-first indoor positioning and RFID identity checkpoints for warehouse and station control.

#### Industrial problem solved / Problema industrial resuelto
Without continuous indoor location and identity continuity, warehouse governance and station validation remain slow and error-prone.

#### Engineering solution / Solución de ingeniería
UWB-first positioning reinforced by RFID checkpoints and event-linked traceability logic.

#### Main functionalities / Funcionalidades principales
- Indoor positioning.
- Identity continuity.
- Checkpoint validation.
- Event/API integration.

#### Operational benefits / Beneficios operativos
- Stronger traceability.
- Lower ambiguity in warehouse search and movement.
- Better governance of roll-related transactions.

#### Typical applications / Aplicaciones típicas
- Roll location in warehouses.
- Station validation.
- Exception handling.

#### Integration possibilities / Posibilidades de integración
- Digital Warehouse
- INGETRANS
- Full Waste Control

#### Related products / Productos relacionados
- Digital Warehouse
- INGETRANS
- Industrial Digital Twin
