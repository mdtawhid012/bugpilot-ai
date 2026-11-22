import csv
import hmac
import os
import re
import stat
import subprocess
import sys
from pathlib import Path


def csrf_token_matches(expected: str, provided: str) -> bool:
    return bool(expected) and hmac.compare_digest(expected, provided)


def ensure_private_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink() or not path.is_dir():
        raise RuntimeError("BugPilot data directory must be a real directory")
    if sys.platform == "win32":
        _set_windows_acl(path, is_directory=True)
        return
    os.chmod(path, 0o700)
    info = path.stat()
    if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise RuntimeError("BugPilot data directory is not owner-private")


def ensure_private_file(path: Path) -> None:
    if not path.exists():
        path.touch(mode=0o600)
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("BugPilot database must be a regular file")
    if sys.platform == "win32":
        _set_windows_acl(path, is_directory=False)
        return
    os.chmod(path, 0o600)
    info = path.stat()
    if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise RuntimeError("BugPilot database is not owner-private")


def _set_windows_acl(path: Path, is_directory: bool) -> None:
    system_root = os.environ.get("SystemRoot")
    if not system_root:
        raise RuntimeError("SystemRoot is required to verify BugPilot data permissions")
    system32 = Path(system_root) / "System32"
    identity = subprocess.run(
        [str(system32 / "whoami.exe"), "/user", "/fo", "csv", "/nh"],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    identity_rows = list(csv.reader(identity.stdout.splitlines()))
    if not identity_rows or len(identity_rows[0]) < 2 or not re.fullmatch(r"S-\d(?:-\d+)+", identity_rows[0][-1]):
        raise RuntimeError("Could not identify the current Windows user SID")
    user_name = identity_rows[0][0].casefold()
    user_sid = identity_rows[0][-1]
    inheritance = "(OI)(CI)F" if is_directory else "F"
    grants = [f"*{user_sid}:{inheritance}", f"*S-1-5-18:{inheritance}"]
    icacls = str(system32 / "icacls.exe")
    subprocess.run(
        [icacls, str(path), "/inheritance:r", "/grant:r", *grants],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    output = subprocess.run(
        [icacls, str(path)], check=True, capture_output=True, text=True, timeout=5
    ).stdout
    principals = set()
    expected_rights = "(OI)(CI)(F)" if is_directory else "(F)"
    for line in output.splitlines():
        if ":(" not in line:
            continue
        principal_entry = line[len(str(path)) :].strip() if line.startswith(str(path)) else line.strip()
        principal, separator, rights = principal_entry.partition(":")
        if not separator or rights != expected_rights:
            raise RuntimeError("BugPilot data ACL contains unexpected access rights")
        principals.add(principal.lstrip("*").casefold())
    allowed_principals = {
        frozenset({user_name, "nt authority\\system"}),
        frozenset({user_sid.casefold(), "s-1-5-18"}),
        frozenset({user_name, "s-1-5-18"}),
        frozenset({user_sid.casefold(), "nt authority\\system"}),
    }
    if frozenset(principals) not in allowed_principals:
        raise RuntimeError("BugPilot data ACL is not limited to the current user and SYSTEM")