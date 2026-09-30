import pytest

from governed_agent.tools import ToolExecutionError, build_default_tools


def test_artifact_writer_rejects_workspace_escape(tmp_path):
    tools = build_default_tools(tmp_path / "workspace")
    with pytest.raises(ToolExecutionError, match="path escapes workspace"):
        tools.execute("artifact.write", {"path": "../escape.txt", "content": "blocked"})
    assert not (tmp_path / "escape.txt").exists()
