# ScenarioManager

## Propósito
Gestionar la creación, parametrización y ejecución de escenarios (Baseline Forklift, INGETRANS, híbrido, AGV, etc.).

## Atributos
| Atributo | Tipo | Unidad | Default | Min | Max | Obligatorio |
| scenarios | list | - | [] | - | - | Sí |
| active_scenario | string | - | null | - | - | No |

## States
- IDLE → LOADING → RUNNING → COMPLETED

## Inputs
- `CreateScenario`, `RunScenario`, `StopScenario`

## Outputs
- `ScenarioStarted`, `ScenarioCompleted`, `ScenarioParams`

## Relaciones
- instancia → ConfigDatabase, SimulationClock, Entities

## Parámetros de Configuración
Referenciar: `03_CONFIG_DATABASE/config_master.yaml`

## Reglas de Validación
- `active_scenario` debe existir en `scenarios`

## KPIs afectados
- Comparaciones entre escenarios

## Riesgos
- Mistmatch de configuraciones aplica overrides incorrectos

## Prioridad
- Alta
