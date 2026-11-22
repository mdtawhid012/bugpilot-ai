from dataclasses import dataclass
import hashlib
import os
import re
import stat
from pathlib import Path, PurePosixPath
from typing import Any

from app.core.errors import NotFoundError


@dataclass(frozen=True)
class Fixture:
    id: str
    title: str
    language: str
    revision: str
    source_ref: dict[str, Any] | None = None


class FixtureService:
    def __init__(self, fixtures: tuple[Fixture, ...]) -> None:
        fixture_ids = [fixture.id for fixture in fixtures]
        if len(fixture_ids) != len(set(fixture_ids)):
            raise ValueError("Fixture IDs must be unique")
        for fixture in fixtures:
            self._validate_source_ref(fixture.source_ref)
        self._fixtures = {fixture.id: fixture for fixture in fixtures}

    def get(self, fixture_id: str) -> Fixture:
        fixture = self._fixtures.get(fixture_id)
        if fixture is None:
            raise NotFoundError("unknown_fixture", "The requested fixture is not available")
        return fixture

    def list(self) -> list[Fixture]:
        return list(self._fixtures.values())

    @staticmethod
    def _validate_source_ref(source_ref: dict[str, Any] | None) -> None:
        if source_ref is None:
            return
        path = source_ref.get("path")
        if not isinstance(path, str) or "\\" in path:
            raise ValueError("Fixture source paths must be repository-relative POSIX paths")
        parsed_path = PurePosixPath(path)
        if (
            parsed_path.is_absolute()
            or not parsed_path.parts
            or parsed_path.parts[0] != "fixtures"
            or any(part in {".", ".."} for part in parsed_path.parts)
        ):
            raise ValueError("Fixture source path escapes the repository root")
        if not isinstance(source_ref.get("revision"), str):
            raise ValueError("Fixture source revision is required")
        if type(source_ref.get("line_start")) is not int or type(source_ref.get("line_end")) is not int:
            raise ValueError("Fixture source line numbers must be integers")
        if source_ref["line_start"] < 1 or source_ref["line_end"] < source_ref["line_start"]:
            raise ValueError("Fixture source line range is invalid")
        if not isinstance(source_ref.get("content_hash"), str) or not re.fullmatch(
            r"[0-9a-f]{64}", source_ref["content_hash"]
        ):
            raise ValueError("Fixture source content hash must be a SHA-256 digest")

    def read_source(self, fixture_id: str) -> tuple[Fixture, dict[str, Any], str]:
        fixture = self.get(fixture_id)
        source_ref = fixture.source_ref
        if source_ref is None:
            raise ValueError("Fixture source reference is unavailable")

        repository_root = Path(__file__).resolve().parents[3]
        fixture_root = (repository_root / "fixtures").resolve(strict=True)
        source_path = (repository_root / source_ref["path"]).resolve(strict=True)
        try:
            source_path.relative_to(fixture_root)
        except ValueError as error:
            raise ValueError("Fixture source escapes the curated fixture root") from error

        for parent in source_path.parents:
            if parent == fixture_root:
                break
            if parent.is_symlink():
                raise ValueError("Fixture source parent is a symlink")
        if source_path.is_symlink():
            raise ValueError("Fixture source is a symlink")
        if not stat.S_ISREG(os.lstat(source_path).st_mode):
            raise ValueError("Fixture source is not a regular file")

        data = source_path.read_bytes()
        if len(data) > 64 * 1024:
            raise ValueError("Fixture source exceeds the provider context limit")
        digest = hashlib.sha256(data).hexdigest()
        if digest != source_ref["content_hash"]:
            raise ValueError("Fixture source digest does not match the manifest")
        try:
            content = data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("Fixture source is not valid UTF-8") from error
        return fixture, source_ref, content