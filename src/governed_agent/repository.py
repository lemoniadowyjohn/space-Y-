from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


class RepositoryCheckError(RuntimeError):
    pass


@dataclass(frozen=True)
class RepositoryState:
    root: str
    commit: str
    dirty: bool
    changed_entries: tuple[str, ...]


def capture_repository_state(path: str | Path) -> RepositoryState:
    """Capture a small, local Git state snapshot for verification-oriented tasks."""
    root = Path(path).resolve()

    def git(*args: str) -> str:
        try:
            completed = subprocess.run(
                ["git", "-C", str(root), *args],
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            raise RepositoryCheckError(f"unable to inspect git repository: {root}") from exc
        return completed.stdout.strip()

    if git("rev-parse", "--is-inside-work-tree") != "true":
        raise RepositoryCheckError(f"not a git working tree: {root}")

    commit = git("rev-parse", "HEAD")
    changed = tuple(line for line in git("status", "--porcelain").splitlines() if line)
    return RepositoryState(
        root=str(root),
        commit=commit,
        dirty=bool(changed),
        changed_entries=changed,
    )
