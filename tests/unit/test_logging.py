import json
import logging

from app.logging import configure_logging, get_logger


def test_logger_emits_json(capsys):
    configure_logging("INFO")
    log = get_logger("test")
    log.info("hello", foo="bar")
    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip().splitlines()[-1])
    assert payload["event"] == "hello"
    assert payload["foo"] == "bar"
    assert payload["level"] == "info"
