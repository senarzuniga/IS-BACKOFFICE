# HIS V3 Technical Report

- Run ID: 20260831_065536_ca0f6085
- Source: C:\Users\isena\Documents\GitHub\IS-BACKOFFICE\reports\spe\runs\20260831_065536_ca0f6085\source\OFF-TEST-BRAND_20260831_065536.md
- Pipeline: HIS V3 Production Ready
- Selected Variant: slide_flow
- Executive Quality Score: 100.0
- Visual Similarity Score: 100.0

## Phase Timing
- phase_1_document_discovery_attempt_1: 0.001 s
- phase_2_object_extraction_attempt_1: 0.0 s
- phase_3_image_extraction_attempt_1: 0.0 s
- phase_4_semantic_classification_attempt_1: 0.0 s
- phase_5_dom_reconstruction_attempt_1: 0.001 s
- phase_6_theme_application_attempt_1: 0.061 s
- phase_7_validation_publication_attempt_1: 0.213 s

## Hypotheses
- H1: Strict structure-first reconstruction | score=8.47
- H2: Balanced semantic-first reconstruction | score=8.16
- H3: Visual-priority reconstruction | score=7.63
- Selected: H1 (Strict structure-first reconstruction)

## Discovery
- Slides: 1
- Master Slides: 0
- Layouts: 1
- Hyperlinks: 0
- Notes Slides: 0

## Object Inventory
- Total Objects: 4
- text: 3
- title: 1

## Images
- Total Images: 0
- Deduplicated Images: 0

## Quality Gates
### slide_flow
- Passed: True
- Components reconstructed: 1
- text_coverage: 100.0
- image_coverage: 100.0
- diagram_coverage: 100.0
- smartart_coverage: 100.0
- theme_compliance: 100.0
- accessibility: 100.0
- responsive: 100.0
- typography: 100.0
- layout_quality: 100.0
- visual_similarity: 100.0
### smart_reconstruction
- Passed: True
- Components reconstructed: 1
- text_coverage: 100.0
- image_coverage: 100.0
- diagram_coverage: 100.0
- smartart_coverage: 100.0
- theme_compliance: 100.0
- accessibility: 100.0
- responsive: 100.0
- typography: 100.0
- layout_quality: 100.0
- visual_similarity: 100.0

## Risks Detected
- No images detected in source; visual fidelity relies on text/layout only.

## Suggested Improvements
- Enable OCR/vision fallback to recover embedded rasterized visuals.
