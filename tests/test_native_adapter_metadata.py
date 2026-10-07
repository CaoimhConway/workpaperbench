import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def test_run_metadata_checks_actual_corrected_adapter_before_provider_access(tmp_path, monkeypatch):
    import hashlib
    import fix_native_version as fix
    import native_run
    import pytest
    path = tmp_path / 'hermes.py'
    path.write_bytes(b'corrected pinned adapter fixture')
    monkeypatch.setattr(fix, 'CORRECTED_MODULE_SHA256', hashlib.sha256(path.read_bytes()).hexdigest())
    metadata = native_run.native_version_fix_metadata(path)
    assert metadata['corrected_module_sha256'] == fix.CORRECTED_MODULE_SHA256
    assert metadata['checked_before_provider_access'] is True
    path.write_bytes(b'unexpected adapter bytes')
    with pytest.raises(ValueError, match='native_corrected_module_mismatch'):
        native_run.native_version_fix_metadata(path)
