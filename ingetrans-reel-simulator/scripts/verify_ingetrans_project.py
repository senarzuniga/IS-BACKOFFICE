import os
import sys
import glob
import yaml

ROOT = os.path.join(os.path.dirname(__file__), '..')
ROOT = os.path.abspath(ROOT)

PHASES = {
    'FASE0': ['00_FIDELITY_FRAMEWORK.md'],
    'FASE1': ['01_ARCHITECTURE_REPORT.md'],
    'FASE2': ['02_SIMULATION_MODEL/*.md'],
    'FASE3': ['03_CONFIG_DATABASE/*.yaml'],
    'FASE4': ['04_LOGIC_ALGORITHMS/*.md'],
    'FASE5': ['07_SOFTWARE_ARCHITECTURE/*.md', '07_SOFTWARE_ARCHITECTURE/*.sql'],
    'FASE6': ['05_CALIBRATION_LEVELS/*.yaml', '06_SCENARIOS/*.yaml'],
    'FASE7': ['07_OUTPUTS/*'],
    'FASE8': ['08_FINAL/*']
}

errors = []
total_files = 0

for phase, patterns in PHASES.items():
    count = 0
    for p in patterns:
        full = os.path.join(ROOT, p)
        matches = glob.glob(full)
        count += len(matches)
        for m in matches:
            total_files += 1
            if m.endswith('.yaml') or m.endswith('.yml'):
                try:
                    with open(m, 'r', encoding='utf-8') as f:
                        yaml.safe_load(f)
                except Exception as e:
                    errors.append((m, str(e)))
    print(f'{phase}: {count} files')

print('Total files found:', total_files)
if errors:
    print('YAML errors:')
    for m, e in errors:
        print(m, e)
    sys.exit(2)

if total_files < 80:
    print('WARNING: Total files < 80')
    sys.exit(1)

print('Verification OK')
sys.exit(0)
