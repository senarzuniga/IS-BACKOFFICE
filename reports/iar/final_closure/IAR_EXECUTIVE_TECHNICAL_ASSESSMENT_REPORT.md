# IAR Executive Technical Assessment Report

Project: IAR - Real Time Paper Roll Location System  
Date: 2026-07-24

---

## Version A - English

### 1. Executive Summary
The engineering challenge is to provide reliable real-time location of paper rolls in non-automated corrugated warehouses under dense stacking, metallic reflections, forklift occlusion, and dynamic layout changes.

Technologies assessed: UWB, BLE AoA, BLE RSSI, Chirp, RFID, GPS RTK, vision-based positioning, and hybrid positioning.

Principal findings:
- UWB is the strongest primary indoor technology for continuous roll localization at operational decision speed.
- BLE AoA is suitable as a complementary medium-precision layer; BLE RSSI is only useful for coarse zone presence.
- RFID is essential for identity continuity and traceability checkpoints, but not as a standalone continuous positioning core.
- Vision adds semantic context, but is sensitive to occlusion, dust, lighting, and maintenance overhead.
- Hybrid architecture, based on UWB + RFID with optional BLE/vision extensions, offers the best long-term resilience.

Recommended technology direction:
- UWB-first architecture with explicit technology abstraction and a hybrid expansion path.

Confidence level:
- High for strategic technology direction.
- Moderate for final supplier award pending harmonized same-site acceptance testing.

### 2. Operational Requirements
A corrugated paper roll warehouse requires:
- Slot-level location confidence under dense stacking.
- Near-real-time updates for forklift operations and search-time reduction.
- Reliable behavior under metallic multipath and intermittent occlusion.
- Valid Z-axis performance for stacked rolls at different heights.
- Manageable calibration and maintenance effort for industrial continuity.
- Scalable architecture for growth in tags, zones, and process complexity.
- Industrial integration capability for MES transaction consistency.
- Readiness for future digital twin and AI-enabled evolution.

### 3. Analysis of Positioning Technologies

#### UWB
- Operating principle: time-based ranging (TDoA/TWR).
- Industrial maturity: high.
- Advantages: high indoor precision potential, low latency, deterministic behavior.
- Limitations: disciplined anchor geometry and calibration management are critical.
- Expected evolution: stronger edge analytics and richer event semantics.
- Suitability for paper roll warehouses: very high.
- Typical applications: industrial RTLS, asset traceability, safety zoning.
- Engineering assessment: preferred primary positioning core.

#### BLE AoA
- Operating principle: angle-of-arrival triangulation.
- Industrial maturity: medium-high.
- Advantages: broad ecosystem, lower entry cost than dense UWB.
- Limitations: precision stability degrades under dense reflections and dynamic occlusion.
- Expected evolution: improved antenna arrays and filtering stacks.
- Suitability: medium as a complementary layer.
- Typical applications: zone analytics and medium-precision asset tracking.
- Engineering assessment: valid support layer, not primary core.

#### BLE RSSI
- Operating principle: signal-strength distance estimation.
- Industrial maturity: high for coarse tracking.
- Advantages: low cost, simple deployment.
- Limitations: high variance in industrial multipath environments.
- Expected evolution: incremental filtering improvements.
- Suitability: low for precise roll localization.
- Typical applications: presence and coarse occupancy detection.
- Engineering assessment: non-critical telemetry layer only.

#### Chirp
- Operating principle: chirp spread-spectrum ranging.
- Industrial maturity: medium/selective.
- Advantages: potential robustness in noisy radio channels.
- Limitations: less broad ecosystem and fewer standardized industrial references than UWB/BLE.
- Expected evolution: niche hybrid deployments.
- Suitability: medium-low as a primary option.
- Typical applications: specialized low-power or selective environments.
- Engineering assessment: secondary option, not preferred core.

