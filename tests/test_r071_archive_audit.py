from pathlib import Path

from scripts.r071.audit_r071_archive import audit


ROOT = Path(__file__).resolve().parents[1]


def test_archive_audit_reports_unresolved_author_metadata():
    report = audit(ROOT)
    findings = {finding["id"]: finding for finding in report["findings"]}
    assert report["required_audit_input_count"] == 24
    assert findings["D-02"]["severity"] == "pass"
    assert findings["D-01-CFF"]["severity"] == "blocker"
    assert any("Missing software authors" in item for item in findings["D-01-CFF"]["details"])
    assert report["blocker_count"] == 1


def test_archive_audit_confirms_legacy_scripts_removed():
    report = audit(ROOT)
    legacy = next(finding for finding in report["findings"] if finding["id"] == "D-01-LEGACY")
    assert legacy["severity"] == "pass"
    assert legacy["details"] == []
