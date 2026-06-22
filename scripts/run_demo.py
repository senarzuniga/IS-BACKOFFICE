import argparse
import os
import sys
# Ensure repo root is on sys.path when running scripts directly
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agents.competitive_intelligence.orchestrator import run_job


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--company", "-c", required=True)
    p.add_argument("--no-web", action="store_true", help="Skip web scraping and run demo with local baseline data")
    p.add_argument("--seed", "-s", nargs="*", help="Seed URLs")
    args = p.parse_args()

    res = run_job(args.company, seeds=args.seed or [], no_web=args.no_web)
    print("Report:", res.get("report"))


if __name__ == '__main__':
    main()
