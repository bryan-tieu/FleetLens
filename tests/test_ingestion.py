import json
from hashlib import sha256

import pytest

from fleetlens.cli import main
from fleetlens.ingestion import jsonl as ingestion_jsonl
from fleetlens.ingestion import read_snapshot
from fleetlens.ingestion.cli import main as validate_main


def _rewrite(directory, rows):
    payload = b"".join(json.dumps(row, sort_keys=True).encode() + b"\n" for row in rows)
    (directory / "samples.jsonl").write_bytes(payload)
    manifest = json.loads((directory / "manifest.json").read_text())
    manifest["sample_count"] = len(rows)
    manifest["sha256_samples_jsonl"] = sha256(payload).hexdigest()
    (directory / "manifest.json").write_text(json.dumps(manifest))


def test_fixture_round_trip_and_repeatable_read(tmp_path):
    assert main(["--output", str(tmp_path), "--fixture"]) == 0
    result = read_snapshot(tmp_path)
    assert result == read_snapshot(tmp_path)
    assert result.input_rows == 11
    assert len(result.samples) == 11
    assert not result.rejected
    assert len({sample.sample_key for sample in result.samples}) == 11
    assert all(
        sample.provenance.origin.value == "synthetic" for sample in result.samples
    )


def test_bad_rows_are_quarantined_and_accounted_for(tmp_path):
    main(["--output", str(tmp_path), "--fixture"])
    rows = [
        json.loads(line)
        for line in (tmp_path / "samples.jsonl").read_text().splitlines()
    ]
    rows[1]["speed_mps"] = -1
    rows[2]["provenance"]["snapshot_id"] = "another-snapshot"
    rows[3] = rows[0].copy()
    rows[4]["unexpected"] = 1
    _rewrite(tmp_path, rows)
    result = read_snapshot(tmp_path)
    assert result.input_rows == len(result.samples) + len(result.rejected) == 11
    assert [item.line_number for item in result.rejected] == [2, 3, 4, 5]
    assert "speed_mps" in result.rejected[0].reason
    assert "snapshot_id" in result.rejected[1].reason
    assert "duplicate sample_key" in result.rejected[2].reason
    assert "v1 fields" in result.rejected[3].reason


def test_bad_json_is_quarantined_without_raw_payload(tmp_path):
    main(["--output", str(tmp_path), "--fixture"])
    payload = (tmp_path / "samples.jsonl").read_bytes()
    lines = payload.splitlines()
    lines[0] = b'{"secret":"private", invalid}'
    changed = b"\n".join(lines) + b"\n"
    (tmp_path / "samples.jsonl").write_bytes(changed)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    manifest["sha256_samples_jsonl"] = sha256(changed).hexdigest()
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    result = read_snapshot(tmp_path)
    assert result.rejected[0].line_number == 1
    assert "private" not in result.rejected[0].reason


def test_quarantine_reasons_do_not_echo_bad_timestamp_or_field_name(tmp_path):
    main(["--output", str(tmp_path), "--fixture"])
    rows = [
        json.loads(line)
        for line in (tmp_path / "samples.jsonl").read_text().splitlines()
    ]
    rows[0]["event_time"] = "PRIVATE-GPS-LOCATIONZ"
    _rewrite(tmp_path, rows)
    result = read_snapshot(tmp_path)
    assert result.rejected[0].reason == "event_time must be a valid ISO UTC timestamp"
    assert "PRIVATE" not in result.rejected[0].reason

    payload = (tmp_path / "samples.jsonl").read_bytes()
    lines = payload.splitlines()
    lines[0] = b'{"PRIVATE-GPS-LOCATION": 1, "PRIVATE-GPS-LOCATION": 2}'
    changed = b"\n".join(lines) + b"\n"
    (tmp_path / "samples.jsonl").write_bytes(changed)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    manifest["sha256_samples_jsonl"] = sha256(changed).hexdigest()
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    result = read_snapshot(tmp_path)
    assert result.rejected[0].reason == "duplicate JSON field"


def test_unrecognized_validation_error_is_sanitized(tmp_path, monkeypatch):
    main(["--output", str(tmp_path), "--fixture"])

    def unsafe_error(**_kwargs):
        raise ValueError("PRIVATE-GPS-LOCATION")

    monkeypatch.setattr(ingestion_jsonl, "Provenance", unsafe_error)
    result = read_snapshot(tmp_path)
    assert result.rejected[0].reason == "invalid sample"
    assert "PRIVATE" not in result.rejected[0].reason


def test_manifest_hash_and_count_guard_snapshot(tmp_path):
    main(["--output", str(tmp_path), "--fixture"])
    with (tmp_path / "samples.jsonl").open("ab") as stream:
        stream.write(b"{}\n")
    with pytest.raises(ValueError, match="hash"):
        read_snapshot(tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    manifest["sha256_samples_jsonl"] = sha256(
        (tmp_path / "samples.jsonl").read_bytes()
    ).hexdigest()
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="sample_count"):
        read_snapshot(tmp_path)


@pytest.mark.parametrize(
    ("field", "unknown"),
    [
        ("source_schema_version", "wire-mph/v2"),
        ("normalization_version", "unknown/v99"),
    ],
)
def test_unsupported_wire_versions_reject_snapshot(tmp_path, field, unknown):
    main(["--output", str(tmp_path), "--fixture"])
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    manifest[field] = unknown
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match=f"unsupported {field}"):
        read_snapshot(tmp_path)


def test_validation_cli_writes_reconciled_report_and_quarantine(tmp_path):
    source = tmp_path / "source"
    output = tmp_path / "report"
    main(["--output", str(source), "--fixture"])
    rows = [
        json.loads(line) for line in (source / "samples.jsonl").read_text().splitlines()
    ]
    rows[0]["speed_mps"] = -1
    _rewrite(source, rows)
    assert validate_main(["--input", str(source), "--output", str(output)]) == 0
    report = json.loads((output / "validation.json").read_text())
    quarantine = [
        json.loads(line)
        for line in (output / "quarantine.jsonl").read_text().splitlines()
    ]
    assert report["input_rows"] == report["accepted_rows"] + report["rejected_rows"]
    assert (report["accepted_rows"], report["rejected_rows"]) == (10, 1)
    assert quarantine == [{"line_number": 1, "reason": "speed_mps must be nonnegative"}]