#### RFID
- Operating principle: passive/active tag-reader identity events.
- Industrial maturity: very high.
- Advantages: strong traceability checkpoints and low-cost identity continuity.
- Limitations: not continuous high-precision localization by itself.
- Expected evolution: deeper fusion with RTLS event models.
- Suitability: high for identity and transaction tracking.
- Typical applications: inventory traceability and gate/checkpoint control.
- Engineering assessment: mandatory identity companion layer.

#### GPS RTK
- Operating principle: differential satellite positioning.
- Industrial maturity: very high outdoors.
- Advantages: excellent outdoor precision.
- Limitations: unsuitable as indoor primary core.
- Expected evolution: indoor/outdoor boundary handover use.
- Suitability: low for indoor paper roll positioning.
- Typical applications: outdoor yard and fleet positioning.
- Engineering assessment: external boundary technology only.

#### Vision
- Operating principle: camera/LiDAR scene interpretation.
- Industrial maturity: medium-high in controlled environments.
- Advantages: semantic awareness and contextual event understanding.
- Limitations: occlusion, dust, lighting sensitivity, and maintenance burden.
- Expected evolution: stronger fusion with RTLS and robotics.
- Suitability: medium as augmentation.
- Typical applications: safety monitoring, process observability, contextual analytics.
- Engineering assessment: high-value complement, not standalone core.

#### Hybrid Positioning
- Operating principle: multi-technology fusion and confidence reconciliation.
- Industrial maturity: high at architecture level.
- Advantages: resilience, redundancy, graceful degradation.
- Limitations: integration complexity and governance overhead.
- Expected evolution: enterprise standard for mission-critical logistics.
- Suitability: very high for long-term product architecture.
- Typical applications: complex industrial workflows under mixed constraints.
- Engineering assessment: target end-state architecture.

### 4. Supplier Technical Assessment

| Supplier | Technical Stack | Hardware/Software | Installation/Calibration | Accuracy/Latency Position | API/MES Integration | Known Limitations | Engineering Assessment |
|---|---|---|---|---|---|---|---|
| Eliko | UWB/BLE RTLS | Anchors, tags, server + recurring software model | Requires standard UWB site planning and recalibration discipline | Competitive claims; requires harmonized field proof | API and MES pathways documented | License floor and recurring costs; performance comparability still open | Viable pilot candidate; final lock requires controlled acceptance validation |
| Sewio | UWB-centered enterprise RTLS | Mature platform profile, industrial references | Strong commissioning profile | High potential, but final KPIs still require same-site proof | Integration posture strong | Public pricing not fully available in reviewed material | Strong technical shortlist candidate |
| GrowSpace | UWB developer-oriented stack | Gateway/anchor kits with MQTT JSON data openness | Fast pilot setup, but production hardening required | Promising for 3D use; robustness under dense operation to validate | Open messaging model, adaptable MES interface path | Several economic claims are partially verified; tag/anchor scaling must be quoted | Strong PoC acceleration option with low entry cost |
| Pozyx | UWB RTLS with platform licensing | Mature kit and software layer | Operationally credible; 3D quality depends on layout discipline | Competitive baseline, pending same-site normalized benchmark | MQTT/API path suitable for industrial integration | Mandatory platform license and tag scaling costs | Benchmark-grade candidate; award contingent on harmonized field results |

Engineering interpretation:
- Supplier differences are concentrated in calibration maturity, integration depth, and lifecycle cost structure.
- Final decision should be based on same-site, same-protocol, same-KPI validation.

### 5. Comparative Engineering Analysis

