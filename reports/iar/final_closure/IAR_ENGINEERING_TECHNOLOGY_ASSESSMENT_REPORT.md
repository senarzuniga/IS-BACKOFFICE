# Informe de Evaluacion Tecnologica de Ingenieria IAR

Fecha: 2026-07-24
Autor: Oficina CTO - Ingenieria Industrial INGECART

## 1. Resumen Ejecutivo
La revision tecnica de la base de evidencia IAR confirma que la trazabilidad interior de bobinas con alta precision se atiende mejor con una estrategia UWB-first, implementada bajo una arquitectura faseada centrada en gemelo digital con abstraccion modular para preservar flexibilidad de proveedor a largo plazo.

El alcance cubrio el corpus completo procesado de documentacion de proveedores RTLS, matrices tecnicas comparativas, scorecards de arquitectura, registros de contradicciones y evidencias de validacion ya indexadas en el Knowledge Hub. Las familias tecnologicas evaluadas incluyen UWB, BLE AoA, RFID, posicionamiento asistido por vision, composiciones RTLS hibridas y referencias adyacentes a Chirp y GPS RTK como paradigmas alternativos.

Hallazgos principales:
- UWB se mantiene como el unico candidato del corpus revisado con via creible hacia localizacion interior continua en rango submetro a decimetro para operaciones de bobinas.
- Las afirmaciones de precision absoluta entre proveedores no son directamente comparables sin condiciones de prueba normalizadas; existe contradiccion en cifras publicas.
- La madurez de APIs e integracion varia segun profundidad tecnica y apertura documental del proveedor; esto es un diferenciador critico para flujos de INGEPRO, MES, Gemelo Digital y futuros AMR.
- La arquitectura con mayor puntuacion es el modelo faseado centrado en gemelo digital porque equilibra realismo de despliegue, mantenibilidad, preparacion para IA y modularidad futura.

Recomendacion final:
- Adoptar UWB como base de posicionamiento IAR.
- Productizar mediante capa de abstraccion modular y despliegue faseado twin-centric.
- Diferir el lock-in final de proveedor hasta que la validacion de campo controlada cierre las contradicciones de rendimiento restantes.

Nivel de confianza:
- Confianza en direccion estrategica: alta.
- Confianza para adjudicacion inmediata de proveedor: moderada.
- Indice de confianza de evidencia normalizada desde distribucion validada de claims: 49.7/100.

## 2. Estado Actual de las Tecnologias RTLS
### UWB
Principio de operacion: ranging basado en tiempo (principalmente variantes TDoA/TWR) mediante pulsos ultracortos.
Madurez: alta para casos de uso de trazabilidad industrial indoor.
Adopcion industrial: fuerte en despliegues de manufactura y logistica desde piloto a produccion.
Fortalezas: alto potencial de precision espacial, fuerte comportamiento en tiempo real, buen encaje en pipeline de eventos.
Limitaciones: sensibilidad a geometria de instalacion, dependencia de calidad de calibracion, diferencias de definicion de KPI entre proveedores.
Evolucion esperada: mayor procesamiento edge, mejor gestion energetica de tags, semantica de eventos mas robusta para gemelo digital.

### Chirp
Principio de operacion: enfoques de ranging estilo chirp spread-spectrum en sistemas de localizacion.
Madurez: media en ecosistema amplio, baja evidencia directa en el corpus IAR actual.
Adopcion industrial: selectiva.
Fortalezas: potencial robustez en canales ruidosos.
Limitaciones: evidencia directa de proveedor limitada en esta linea base de mision.
Evolucion esperada: hibridacion de nicho con stacks RTLS indoor mainstream.

### BLE AoA
Principio de operacion: triangulacion por angulo de llegada sobre infraestructura BLE.
Madurez: media-alta.
Adopcion industrial: amplia para tracking por zonas y precision media.
Fortalezas: menor costo de entrada de infraestructura, ecosistema de hardware amplio.
Limitaciones: estabilidad de precision inferior a UWB en layouts industriales densos; sensibilidad a multipath.
Evolucion esperada: mejores arreglos de antena y filtrado, manteniendose en general por debajo del sobre de precision UWB para pilas densas de bobinas.

