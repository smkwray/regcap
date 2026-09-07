from regcap.config import validate_config


def test_validate_config_accepts_scaffold():
    messages = validate_config()

    assert any("5 mechanisms" in message for message in messages)
    assert any("sibling source contracts" in message for message in messages)