#### 5.1 Technical Comparison Matrix
| Criterion | UWB | BLE AoA | BLE RSSI | Chirp | RFID | GPS RTK | Vision | Hybrid |
|---|---|---|---|---|---|---|---|---|
| Accuracy | High | Medium | Low | Medium | Low-Medium | High outdoor / Low indoor | Medium-High | High |
| Latency | High | Medium | Medium | Medium | Medium | Medium | Medium | High |
| Robustness | High | Medium | Low | Medium | High for ID events | Low indoor | Medium | High |
| Installation complexity | Medium-High | Medium | Low | Medium | Medium | Medium | High | High |
| Calibration effort | Medium-High | Medium | Low | Medium | Low | Medium | High | High |
| Maintenance burden | Medium | Medium | Low | Medium | Low-Medium | Medium | High | Medium-High |
| Scalability | High | High | High | Medium | High | Medium | Medium | High |
| Vendor dependency risk | Medium | Medium | Low | Medium | Low | Medium | Medium | Low-Medium |
| Industrial maturity | High | Medium-High | High (coarse use) | Medium | Very High | Very High outdoor | Medium-High | High |
| Digital Twin readiness | High | Medium | Low-Medium | Medium | Medium | Low indoor | High | High |
| AI readiness | High | Medium | Low-Medium | Medium | Medium | Low indoor | High | High |
| MES integration readiness | High | Medium | Medium | Medium | High | Low-Medium | Medium | High |

#### 5.2 Technical-Economic Scoring Panel
Scoring method:
- Technical fit: 40%
- Industrial maturity: 20%
- Economic attractiveness: 25%
- Lifecycle visibility: 10%
- Integration readiness: 5%

| Supplier | Technical fit | Industrial maturity | Economic attractiveness | Lifecycle visibility | Integration readiness | Weighted score |
|---|---:|---:|---:|---:|---:|---:|
| Pozyx | 88 | 86 | 77 | 78 | 84 | 84.0 |
| GrowSpace | 81 | 72 | 92 | 70 | 82 | 80.8 |
| Sewio | 87 | 88 | 56 | 54 | 85 | 76.3 |
| Eliko | 79 | 74 | 60 | 62 | 78 | 72.8 |

Decision reading:
- Best balanced option: Pozyx, because it combines strong technical maturity with acceptable economic structure.
- Best entry economics: GrowSpace, but it requires more industrial hardening before final product lock.
- Strong technical but weaker economic visibility: Sewio.
- Stable but recurrence-sensitive: Eliko.

Sensitivity note:
- If the decision prioritizes PoC entry cost over product maturity, GrowSpace rises.
- If the decision prioritizes industrial readiness and balanced lifecycle economics, Pozyx remains the lead option.

#### 5.3 Engineering Discussion
- UWB provides the best precision-latency-robustness balance for continuous roll localization.
- RFID is the strongest identity companion layer.
- Hybrid architecture is the strongest long-term resilience strategy.

### 6. Engineering Trade-Off Analysis
- Centralized vs distributed positioning: centralized simplifies governance; distributed improves latency and fault containment. Recommended: distributed acquisition with centralized reconciliation.
- Single-vendor vs abstraction layer: single-vendor accelerates initial deployment, but abstraction protects roadmap and reduces lock-in. Recommended: abstraction from phase 1.
- Active tags vs passive tags: active tags provide continuous position; passive tags optimize identity cost only. Recommended: active for positioning, passive for checkpoints.
- Hybrid technologies: increase integration complexity, but improve resilience and evolution. Recommended: phased hybrid evolution after UWB stabilization.
- Fixed anchors vs mobile infrastructure: fixed anchors provide repeatability; mobile infrastructure adds flexibility with more uncertainty. Recommended: fixed backbone with controlled mobile extensions.
- Cloud vs edge: edge for deterministic latency; cloud for analytics and history. Recommended: edge-first operations with cloud-assisted analytics.

### 7. Recommended Architecture for INGECART IAR
Recommended architecture:
- UWB-first industrial positioning platform prepared for hybridization.

Hardware layer:
- Fixed UWB anchors and active tags as the positioning backbone.
- RFID checkpoints for identity and transactional hardening.
- Optional vision nodes in critical zones requiring semantic context.

Communications layer:
- Deterministic local telemetry network.
- Event backbone for movement, inventory, and exception propagation.

Positioning layer:
- Real-time location engine with confidence scoring.
- Outlier filtering, health monitoring, and calibration governance.

Middleware:
- Vendor abstraction API for interchangeable adapters.
- Unified roll-state model independent of vendor payload format.

MES interface:
- Bi-directional contracts for inventory, movement, and event reconciliation.