### RFID
Principio de operacion: captura de identidad/evento via tags y lectores pasivos o activos.
Madurez: muy alta.
Adopcion industrial: muy alta para checkpoints de trazabilidad.
Fortalezas: continuidad de identidad a bajo costo, fuerte compatibilidad con flujos transaccionales.
Limitaciones: por si sola no sustituye posicionamiento continuo.
Evolucion esperada: rol creciente como capa complementaria en arquitecturas hibridas.

### GPS RTK
Principio de operacion: correccion diferencial satelital para alta precision outdoor.
Madurez: muy alta en exterior.
Adopcion industrial: alta en exterior, baja relevancia en interior.
Fortalezas: excelente precision geoespacial a cielo abierto.
Limitaciones: debilidad estructural para posicionamiento indoor de almacen de bobinas.
Evolucion esperada: integracion en escenarios de handover indoor-outdoor, no como nucleo primario RTLS interior.

### Posicionamiento Basado en Vision
Principio de operacion: interpretacion de escena con camara/LiDAR/computer vision.
Madurez: media-alta segun control del entorno.
Adopcion industrial: creciente en lineas controladas y robotica.
Fortalezas: contexto semantico rico, sin tag activo por activo en algunos escenarios.
Limitaciones: oclusion, dependencia de iluminacion, intensidad de mantenimiento y computo en entornos de almacen con polvo.
Evolucion esperada: fusion mas fuerte con UWB y stacks de localizacion AMR.

### Sistemas de Posicionamiento Hibrido
Principio de operacion: combinacion multisensor (por ejemplo UWB + RFID/vision/BLE).
Madurez: alta a nivel de arquitectura, variable segun disciplina de implementacion.
Adopcion industrial: creciente en instalaciones avanzadas.
Fortalezas: resiliencia, aislamiento de modos de fallo, mejor opcionalidad de ciclo de vida.
Limitaciones: complejidad de integracion y carga de gobernanza.
Evolucion esperada: patron empresarial por defecto para plataformas industriales de localizacion criticas.

## 3. Analisis Tecnico de Cada Proveedor
### Eliko
Perfil de empresa y plataforma:
- Estructuras comerciales practicas demostradas (hardware + licencias recurrentes + servicios) y modelo de soporte de implementacion.
- La evidencia incluye elementos de oferta UWB y lenguaje de integracion, pero la completitud de benchmark tecnico es desigual en datos validados.

Tecnologia y arquitectura:
- La evidencia del stack de posicionamiento en la matriz validada actual es escasa frente a la amplitud de pares.
- La transparencia de API/SDK es menor en perfil validado frente a referencias competidoras.

Hardware y software:
- Presencia de referencias de catalogo de tags y anchors con componentes de mantenimiento y servicio.
- El modelo de licencia anual y estructura de tarifas de servicio impactan materialmente la planificacion de TCO.

Despliegue, calibracion y escalabilidad:
- Requiere disciplina estandar de planificacion de sitio UWB.
- La evidencia verificada de escalabilidad es limitada en la matriz normalizada.

Integracion y preparacion DT/AMR/IA:
- Existen claims de integracion; la profundidad independiente sigue siendo mixta.
- La preparacion para gemelo digital y AMR requiere validacion explicita de interfaces en PoC.

Limitaciones conocidas:
- Brecha amplia entre detalle comercial y especificidad de rendimiento validada de forma independiente en la tabla normalizada final.

Evaluacion de ingenieria:
- Candidato viable para engagement comercial y participacion en piloto.
- Insuficiente para lock tecnico final sin evidencia de rendimiento verificada mas robusta bajo protocolo de aceptacion INGECART.

### Sewio
Perfil de empresa y plataforma:
- Fuerte enfoque de ingenieria en el material revisado con trayectoria prolongada de especializacion UWB.
- La arquitectura documentada y el empaquetado de despliegue parecen maduros para despliegues industriales.

Tecnologia y arquitectura:
- Nucleo UWB con postura practica de integracion empresarial.
- Referencias mas claras de capas de software y modelo de implementacion.

Hardware y software:
- Referencias de familia industrial de tags/anchors con evidencia de kits de despliegue.
- Orientacion de integracion de plataforma alineada con arquitectura de planta orientada a eventos.

Despliegue, calibracion y escalabilidad:
- Buenos indicadores de madurez; aun sujeto a confirmacion de KPI normalizados bajo mismas condiciones usadas para pares.

