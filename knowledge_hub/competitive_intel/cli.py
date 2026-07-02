"""Simple CLI entrypoints (scaffold only).

The CLI exposes commands that print what they would do. They DO NOT
perform network crawling or indexing. This file is useful for manual
integration testing and as example invocation points.
"""

import argparse


def main():
    p = argparse.ArgumentParser(prog='ci-engine')
    sub = p.add_subparsers(dest='cmd')

    sub.add_parser('scaffold', help='Print scaffold info (no actions)')
    dry = sub.add_parser('dry-run', help='Perform a dry-run using mock data')
    dry.add_argument('--company', default='TestCo')

    args = p.parse_args()
    if args.cmd == 'scaffold':
        print('Scaffold OK: no external actions performed')
    elif args.cmd == 'dry-run':
        print(f"Dry-run requested for company: {getattr(args, 'company', 'TestCo')}")
        print('Note: dry-run uses only placeholder data and does not index real sources')
    else:
        p.print_help()


if __name__ == '__main__':
    main()
