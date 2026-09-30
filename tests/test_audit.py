import json

from governed_agent.audit import AuditTrail


def test_audit_hash_chain_detects_in_memory_tamper():
    trail = AuditTrail()
    trail.append("one", {"x": 1})
    trail.append("two", {"x": 2})
    assert trail.verify_integrity()
    trail.events[0].payload["x"] = 999
    assert not trail.verify_integrity()


def test_persisted_audit_reloads_and_verifies(tmp_path):
    path = tmp_path / "audit.jsonl"
    trail = AuditTrail(path)
    trail.append("one", {"x": 1})
    trail.append("two", {"x": 2})
    reloaded = AuditTrail(path)
    assert len(reloaded.events) == 2
    assert reloaded.verify_integrity()


def test_persisted_audit_detects_file_tamper(tmp_path):
    path = tmp_path / "audit.jsonl"
    trail = AuditTrail(path)
    trail.append("one", {"x": 1})
    trail.append("two", {"x": 2})
    rows = path.read_text(encoding="utf-8").splitlines()
    first = json.loads(rows[0])
    first["payload"]["x"] = 999
    rows[0] = json.dumps(first, sort_keys=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    assert not AuditTrail(path).verify_integrity()