Future digital twin interface:
- Timestamped state stream and replay-ready history.

Future AI modules:
- Search-time optimization.
- Forklift flow optimization and congestion prediction.
- Anomaly detection and predictive maintenance triggers.

Future product evolution:
- Phase 1: deterministic UWB core + MES integration baseline.
- Phase 2: RFID identity hardening + semantic overlays.
- Phase 3: advanced hybrid fusion and optimization services.

### 8. Technology Selection
Which technology should INGECART adopt?
- UWB as the primary indoor positioning technology, under a hybrid-ready architecture.

Why?
- Best overall balance of precision, latency, industrial robustness, and operational utility.

Why not the alternatives as primary core?
- BLE AoA/BLE RSSI: lower confidence for final slot-level localization in dense stacks.
- RFID: excellent identity layer, insufficient for continuous location.
- Vision-only: higher operational fragility under occlusion and maintenance constraints.
- GPS RTK: unsuitable for indoor primary positioning.

Expected risks:
- Site-specific multipath and vertical-axis edge cases.
- Calibration drift if operational discipline weakens.
- Cost escalation if licenses and support are not normalized early.

Remaining uncertainties:
- Final KPI comparability across suppliers under identical field protocols.
- Lifecycle economics at scale for tags, support, and replacement cycles.

Validation tests required:
- Same-site multi-vendor benchmark with common KPIs.
- Full-shift latency and availability tests under realistic forklift traffic.
- Z-axis reliability tests in stacked-roll scenarios.
- End-to-end MES consistency and reconciliation tests.
- 5-year TCO scenarios (baseline, conservative, expansion).

Technology roadmap:
- Short term: UWB baseline deployment and acceptance qualification.
- Mid term: RFID reinforcement and controlled hybrid enrichment.
- Long term: predictive optimization and scalable multi-site standardization.

### 9. Conclusions
Main findings:
- UWB-first is the strongest technical path for the future IAR product.
- Hybrid-ready architecture is necessary for long-term resilience and scalability.
- Economic structure is a critical differentiator and must be normalized through formal TCO modeling.

Recommended architecture:
- UWB core + vendor abstraction + RFID identity layer + selective semantic augmentation.

Expected product capabilities:
- Reliable roll identification and real-time location.
- Reduced search time and improved inventory traceability.
- Strong MES interoperability and better operational observability.
- A scalable foundation for digital twin and AI-enabled evolution.

Future opportunities:
- Predictive warehouse orchestration.
- Forklift path optimization and congestion reduction.
- Progressive automation readiness with low architectural lock-in.

Engineering confidence:
- High on technology direction.
- Moderate on final supplier award until field and economic normalization are closed.

---

## Version B - Castellano

### 1. Resumen Ejecutivo
El reto de ingenieria consiste en proporcionar localizacion fiable en tiempo real de bobinas de papel dentro de almacenes no automatizados de carton corrugado, bajo condiciones de estiba densa, reflexiones metalicas, oclusion por carretillas y cambios dinamicos de configuracion.

Tecnologias evaluadas: UWB, BLE AoA, BLE RSSI, Chirp, RFID, GPS RTK, vision y posicionamiento hibrido.

Hallazgos principales:
- UWB es la tecnologia primaria mas solida para localizacion continua indoor de bobinas con velocidad de decision operativa.
- BLE AoA es adecuada como capa complementaria de precision media; BLE RSSI solo es util para presencia por zonas.
- RFID es esencial para la continuidad de identidad y los checkpoints de trazabilidad, pero no como core de posicionamiento continuo.
- Vision aporta contexto semantico, aunque es sensible a oclusion, polvo, iluminacion y carga de mantenimiento.
- La arquitectura hibrida, basada en UWB + RFID y con extensiones opcionales BLE/vision, ofrece la mejor resiliencia de largo plazo.

Direccion tecnologica recomendada:
- Arquitectura UWB-first con abstraccion tecnologica explicita y via de expansion hibrida.

Nivel de confianza:
- Alto para la direccion tecnologica estrategica.
- Moderado para la adjudicacion final de proveedor hasta completar validacion armonizada en mismo sitio.

