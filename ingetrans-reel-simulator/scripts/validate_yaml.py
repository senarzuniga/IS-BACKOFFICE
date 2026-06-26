#!/usr/bin/env python3
"""Validador sencillo de YAML para ingetrans-reel-simulator/03_CONFIG_DATABASE
Comprueba parseo y reglas básicas (includes en config_master.yaml, existencia de entity.name).
"""
import os
import glob
import sys

try:
    import yaml
except Exception as e:
    print('PyYAML no está disponible:', e)
    sys.exit(2)


def load_yaml_file(path):
    with open(path, 'r', encoding='utf-8') as fh:
        content = fh.read()
    try:
        return yaml.safe_load(content), None
    except Exception as e:
        return None, str(e)


def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_dir = os.path.join(base, '03_CONFIG_DATABASE')
    if not os.path.isdir(cfg_dir):
        print('DIRECTORY NOT FOUND:', cfg_dir)
        sys.exit(2)

    files = sorted(glob.glob(os.path.join(cfg_dir, '*.yaml')))
    print(f'Found {len(files)} YAML files in {cfg_dir}')

    errors = []
    parsed = {}

    for f in files:
        data, err = load_yaml_file(f)
        if err:
            errors.append((os.path.basename(f), f'YAML parse error: {err}'))
        else:
            parsed[os.path.basename(f)] = data

    # Validate config_master includes
    master = parsed.get('config_master.yaml')
    if master and isinstance(master, dict):
        includes = master.get('includes', [])
        if not isinstance(includes, list):
            errors.append(('config_master.yaml', 'includes must be a list'))
        else:
            missing = [inc for inc in includes if inc not in parsed]
            if missing:
                errors.append(('config_master.yaml', f'Missing includes referenced: {missing}'))

    # Basic per-file checks
    for fname, data in parsed.items():
        if fname == 'config_master.yaml':
            continue
        if not isinstance(data, dict):
            errors.append((fname, 'Top-level YAML is not a mapping'))
            continue
        ent = data.get('entity')
        if ent is None:
            errors.append((fname, "Missing 'entity' mapping"))
            continue
        if not isinstance(ent, dict) or 'name' not in ent:
            errors.append((fname, "Missing entity.name"))

    if errors:
        print('\nValidation errors:')
        for f, msg in errors:
            print(f'- {f}: {msg}')
        sys.exit(2)

    print('All YAML files parsed and basic validations passed.')
    sys.exit(0)


if __name__ == '__main__':
    main()
