# Animation Engine

## Propósito
Diseñar un motor que exporte trazas de movimiento por tick para visualizadores externos (sin UI propio).

## Salida
- Archivo de trazas (`.jsonl` o `.ndjson`) donde cada línea es un `AnimationFrame` con timestamp y posiciones de entidades.

## Parámetros
- `sample_rate_s` para control de granularidad.
