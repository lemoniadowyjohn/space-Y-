from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]

SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_pat": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "openai_like": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "slack_token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
}

TEXT_SUFFIXES = {".py", ".md", ".toml", ".yml", ".yaml", ".json", ".txt", ".example"}


def run(command: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True)


def scan_secrets() -> list[dict]:
    findings: list[dict] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", ".venv", ".pytest_cache", "__pycache__"} for part in path.parts):
            continue
        if path.suffix not in TEXT_SUFFIXES and path.name not in {"Dockerfile", ".gitignore"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append({"pattern": name, "file": str(path.relative_to(ROOT))})
    return findings


def main() -> int:
    checks: dict[str, dict] = {}

    tests = run([sys.executable, "-m", "pytest", "-q"])
    checks["tests"] = {
        "pass": tests.returncode == 0,
        "detail": tests.stdout.strip() or tests.stderr.strip(),
    }

    demo_results = {}
    with tempfile.TemporaryDirectory(prefix="governed-agent-demo-") as tmp:
        for scenario in ("success", "fallback", "approval"):
            completed = run(
                [
                    sys.executable,
                    "-m",
                    "governed_agent.demo",
                    "--scenario",
                    scenario,
                    "--workspace",
                    str(Path(tmp) / scenario),
                ]
            )
            parsed = None
            try:
                parsed = json.loads(completed.stdout)
            except json.JSONDecodeError:
                pass
            demo_results[scenario] = {
                "pass": completed.returncode == 0
                and parsed is not None
                and parsed["record"]["status"] == "complete"
                and parsed["audit_integrity"] is True,
                "status": parsed["record"]["status"] if parsed else None,
                "audit_integrity": parsed.get("audit_integrity") if parsed else None,
            }
    checks["demos"] = {"pass": all(v["pass"] for v in demo_results.values()), "detail": demo_results}

    secret_findings = scan_secrets()
    checks["secret_scan"] = {"pass": not secret_findings, "detail": secret_findings}

    required_docs = [
        "README.md",
        "PORTFOLIO_REVIEW.md",
        "AI_PORTFOLIO_CV_BLOCK.md",
        "docs/ARCHITECTURE.md",
        "docs/CAPABILITY_MATRIX.md",
        "docs/AI_PORTFOLIO_STRENGTHENING_TASKS.md",
        "docs/THREAT_MODEL.md",
    ]
    missing_docs = [name for name in required_docs if not (ROOT / name).exists()]
    checks["required_docs"] = {"pass": not missing_docs, "detail": missing_docs}

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    boundary_terms = ["prototype", "not", "production", "limitations"]
    checks["scope_boundary"] = {
        "pass": all(term.lower() in readme.lower() for term in boundary_terms),
        "detail": "README states prototype/production limitations" if all(term.lower() in readme.lower() for term in boundary_terms) else "boundary wording missing",
    }

    passed = all(item["pass"] for item in checks.values())
    report = {"verdict": "PORTFOLIO READY" if passed else "NOT READY", "checks": checks}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
