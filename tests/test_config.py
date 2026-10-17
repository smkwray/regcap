from regcap.config import validate_config
from regcap import validation


def test_validate_config_accepts_scaffold():
    messages = validate_config()

    assert any("5 mechanisms" in message for message in messages)
    assert any("sibling source contracts" in message for message in messages)


def test_validate_package_allows_local_environment(tmp_path, monkeypatch):
    (tmp_path / ".venv").mkdir()
    monkeypatch.setattr(validation, "PROJECT_ROOT", tmp_path)

    messages = validation.validate_package()

    assert any("5 mechanisms" in message for message in messages)
