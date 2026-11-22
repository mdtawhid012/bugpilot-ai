import os
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


def default_data_directory() -> Path:
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if not local_app_data:
            raise RuntimeError("LOCALAPPDATA is required for private BugPilot data")
        return Path(local_app_data) / "BugPilotAI" / "prototype"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "BugPilotAI" / "prototype"
    data_home = os.environ.get("XDG_DATA_HOME")
    return (Path(data_home) if data_home else Path.home() / ".local" / "share") / "bugpilot-ai" / "prototype"


@dataclass(frozen=True)
class Settings:
    data_directory: Path
    ui_origin: str = "http://127.0.0.1:3000"
    api_port: int = 8000
    coordinator_capacity: int = 4
    event_page_limit: int = 100

    @property
    def allowed_hosts(self) -> frozenset[str]:
        return frozenset({f"127.0.0.1:{self.api_port}", f"[::1]:{self.api_port}"})

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            data_directory=default_data_directory(),
            ui_origin=os.environ.get("BUGPILOT_UI_ORIGIN", "http://127.0.0.1:3000"),
            api_port=int(os.environ.get("BUGPILOT_API_PORT", "8000")),
            coordinator_capacity=int(os.environ.get("BUGPILOT_COORDINATOR_CAPACITY", "4")),
        )

    def validate(self) -> None:
        if not 1 <= self.api_port <= 65535:
            raise ValueError("API port must be between 1 and 65535")
        if self.coordinator_capacity < 1:
            raise ValueError("Coordinator capacity must be positive")
        if self.event_page_limit < 1:
            raise ValueError("Event page limit must be positive")
        origin = urlsplit(self.ui_origin)
        if (
            origin.scheme != "http"
            or origin.hostname not in {"127.0.0.1", "::1"}
            or origin.port is None
            or not 1 <= origin.port <= 65535
            or origin.path
            or origin.query
            or origin.fragment
            or origin.username
            or origin.password
            or self.ui_origin.endswith("/")
        ):
            raise ValueError("UI origin must be an exact loopback HTTP origin")
        data_path = self.data_directory.resolve()
        repository_root = Path(__file__).resolve().parents[3]
        if _is_within(data_path, repository_root):
            raise ValueError("BugPilot data must be outside the repository")
        for variable in ("OneDrive", "OneDriveCommercial", "OneDriveConsumer"):
            synced_root = os.environ.get(variable)
            if synced_root and _is_within(data_path, Path(synced_root).resolve()):
                raise ValueError("BugPilot data must be outside synced folders")


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False