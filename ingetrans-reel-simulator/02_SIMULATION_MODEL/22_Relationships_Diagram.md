# 22_Relationships_Diagram

Propósito: Documento tabular que mapea relaciones entre entidades del modelo.

| From | Relationship | To | Notes |
|------|--------------|----|-------|
| Warehouse | almacena | Reel | Slots, capacidades |
| Warehouse | coordina_con | Forklift, Transfer | Recepciones y salidas |
| Exchange | sirve_a | RollStand | Zona de intercambio |
| Track | conecta_a | RollStand, Exchange, Warehouse | Transporte lineal |
| RollStand | alimenta | Corrugator | Instalación de reels |
| Transfer | opera_sobre | Track, Exchange, Warehouse | Movimientos |
| Forklift | asigna_a | Reel | Movimientos manuales |
| ProductionOrder | requiere | Reel, PaperGrade | Demanda de consumo |
| ScenarioManager | instancia | ConfigDatabase | Escenarios y overrides |
| EventQueue | alimenta | Entities | Eventos discretos |
| KPIEngine | consume | EventQueue | Cálculo de métricas |
| FinancialEngine | consume | KPIEngine | Cálculo financiero |

Notas: Todos los enlaces deben representarse en el engine mediante referencias de ID para evitar dependencias circulares.
