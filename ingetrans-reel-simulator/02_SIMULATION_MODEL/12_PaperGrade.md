# PaperGrade

## Propósito
Definir las propiedades del papel que afectan masa, gramaje y comportamiento en producción.

## Atributos
| Atributo | Tipo | Unidad | Default | Min | Max | Obligatorio |
| id | string | - | auto | - | - | Sí |
| code | string | - | "A" | - | - | Sí |
| gramaje_g_m2 | float | g/m² | 120.0 | 10 | 1000 | Sí |
| density_kg_m3 | float | kg/m³ | 800.0 | 100 | 2000 | No |
| width_mm | float | mm | 1500.0 | 100 | 3000 | Sí |

## States
- STATIC (no state machine requerido)

## Inputs
- `CreatePaperGrade`, `AdjustPaperGrade`

## Outputs
- `PaperGradeDefined`

## Relaciones
- aplicado_en → Reel, ProductionOrder

## Parámetros de Configuración
Referenciar: `03_CONFIG_DATABASE/config_paper_grade.yaml`

## Reglas de Validación
- `gramaje_g_m2 > 0`

## KPIs afectados
- Material consumption accuracy

## Riesgos
- Errores en gramaje producen desviaciones en masa estimada

## Prioridad
- Media
