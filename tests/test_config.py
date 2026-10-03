from app.config.config import _read_secret


def test_read_secret_from_file(tmp_path):
    secret = tmp_path / "secret_key"
    secret.write_text("abc123\n")
    assert _read_secret(str(secret)) == "abc123"


def test_read_secret_missing_or_empty(tmp_path):
    empty = tmp_path / "empty"
    empty.write_text("")
    assert _read_secret(None) is None
    assert _read_secret(str(tmp_path / "missing")) is None
    assert _read_secret(str(empty)) is None