Integracion y preparacion DT/AMR/IA:
- Alto potencial por arquitectura orientada a integracion y ajuste a flujos empresariales.

Limitaciones conocidas:
- Las cifras de rendimiento reportadas siguen dentro del sobre de contradiccion entre proveedores.

Evaluacion de ingenieria:
- Contendiente tecnicamente fuerte; debe permanecer en shortlist final.

### GrowSpace
Perfil de empresa y plataforma:
- Perfil orientado a desarrollador con narrativas practicas de implementacion y marco de datos centrado en MQTT.

Tecnologia y arquitectura:
- Referencias centradas en UWB con lenguaje explicito de uso orientado a 3D en el corpus revisado.

Hardware y software:
- Estructuras de kit practicas y ejemplos de integracion a nivel aplicacion utiles para puesta en marcha rapida de piloto.

Despliegue, calibracion y escalabilidad:
- Atractivo para prototipado rapido y experimentacion de integracion.
- Confianza de industrializacion menor que alternativas top enterprise-heavy hasta prueba de campo.

Integracion y preparacion DT/AMR/IA:
- Buen mensaje sobre apertura de datos y acoplamiento de aplicaciones.
- Requiere validacion de robustez bajo estresores reales de almacen de carton corrugado.

Limitaciones conocidas:
- Confianza de evidencia materialmente inferior a la deseada para lock directo en escala productiva.

Evaluacion de ingenieria:
- Valioso como socio de innovacion y velocidad en contexto PoC; la seleccion critica para produccion exige validacion independiente mas fuerte.

### Pozyx
Perfil de empresa y plataforma:
- Oferta RTLS reconocida con huella documental amplia.

Tecnologia y arquitectura:
- Referencias de posicionamiento basado en UWB con consideraciones de integracion y cloud/on-prem en el material revisado.

Hardware y software:
- Existen referencias de empaquetado maduro; implicaciones de precio/licenciamiento deben normalizarse contra restricciones de ciclo de vida.

Despliegue, calibracion y escalabilidad:
- El candidato parece operacionalmente creible; los resultados de benchmark siguen acotados por confianza de evidencia y requisitos de normalizacion de contradicciones.

Integracion y preparacion DT/AMR/IA:
- Capacidad de integracion probablemente suficiente para ajuste arquitectonico, pendiente de pruebas estandarizadas de interoperabilidad.

Limitaciones conocidas:
- La puntuacion de confianza en la matriz actual verified-only es inferior al objetivo para lock final directo.

Evaluacion de ingenieria:
- Mantener como benchmark y comparador de negociacion; adjudicacion final condicionada a resultados de validacion controlada.

## 4. Analisis Comparativo de Tecnologias
### Matriz Comparativa de Ingenieria
| Criterio | UWB | BLE AoA | RFID | Vision | RTLS Hibrido |
|---|---|---|---|---|---|
| Potencial de precision (indoor) | Alta | Media | Baja-Media | Media-Alta | Alta |
| Adecuacion de latencia para orquestacion en tiempo real | Alta | Media | Baja-Media | Media | Alta |
| Escalabilidad en operaciones de almacen de bobinas | Alta | Alta | Alta | Media | Alta |
| Esfuerzo de instalacion | Medio-Alto | Medio | Medio | Alto | Alto |
| Carga de mantenimiento | Media | Media | Baja-Media | Alta | Media-Alta |
| Costo de infraestructura | Medio-Alto | Medio | Baja-Media | Alto | Alto |
| Costo de ciclo de vida | Medio | Medio | Medio | Alto | Media-Alta |
| Riesgo de dependencia de proveedor | Medio | Medio | Baja-Media | Medio | Baja-Media |
| Madurez industrial | Alta | Media-Alta | Muy Alta | Media-Alta | Alta |
| Confiabilidad bajo restricciones de almacen | Alta (con disciplina de calibracion) | Media | Media | Media | Alta |
| Complejidad de integracion | Media | Media | Media | Alta | Alta |
| Superficie de ciberseguridad | Media | Media | Media | Alta | Alta |
| Preparacion para Gemelo Digital | Alta | Media | Media | Alta | Alta |
| Preparacion para integracion IA | Alta | Media | Media | Alta | Alta |