### 2. Requisitos Operacionales
Un almacen de bobinas de carton corrugado requiere:
- Confianza de posicion a nivel hueco bajo estiba densa.
- Actualizacion cuasi en tiempo real para operaciones de carretilla y reduccion del tiempo de busqueda.
- Comportamiento fiable bajo multipath metalico y oclusion intermitente.
- Rendimiento valido del eje Z con bobinas apiladas a distintas alturas.
- Carga de calibracion y mantenimiento gestionable para continuidad industrial.
- Arquitectura escalable para crecimiento de tags, zonas y complejidad de proceso.
- Capacidad de integracion industrial con consistencia transaccional MES.
- Preparacion para evolucion futura a gemelo digital e IA aplicada.

### 3. Analisis de Tecnologias de Posicionamiento

#### UWB
- Principio de operacion: ranging basado en tiempo (TDoA/TWR).
- Madurez industrial: alta.
- Ventajas: alto potencial de precision indoor, baja latencia y comportamiento determinista.
- Limitaciones: requiere disciplina de geometria de anchors y gestion de calibracion.
- Evolucion esperada: mejor analitica edge y semantica de eventos mas rica.
- Idoneidad para almacenes de bobinas: muy alta.
- Aplicaciones tipicas: RTLS industrial, trazabilidad de activos y zonificacion de seguridad.
- Evaluacion de ingenieria: core primario recomendado.

#### BLE AoA
- Principio de operacion: triangulacion por angulo de llegada.
- Madurez industrial: media-alta.
- Ventajas: ecosistema amplio y barrera de entrada menor que UWB denso.
- Limitaciones: menor estabilidad de precision en reflexiones densas y oclusion dinamica.
- Evolucion esperada: mejoras en antenas y filtrado.
- Idoneidad: media como capa complementaria.
- Aplicaciones tipicas: analitica por zonas y seguimiento de precision media.
- Evaluacion de ingenieria: capa de apoyo valida, no core.

#### BLE RSSI
- Principio de operacion: estimacion de distancia por intensidad de senal.
- Madurez industrial: alta para seguimiento grueso.
- Ventajas: bajo costo y despliegue simple.
- Limitaciones: alta variabilidad en entornos industriales multipath.
- Evolucion esperada: mejoras incrementales de filtrado.
- Idoneidad: baja para localizacion precisa.
- Aplicaciones tipicas: presencia y ocupacion basica por zonas.
- Evaluacion de ingenieria: telemetria no critica.

#### Chirp
- Principio de operacion: ranging chirp spread-spectrum.
- Madurez industrial: media/selectiva.
- Ventajas: posible robustez en canales radio ruidosos.
- Limitaciones: ecosistema menos amplio y menos referencias estandarizadas que UWB/BLE.
- Evolucion esperada: rol hibrido de nicho.
- Idoneidad: media-baja como opcion primaria.
- Aplicaciones tipicas: escenarios selectivos de bajo consumo o largo alcance.
- Evaluacion de ingenieria: complemento secundario.

#### RFID
- Principio de operacion: eventos de identidad por tag-lector pasivo o activo.
- Madurez industrial: muy alta.
- Ventajas: checkpoints de trazabilidad y continuidad de identidad muy robustos.
- Limitaciones: no ofrece localizacion continua de alta precision por si sola.
- Evolucion esperada: mayor fusion con modelos RTLS.
- Idoneidad: alta para identidad y trazabilidad transaccional.
- Aplicaciones tipicas: control de inventario y pasos de control.
- Evaluacion de ingenieria: capa companera obligatoria.

#### GPS RTK
- Principio de operacion: posicionamiento diferencial satelital.
- Madurez industrial: muy alta en exterior.
- Ventajas: precision excelente en exterior.
- Limitaciones: no apto como core indoor.
- Evolucion esperada: uso en transicion indoor/outdoor.
- Idoneidad: baja para posicionamiento interior de bobinas.
- Aplicaciones tipicas: patio exterior y flota.
- Evaluacion de ingenieria: tecnologia de borde exterior.

