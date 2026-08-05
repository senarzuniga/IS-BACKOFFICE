from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from report_publication_guard import REPORT_PUBLISHER_AGENT, assert_can_write

LOCK_RETRY_MS = 500
LOCK_MAX_RETRIES = 20


@dataclass
class PublishItem:
    source: Path
    target: Path
    expected_sha256: str | None = None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def acquire_lock(lock_path: Path) -> bool:
    retries = 0
    while retries < LOCK_MAX_RETRIES:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(str(os.getpid()))
            return True
        except FileExistsError:
            retries += 1
            time.sleep(LOCK_RETRY_MS / 1000.0)
    return False


def release_lock(lock_path: Path) -> None:
    try:
        lock_path.unlink(missing_ok=True)
    except Exception:
        pass


def atomic_replace(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as src_fp:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp", delete=False) as tmp_fp:
            shutil.copyfileobj(src_fp, tmp_fp)
            tmp_name = tmp_fp.name

    tmp_path = Path(tmp_name)
    # fs-level atomic swap on same filesystem
    os.replace(str(tmp_path), str(target))


def parse_manifest(path: Path) -> list[PublishItem]:
    # PowerShell Set-Content may emit UTF-8 BOM on some environments.
    payload: Any = json.loads(path.read_text(encoding="utf-8-sig"))
    items_raw = payload if isinstance(payload, list) else payload.get("items", [])
    items: list[PublishItem] = []
    for raw in items_raw:
        items.append(
            PublishItem(
                source=Path(raw["source"]),
                target=Path(raw["target"]),
                expected_sha256=raw.get("sha256"),
            )
        )
    return items


def parse_item(value: str) -> PublishItem:
    # format: source::target[::sha256]
    parts = value.split("::")
    if len(parts) < 2:
        raise ValueError(f"Invalid --item format: {value}")
    source = Path(parts[0])
    target = Path(parts[1])
    checksum = parts[2] if len(parts) > 2 and parts[2] else None
    return PublishItem(source=source, target=target, expected_sha256=checksum)


def publish_items(items: list[PublishItem], agent_name: str) -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    for item in items:
        item_result: dict[str, Any] = {
            "source": str(item.source),
            "target": str(item.target),
            "status": "pending",
            "warning": None,
            "error": None,
            "sha256": None,
        }

        try:
            assert_can_write(item.target, agent_name)

            if not item.source.exists() or not item.source.is_file():
                item_result["status"] = "error"
                item_result["error"] = "Source file not found"
                results.append(item_result)
                continue

            source_hash = sha256_file(item.source)
            item_result["sha256"] = source_hash

            if item.expected_sha256 and source_hash.lower() != item.expected_sha256.lower():
                item_result["status"] = "error"
                item_result["error"] = "Checksum mismatch"
                results.append(item_result)
                continue

            lock_path = item.target.with_suffix(item.target.suffix + ".lock")
            locked = acquire_lock(lock_path)
            if not locked:
                item_result["status"] = "warning"
                item_result["warning"] = (
                    f"Target locked after {LOCK_MAX_RETRIES} retries ({LOCK_RETRY_MS}ms each). Skipped."
                )
                results.append(item_result)
                continue

            try:
                atomic_replace(item.source, item.target)
            finally:
                release_lock(lock_path)

            published_hash = sha256_file(item.target)
            if published_hash != source_hash:
                item_result["status"] = "error"
                item_result["error"] = "Post-publish checksum verification failed"
            else:
                item_result["status"] = "published"

        except PermissionError as ex:
            item_result["status"] = "error"
            item_result["error"] = str(ex)
        except Exception as ex:
            item_result["status"] = "error"
            item_result["error"] = str(ex)

        results.append(item_result)

    summary = {
        "published": sum(1 for r in results if r["status"] == "published"),
        "warnings": sum(1 for r in results if r["status"] == "warning"),
        "errors": sum(1 for r in results if r["status"] == "error"),
        "results": results,
    }
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report Publisher Agent: policy-enforced publish to reports/<project>/final/ with lock, checksum and atomic replace."
    )
    parser.add_argument("--agent-name", default=REPORT_PUBLISHER_AGENT, help="Agent identity. Must be report_publisher_agent for final writes.")
    parser.add_argument("--manifest", type=Path, help="JSON file with items [{source,target,sha256?}] or {items:[...]}")
    parser.add_argument("--item", action="append", default=[], help="Single publish item: source::target[::sha256]")
    parser.add_argument("--output", type=Path, help="Optional path to write publish result JSON")
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    items: list[PublishItem] = []
    if args.manifest:
        items.extend(parse_manifest(args.manifest))
    for raw_item in args.item:
        items.append(parse_item(raw_item))

    if not items:
        parser.error("No publish items provided. Use --manifest or --item.")

    summary = publish_items(items=items, agent_name=args.agent_name)
    output_text = json.dumps(summary, ensure_ascii=False, indent=2)
    print(output_text)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_text, encoding="utf-8")

    # non-zero on hard errors only
    return 1 if summary["errors"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