### Matriz de Decision de Proveedores (modelo verified-only)
| Proveedor | Puntuacion Tecnologica | Puntuacion Ingenieria | Puntuacion Negocio | Puntuacion Confianza | Puntuacion Recomendacion Global |
|---|---:|---:|---:|---:|---:|
| Eliko | 72.50 | 62.00 | 52.00 | 100.00 | 70.75 |
| Sewio | 55.65 | 63.00 | 52.00 | 54.55 | 56.90 |
| GrowSpace | 53.53 | 63.00 | 52.00 | 42.86 | 53.93 |
| Pozyx | 52.59 | 63.00 | 52.00 | 36.36 | 52.35 |

Interpretacion de ingenieria:
- La matriz es valida como salida de gobernanza de evidencia, no como ranking final de compra.
- La asimetria de confianza entre proveedores y la presencia de contradicciones impiden adjudicacion directa solo con esta tabla.

## 5. Claims de Marketing versus Realidad de Ingenieria
| Claim del proveedor | Estado de evidencia | Realidad de ingenieria | Confianza | Conclusion |
|---|---|---|---:|---|
| Posicionamiento clase sub-30 cm en condiciones industriales | Contradicho entre proveedores | El rendimiento depende fuertemente de geometria, entorno y definicion de KPI | Media-Baja | Debe demostrarse con protocolo A/B en mismo sitio |
| Confiabilidad 3D por defecto en niveles de estiba | Parcialmente Verificado | El 3D es viable pero sensible a topologia de anchors y oclusion | Media | Requiere validacion en estibas de bobinas multi-altura |
| Integracion MES/ERP fluida por defecto | Parcialmente Verificado | La integracion existe a nivel conceptual; la profundidad de implementacion varia materialmente | Media | Validar semantica API, throughput y manejo de fallos |
| Despliegue rapido con calibracion minima | No Verificado para condiciones productivas | La velocidad de comisionamiento es plausible para huella piloto, no garantizada para robustez de almacen completo | Baja-Media | Exigir plan de comisionamiento por sitio y KPI de aceptacion |
| Menor costo total manteniendo precision enterprise-grade | No Verificado | Los claims de liderazgo en costo son incompletos sin normalizacion de ciclo de vida y soporte | Baja | Ejecutar escenario TCO a 5 anos con sensibilidad de soporte/licencias |

Las afirmaciones no soportadas estan catalogadas explicitamente en los artefactos validados de claims y no deben influir decisiones de adjudicacion final hasta su confirmacion independiente.

## 6. Analisis de Arquitectura para INGECART IAR
### Alternativas evaluadas
- A: Arquitectura single-vendor
- B: Capa de abstraccion multi-vendor
- C: Arquitectura RTLS hibrida
- D: Framework modular de posicionamiento
- E: Arquitectura faseada centrada en gemelo digital

### Resultados de arquitectura puntuados
| Arquitectura | Robustez de Ingenieria | Independencia de Proveedor | Escalabilidad Futura | Integracion IA | Compatibilidad DT | Integracion AMR | TCO | Riesgo Tecnico | Mantenibilidad | Global |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A Single-vendor | 8.4 | 4.8 | 8.3 | 8.2 | 8.6 | 8.0 | 7.2 | 7.0 | 7.8 | 75.92 |
| B Abstraccion multi-vendor | 8.8 | 9.2 | 9.0 | 8.9 | 9.0 | 8.8 | 7.0 | 8.2 | 8.2 | 85.97 |
| C RTLS hibrido | 9.0 | 8.4 | 9.1 | 9.0 | 9.2 | 8.9 | 7.6 | 8.5 | 8.6 | 87.20 |
| D Framework modular | 8.9 | 9.0 | 9.3 | 9.2 | 9.3 | 9.1 | 7.4 | 8.4 | 8.8 | 88.44 |
| E Faseada twin-centric | 9.2 | 8.5 | 9.4 | 9.4 | 9.5 | 9.2 | 7.8 | 8.8 | 9.0 | 89.96 |

Arquitectura recomendada: E, faseada twin-centric, con limites de abstraccion explicitos para preservar opcionalidad e integrar plugins de posicionamiento futuros.

