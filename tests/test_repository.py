import subprocess

from governed_agent.repository import capture_repository_state


def test_repository_state_detects_clean_and_dirty(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "demo@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Portfolio Demo"], check=True)
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("v1", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "tracked.txt"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-qm", "init"], check=True)

    clean = capture_repository_state(tmp_path)
    assert clean.dirty is False
    assert len(clean.commit) == 40

    tracked.write_text("v2", encoding="utf-8")
    dirty = capture_repository_state(tmp_path)
    assert dirty.dirty is True
    assert dirty.changed_entries
