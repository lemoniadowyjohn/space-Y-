from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .models import ToolResult, ToolRisk


class ToolExecutionError(RuntimeError):
    pass


class ToolAuthorizationError(RuntimeError):
    pass


ToolFn = Callable[[dict], ToolResult]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    fn: ToolFn
    risk: ToolRisk
    side_effecting: bool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(
        self,
        name: str,
        fn: ToolFn,
        *,
        risk: ToolRisk = ToolRisk.LOW,
        side_effecting: bool = False,
    ) -> None:
        self._tools[name] = ToolSpec(name=name, fn=fn, risk=risk, side_effecting=side_effecting)

    def spec(self, name: str) -> ToolSpec:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolExecutionError(f"unknown tool: {name}") from exc

    def authorize(self, name: str, allowed_tools: tuple[str, ...]) -> ToolSpec:
        spec = self.spec(name)
        if name not in allowed_tools:
            raise ToolAuthorizationError(f"tool not in task allowlist: {name}")
        return spec

    def execute(self, name: str, arguments: dict) -> ToolResult:
        spec = self.spec(name)
        try:
            result = spec.fn(arguments)
        except Exception as exc:
            raise ToolExecutionError(str(exc)) from exc
        if not result.ok:
            raise ToolExecutionError(str(result.output.get("error", "tool failed")))
        return result


def build_default_tools(workspace: Path) -> ToolRegistry:
    workspace.mkdir(parents=True, exist_ok=True)
    registry = ToolRegistry()

    def write_artifact(arguments: dict) -> ToolResult:
        relative_path = str(arguments.get("path", "result.txt"))
        content = str(arguments.get("content", ""))
        target = (workspace / relative_path).resolve()
        if workspace.resolve() not in target.parents and target != workspace.resolve():
            raise ValueError("path escapes workspace")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return ToolResult(
            ok=True,
            output={"bytes_written": target.stat().st_size},
            artifact_paths=(str(target),),
        )

    def read_artifact(arguments: dict) -> ToolResult:
        relative_path = str(arguments.get("path", "result.txt"))
        target = (workspace / relative_path).resolve()
        if workspace.resolve() not in target.parents and target != workspace.resolve():
            raise ValueError("path escapes workspace")
        return ToolResult(ok=True, output={"content": target.read_text(encoding="utf-8")})

    def fail_tool(arguments: dict) -> ToolResult:
        return ToolResult(ok=False, output={"error": arguments.get("message", "simulated failure")})

    registry.register("artifact.read", read_artifact, risk=ToolRisk.READ_ONLY, side_effecting=False)
    registry.register("artifact.write", write_artifact, risk=ToolRisk.MEDIUM, side_effecting=True)
    registry.register("tool.fail", fail_tool, risk=ToolRisk.LOW, side_effecting=False)
    return registry