## 7. Decision de Ingenieria
### Que tecnologia debe adoptar INGECART?
UWB como tecnologia core de posicionamiento interior para IAR, implementada con abstraccion modular y preparacion para extension hibrida.

### Por que esta eleccion?
- Mejor ajuste tecnico para localizacion interior continua de bobinas.
- Via mas solida para sincronizacion con Gemelo Digital y orquestacion orientada a eventos.
- Compatible con futuras capas de optimizacion AMR e IA.
- La flexibilidad arquitectonica puede mitigar riesgo de lock de proveedor.

### Por que no alternativas como core primario?
- BLE AoA: menor confianza de precision para operaciones densas de estiba de bobinas.
- RFID sola: excelente para identidad/eventos pero insuficiente como backbone de posicionamiento continuo.
- Solo vision: sensibilidad operativa a oclusion y mayor carga de mantenimiento en condiciones de almacen.
- GPS RTK: no apto como nucleo primario de localizacion interior.

### Riesgos tecnicos restantes
- Contradiccion entre proveedores sobre claims de rendimiento normalizado.
- Precision 3D especifica de sitio bajo condiciones metalicas e inventario apilado.
- Confiabilidad de integracion bajo carga operacional pico.

### Validacion aun requerida antes del compromiso de producto
- Piloto controlado multi-vendor con protocolo KPI armonizado.
- Pruebas end-to-end de latencia y resiliencia INGEPRO y MES.
- Caracterizacion de estabilidad, bateria y esfuerzo de mantenimiento bajo operacion de turno completo.

### Horizonte de evolucion tecnologica a cinco anos
- UWB se mantiene central para posicionamiento indoor de alto valor.
- Aumenta la hibridacion con capas de identidad y percepcion.
- La orquestacion impulsada por IA y optimizacion predictiva se vuelven diferenciadores estandar.
- Las abstracciones neutrales a proveedor se convierten en punto estrategico de apalancamiento.

## 8. Hoja de Ruta de Producto Recomendada
### Arquitectura core de plataforma
- Motor RTLS core (UWB-first)
- Capa de comunicacion (event bus + API gateway)
- Capa de abstraccion de posicionamiento (adapters de proveedor)
- Servicio de sincronizacion de Gemelo Digital
- Servicio de integracion INGEPRO
- Servicio de integracion MES
- Modulo de orquestacion IA
- Integracion de evidencia y modelos con Knowledge Hub
- Conector de simulacion (what-if y replay)

### Modulos de expansion
- Adapter de orquestacion AMR
- Paquete de plugins de fusion sensorial
- Deteccion avanzada de anomalias
- Modulo de benchmark inter-planta

### Roadmap
1. Fase 1: Base piloto
- Desplegar UWB en zona controlada, establecer KPIs base, validar contratos de integracion.

2. Fase 2: Escalado operacional
- Extender al alcance completo de almacen, endurecer controles de confiabilidad, activar supervision guiada por gemelo digital.

3. Fase 3: Automatizacion inteligente
- Introducir acoplamiento de eventos AMR, optimizacion asistida por IA y extensiones de fusion sensorial.

## 9. Conclusiones
La direccion recomendada esta tecnicamente justificada porque maximiza el valor del posicionamiento preservando el control arquitectonico a largo plazo. UWB-first con arquitectura faseada twin-centric es la opcion mas robusta para IAR con la evidencia actual.

La confianza no es binaria:
- La confianza en direccion de arquitectura y tecnologia es alta.
- La confianza en adjudicacion de proveedor es moderada hasta que la validacion de campo armonizada cierre la incertidumbre restante.

Las incertidumbres restantes son explicitas y gestionables mediante pruebas de campo dirigidas y criterios de aceptacion de integracion.

Impacto esperado en ROI por seleccion tecnologica correcta:
- Reduccion de ineficiencia en busqueda y manejo de bobinas.
- Menor error operacional y brechas de trazabilidad.
- Mayor calidad de planificacion mediante observabilidad del gemelo digital.
- Apalancamiento estrategico de plataforma para automatizacion futura y diferenciacion por IA.

Impacto estrategico para INGECART:
- Posiciona IAR como plataforma industrial de grado ingenieria y no como solucion puntual.
- Crea know-how de integracion defendible en operaciones de planta de carton corrugado.
- Habilita una ruta escalable de productizacion con riesgo tecnico controlado.