#### Vision
- Principio de operacion: interpretacion de escena con camara/LiDAR.
- Madurez industrial: media-alta en entornos controlados.
- Ventajas: contexto semantico y observabilidad operacional.
- Limitaciones: oclusion, polvo, iluminacion y carga de mantenimiento.
- Evolucion esperada: fusion mas profunda con RTLS y robotica.
- Idoneidad: media como aumento.
- Aplicaciones tipicas: seguridad, analitica contextual y control visual.
- Evaluacion de ingenieria: complemento de alto valor, no backbone unico.

#### Posicionamiento Hibrido
- Principio de operacion: fusion multisensor y reconciliacion de confianza.
- Madurez industrial: alta a nivel de arquitectura.
- Ventajas: resiliencia, redundancia y degradacion controlada.
- Limitaciones: mayor complejidad de integracion y necesidad de gobernanza.
- Evolucion esperada: estandar enterprise en logistica critica.
- Idoneidad: muy alta para arquitectura de producto a largo plazo.
- Aplicaciones tipicas: operaciones industriales complejas.
- Evaluacion de ingenieria: arquitectura objetivo estrategica.

### 4. Evaluacion Tecnica de Proveedores

| Proveedor | Stack tecnico | Hardware/Software | Instalacion/Calibracion | Posicion en precision/latencia | Integracion API/MES | Limitaciones conocidas | Evaluacion de ingenieria |
|---|---|---|---|---|---|---|---|
| Eliko | RTLS UWB/BLE | Anchors, tags, servidor y licenciamiento recurrente | Requiere planificacion de sitio UWB y disciplina de recalibracion | Claims competitivos; requiere prueba armonizada | Rutas API y MES documentadas | Suelo de licencia y OPEX recurrente sensibles a escala | Candidato valido para piloto; lock final requiere validacion controlada |
| Sewio | RTLS enterprise centrado en UWB | Perfil maduro de plataforma con referencias industriales | Buen perfil de comisionamiento | Alto potencial; KPI final requiere prueba en mismo sitio | Postura de integracion robusta | Detalle economico publico insuficiente en el material revisado | Candidato tecnico fuerte de shortlist |
| GrowSpace | Stack UWB orientado a desarrollo | Kits gateway/anchor con salida MQTT JSON abierta | Arranque rapido de piloto; requiere endurecimiento productivo | Prometedor para 3D; robustez en densidad alta por validar | Modelo de mensajeria abierto y adaptable a MES | Algunos claims economicos estan parcialmente verificados; el escalado de tags/anchors debe cotizarse | Opcion fuerte para acelerar PoC con bajo costo de entrada |
| Pozyx | RTLS UWB con plataforma licenciada | Kits y capa software madura | Despliegue creible; calidad 3D depende del layout | Base competitiva, pendiente de benchmark normalizado en mismo sitio | Ruta MQTT/API adecuada para integracion industrial | Licencia de plataforma obligatoria y costo de escalado de tags | Candidato de referencia; adjudicacion sujeta a validacion armonizada |

Interpretacion de ingenieria:
- Las diferencias clave entre proveedores estan en la madurez de calibracion, la profundidad de integracion y la estructura de costo de ciclo de vida.
- La decision final debe basarse en validacion misma planta, mismo protocolo y mismos KPIs.

### 5. Analisis Comparativo de Ingenieria

