from __future__ import annotations

from pathlib import Path

REPORT_PUBLISHER_AGENT = "report_publisher_agent"


def is_final_report_path(path: str | Path) -> bool:
    """Return True when path is under reports/<project>/final/."""
    p = Path(path)
    parts = [part.lower() for part in p.parts]
    for idx, part in enumerate(parts):
        if part == "reports" and idx + 2 < len(parts):
            if parts[idx + 2] == "final":
                return True
    return False


def assert_can_write(path: str | Path, agent_name: str) -> None:
    """Enforce that only the publisher agent can write to reports/<project>/final/."""
    if is_final_report_path(path) and agent_name != REPORT_PUBLISHER_AGENT:
        raise PermissionError(
            f"Write blocked by policy: only '{REPORT_PUBLISHER_AGENT}' can write to reports/<project>/final/."
        )


def get_isolated_workspace(repo_root: str | Path, project: str, agent_name: str) -> Path:
    """Return and create the isolated workspace path for a non-publisher agent."""
    root = Path(repo_root)
    workspace = root / "reports" / project / "workspaces" / agent_name
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace
