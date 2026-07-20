#!/usr/bin/env python3
"""CLI for quick queries against the Platform Registry"""
from __future__ import annotations

import argparse
from platform_registry.client import PlatformRegistryClient


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["list-capabilities", "find", "resolve"], help="Command")
    p.add_argument("arg", nargs="?", help="Argument for command")
    args = p.parse_args()

    client = PlatformRegistryClient()

    if args.cmd == "list-capabilities":
        for c in client.list_capabilities():
            print(c)

    elif args.cmd == "find":
        if not args.arg:
            print("Provide capability name")
            return
        objs = client.find_objects_by_capability(args.arg)
        for o in objs:
            print(f"{o['name']} — {o['path']}")

    elif args.cmd == "resolve":
        if not args.arg:
            print("Provide intent text in quotes")
            return
        res = client.resolve_capability_from_intent(args.arg)
        for r in res:
            print(f"{r['capability']} (score={r['score']}, count={r['count']})")


if __name__ == '__main__':
    main()
