from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backoffice.his.repository_adapters import (
    AIFactoryRepositoryAdapter,
    IngesiteRepositoryAdapter,
    RepositoryAdapterError,
)


class TestHISRepositoryAdapters(unittest.TestCase):
    def test_snapshot_detects_dependency_change_and_blocks_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ai-factory"
            source = root / "data" / "result.json"
            source.parent.mkdir(parents=True)
            source.write_text('{"result": 1}', encoding="utf-8")
            outside = Path(tmp) / "outside.json"
            outside.write_text("{}", encoding="utf-8")
            adapter = AIFactoryRepositoryAdapter(root)

            dependency = adapter.snapshot("data/result.json")
            self.assertEqual(dependency.repository_id, "ai_factory")
            self.assertFalse(adapter.is_stale(dependency))

            source.write_text('{"result": 2}', encoding="utf-8")
            self.assertTrue(adapter.is_stale(dependency))
            with self.assertRaises(RepositoryAdapterError):
                adapter.snapshot("../outside.json")

    def test_ingesite_only_accepts_external_staging_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "ingesite"
            root.mkdir()
            staging = base / "publishing" / "ingesite_staging"
            adapter = IngesiteRepositoryAdapter(root, staging)

            accepted = adapter.validate_sync_destination(staging / "mission-1" / "index.html")
            self.assertTrue(str(accepted).startswith(str(staging.resolve())))
            with self.assertRaises(RepositoryAdapterError):
                adapter.validate_sync_destination(root / "index.html")
            with self.assertRaises(RepositoryAdapterError):
                adapter.validate_sync_destination(base / "other" / "index.html")

    def test_ingesite_rejects_staging_inside_source_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ingesite"
            root.mkdir()
            with self.assertRaises(RepositoryAdapterError):
                IngesiteRepositoryAdapter(root, root / "staging")


if __name__ == "__main__":
    unittest.main()