#### 5.1 Matriz Tecnica Comparativa
| Criterio | UWB | BLE AoA | BLE RSSI | Chirp | RFID | GPS RTK | Vision | Hibrido |
|---|---|---|---|---|---|---|---|---|
| Precision | Alta | Media | Baja | Media | Baja-Media | Alta exterior / Baja interior | Media-Alta | Alta |
| Latencia | Alta | Media | Media | Media | Media | Media | Media | Alta |
| Robustez | Alta | Media | Baja | Media | Alta para eventos de identidad | Baja indoor | Media | Alta |
| Complejidad de instalacion | Media-Alta | Media | Baja | Media | Media | Media | Alta | Alta |
| Esfuerzo de calibracion | Media-Alta | Media | Baja | Media | Baja | Media | Alta | Alta |
| Mantenimiento | Medio | Medio | Bajo | Medio | Bajo-Medio | Medio | Alto | Medio-Alto |
| Escalabilidad | Alta | Alta | Alta | Media | Alta | Media | Media | Alta |
| Dependencia de proveedor | Media | Media | Baja | Media | Baja | Media | Media | Baja-Media |
| Madurez industrial | Alta | Media-Alta | Alta (uso grueso) | Media | Muy Alta | Muy Alta exterior | Media-Alta | Alta |
| Preparacion Gemelo Digital | Alta | Media | Baja-Media | Media | Media | Baja indoor | Alta | Alta |
| Preparacion IA | Alta | Media | Baja-Media | Media | Media | Baja indoor | Alta | Alta |
| Preparacion integracion MES | Alta | Media | Media | Media | Alta | Baja-Media | Media | Alta |

#### 5.2 Panel de Scoring Tecnico-Economico
Metodo de scoring:
- Ajuste tecnico: 40%
- Madurez industrial: 20%
- Atractivo economico: 25%
- Visibilidad de ciclo de vida: 10%
- Preparacion de integracion: 5%

| Proveedor | Ajuste tecnico | Madurez industrial | Atractivo economico | Visibilidad de ciclo de vida | Preparacion integracion | Puntuacion ponderada |
|---|---:|---:|---:|---:|---:|---:|
| Pozyx | 88 | 86 | 77 | 78 | 84 | 84.0 |
| GrowSpace | 81 | 72 | 92 | 70 | 82 | 80.8 |
| Sewio | 87 | 88 | 56 | 54 | 85 | 76.3 |
| Eliko | 79 | 74 | 60 | 62 | 78 | 72.8 |

Lectura de la decision:
- Mejor opcion balanceada: Pozyx, porque combina madurez tecnica fuerte con una estructura economica aceptable.
- Mejor economia de entrada: GrowSpace, pero requiere mas endurecimiento industrial antes del lock final de producto.
- Mejor perfil tecnico pero con menor visibilidad economica: Sewio.
- Perfil estable pero sensible a recurrentes: Eliko.

Nota de sensibilidad:
- Si la decision prioriza el coste de entrada del PoC por encima de la madurez del producto, GrowSpace sube.
- Si la decision prioriza la preparacion industrial y el equilibrio del ciclo de vida, Pozyx sigue liderando.

#### 5.3 Discusion de Ingenieria
- UWB ofrece el mejor balance precision-latencia-robustez para localizacion continua de bobinas.
- RFID es la mejor capa companera de identidad.
- La arquitectura hibrida es la estrategia mas robusta a largo plazo.

### 6. Analisis de Trade-Offs de Ingenieria
- Posicionamiento centralizado vs distribuido: el primero simplifica gobernanza; el segundo mejora latencia y aislamiento de fallos. Recomendacion: captura distribuida con reconciliacion central.
- Single-vendor vs capa de abstraccion: la opcion unica acelera el despliegue, pero aumenta lock-in. Recomendacion: abstraccion desde fase 1.
- Tags activos vs pasivos: activos para posicion continuo; pasivos para identidad de menor costo.
- Tecnologias hibridas: aumentan complejidad, pero mejoran resiliencia y evolucion.
- Anchors fijos vs infraestructura movil: los fijos ofrecen mejor repetibilidad; la infraestructura movil aporta flexibilidad con mas incertidumbre.
- Cloud vs edge: edge para latencia determinista; cloud para analitica e historico.

### 7. Arquitectura Recomendada para INGECART IAR
Arquitectura recomendada:
- Plataforma industrial UWB-first, preparada para hibridacion.

Capa de hardware:
- Anchors UWB fijos y tags activos como backbone de posicionamiento.
- Checkpoints RFID para identidad y endurecimiento transaccional.
- Nodos de vision opcionales en zonas criticas donde se requiera contexto semantico.

