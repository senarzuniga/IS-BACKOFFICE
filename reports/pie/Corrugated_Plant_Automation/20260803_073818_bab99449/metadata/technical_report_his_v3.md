# HIS V3 Technical Report

- Run ID: 20260803_073818_bab99449
- Source: C:\Users\Inaki Senar\Documents\GitHub\IS-BACKOFFICE\reports\pie\Corrugated_Plant_Automation\20260803_073818_bab99449\source\Corrugated Plant Automation Solutions v2.pptx
- Pipeline: HIS V3 Production Ready
- Selected Variant: slide_flow
- Executive Quality Score: 98.5
- Visual Similarity Score: 100.0

## Phase Timing
- phase_1_document_discovery_attempt_1: 0.741 s
- phase_2_object_extraction_attempt_1: 1.938 s
- phase_3_image_extraction_attempt_1: 0.0 s
- phase_4_semantic_classification_attempt_1: 0.013 s
- phase_5_dom_reconstruction_attempt_1: 0.011 s
- phase_6_theme_application_attempt_1: 0.013 s
- phase_7_validation_publication_attempt_1: 6.236 s
- phase_1_document_discovery_attempt_2: 0.294 s
- phase_2_object_extraction_attempt_2: 3.287 s
- phase_3_image_extraction_attempt_2: 0.0 s
- phase_4_semantic_classification_attempt_2: 0.028 s
- phase_5_dom_reconstruction_attempt_2: 0.008 s
- phase_6_theme_application_attempt_2: 0.001 s
- phase_7_validation_publication_attempt_2: 14.049 s

## Hypotheses
- H1: Strict structure-first reconstruction | score=8.61
- H2: Balanced semantic-first reconstruction | score=8.16
- H3: Visual-priority reconstruction | score=7.63
- Selected: H1 (Strict structure-first reconstruction)

## Discovery
- Slides: 29
- Master Slides: 1
- Layouts: 11
- Hyperlinks: 0
- Notes Slides: 1

## Object Inventory
- Total Objects: 103
- heading: 21
- shape: 57
- text: 16
- title: 9

## Images
- Total Images: 0
- Deduplicated Images: 0

## Quality Gates
### slide_flow
- Passed: False
- Components reconstructed: 29
- text_coverage: 100.0
- image_coverage: 100.0
- diagram_coverage: 100.0
- smartart_coverage: 100.0
- theme_compliance: 100.0
- accessibility: 85.0
- responsive: 100.0
- typography: 100.0
- layout_quality: 100.0
- visual_similarity: 100.0
### smart_reconstruction
- Passed: False
- Components reconstructed: 29
- text_coverage: 100.0
- image_coverage: 100.0
- diagram_coverage: 100.0
- smartart_coverage: 100.0
- theme_compliance: 100.0
- accessibility: 85.0
- responsive: 100.0
- typography: 100.0
- layout_quality: 100.0
- visual_similarity: 100.0

## Risks Detected
- Multiple regeneration attempts were needed; source complexity may impact deterministic quality.
- No images detected in source; visual fidelity relies on text/layout only.

## Suggested Improvements
- Add source-type-specific extraction adapters for complex diagrams.
- Enable OCR/vision fallback to recover embedded rasterized visuals.
