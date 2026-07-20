# Platform Registry

Utilities to load a discovery registry produced by `tools/discovery/discover_platform.py`, build a capability registry and produce simple inventory reports.

Usage:

1. Run discovery:

```
& ".venv/Scripts/python.exe" tools/discovery/discover_platform.py --root .
```

2. Ingest into capability registry:

```
& ".venv/Scripts/python.exe" platform_registry/ingest.py
```