Capa de comunicaciones:
- Red local determinista para telemetria de posicionamiento.
- Backbone de eventos para movimientos, inventario y excepciones.

Capa de posicionamiento:
- Motor en tiempo real con scoring de confianza.
- Filtrado de outliers, monitoreo de salud y gobernanza de calibracion.

Middleware:
- API de abstraccion de proveedor para adapters intercambiables.
- Modelo unificado de estado de bobina independiente del payload del vendor.

Interfaz MES:
- Contratos bidireccionales para inventario, movimientos y reconciliacion de eventos.

Interfaz futura de gemelo digital:
- Flujo de estado con marca temporal e historial apto para replay.

Modulos futuros de IA:
- Optimizacion de tiempo de busqueda.
- Optimizacion de flujo de carretillas y prediccion de congestion.
- Deteccion de anomalias y disparadores de mantenimiento predictivo.

Evolucion futura del producto:
- Fase 1: core UWB determinista + baseline de integracion MES.
- Fase 2: endurecimiento RFID de identidad + overlays semanticos.
- Fase 3: fusion hibrida avanzada y servicios de optimizacion.

### 8. Seleccion Tecnologica
Que tecnologia debe adoptar INGECART?
- UWB como tecnologia primaria de posicionamiento indoor, sobre una arquitectura preparada para hibridacion.

Por que?
- Mejor balance global entre precision, latencia, robustez industrial y utilidad operativa.

Por que no las alternativas como core primario?
- BLE AoA/BLE RSSI: menor confianza para posicion final a nivel hueco en estibas densas.
- RFID: excelente capa de identidad, insuficiente para localizacion continua.
- Vision-only: fragilidad operativa mayor ante oclusion y mantenimiento.
- GPS RTK: no apto para posicionamiento indoor primario.

Riesgos esperados:
- Multipath especifico de sitio y casos limite del eje vertical.
- Deriva de calibracion si no se mantiene disciplina operativa.
- Escalada de costos si licencias y soporte no se normalizan desde el inicio.

Incertidumbres restantes:
- Comparabilidad final de KPI entre proveedores bajo protocolo identico.
- Economia de ciclo de vida a escala para tags, soporte y reposicion.

Pruebas de validacion requeridas:
- Benchmark multi-vendor en mismo sitio con KPIs comunes.
- Prueba de latencia y disponibilidad en turno completo con trafico real.
- Prueba de fiabilidad del eje Z en bobina apilada.
- Prueba end-to-end de consistencia y reconciliacion MES.
- Escenarios TCO a 5 anos (base, conservador y expansion).

Roadmap tecnologico:
- Corto plazo: despliegue baseline UWB y cualificacion de aceptacion.
- Medio plazo: refuerzo RFID y enriquecimiento hibrido controlado.
- Largo plazo: optimizacion predictiva y estandarizacion escalable multi-planta.

### 9. Conclusiones
Hallazgos principales:
- UWB-first es la via tecnica mas robusta para el futuro IAR.
- La arquitectura hibrida es necesaria para resiliencia y escalabilidad de largo plazo.
- La estructura economica es un diferenciador critico y debe normalizarse mediante un modelado TCO formal.

Arquitectura recomendada:
- Core UWB + abstraccion de proveedor + capa RFID de identidad + aumento semantico selectivo.

Capacidades esperadas del producto:
- Identificacion de bobina fiable y localizacion en tiempo real.
- Reduccion del tiempo de busqueda y mejora de la trazabilidad de inventario.
- Interoperabilidad robusta con MES y mayor observabilidad operativa.
- Base escalable para evolucion a gemelo digital e IA aplicada.

Oportunidades futuras:
- Orquestacion predictiva del almacen.
- Optimizacion de rutas de carretillas y reduccion de congestion.
- Preparacion para automatizacion progresiva con bajo lock arquitectonico.

Confianza de ingenieria:
- Alta en direccion tecnologica.
- Moderada en adjudicacion final de proveedor hasta cerrar la validacion de campo y la normalizacion economica.
