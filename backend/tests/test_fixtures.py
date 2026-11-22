import hashlib
import unittest
from pathlib import Path

from app.application import DEFAULT_FIXTURES
from app.services.fixture_service import Fixture, FixtureService


class FixtureServiceTests(unittest.TestCase):
    def test_curated_source_reference_matches_fixture_digest(self) -> None:
        fixture = DEFAULT_FIXTURES[0]
        repository_root = Path(__file__).resolve().parents[2]
        source_path = repository_root / fixture.source_ref["path"]
        digest = hashlib.sha256(source_path.read_bytes()).hexdigest()

        self.assertEqual(digest, fixture.source_ref["content_hash"])

    def test_fixture_manifest_rejects_paths_that_escape_or_leave_fixture_root(self) -> None:
        invalid_paths = ("../secret", "docs/secret.md", "/etc/passwd", "fixtures\\secret.py")
        for path in invalid_paths:
            with self.subTest(path=path):
                source_ref = {
                    "path": path,
                    "line_start": 1,
                    "line_end": 1,
                    "revision": "test-revision",
                    "content_hash": "0" * 64,
                }
                with self.assertRaises(ValueError):
                    FixtureService((Fixture("unsafe", "Unsafe", "python", "test-revision", source_ref),))