#!/usr/bin/env python3
"""Find large blob objects in git history.

Usage: python scripts/find_large_git_objects.py --threshold-mb 100
"""
import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--threshold-mb', type=int, default=100)
    args = parser.parse_args()
    threshold = args.threshold_mb * 1024 * 1024

    # get all objects with paths
    p = subprocess.run(['git', 'rev-list', '--objects', '--all'], capture_output=True, text=True)
    if p.returncode != 0:
        print('git rev-list failed', file=sys.stderr)
        sys.exit(1)

    lines = p.stdout.strip().splitlines()
    hash_to_path = {}
    hashes = []
    for line in lines:
        parts = line.split(' ', 1)
        if len(parts) == 2:
            h, path = parts
            hash_to_path[h] = path
            hashes.append(h)

    if not hashes:
        print('No objects found')
        return

    # call git cat-file --batch-check
    proc = subprocess.Popen(['git', 'cat-file', '--batch-check=%(objectname) %(objecttype) %(objectsize)'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    stdin = '\n'.join(hashes)
    out, _ = proc.communicate(stdin)
    results = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            h, typ, size = parts[0], parts[1], int(parts[2])
            if typ == 'blob' and size >= threshold:
                results.append((h, size, hash_to_path.get(h, '(no-path)')))

    if not results:
        print(f'No blobs >= {args.threshold_mb} MB found in git history.')
        return

    results.sort(key=lambda x: x[1], reverse=True)
    for h, size, path in results:
        print(f'{path}\t{size}\t{h}')


if __name__ == '__main__':
    main()
