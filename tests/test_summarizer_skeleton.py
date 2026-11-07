from __future__ import annotations

import json
from pathlib import Path

from summarizer.handler import handler

EVENT = Path(__file__).resolve().parents[1] / "events" / "summarize.json"


def test_sample_event_matches_contract(capsys):
    event = json.loads(EVENT.read_text(encoding="utf-8"))
    assert handler(event, None) == {"batchItemFailures": []}
    log = json.loads(capsys.readouterr().out.strip())
    assert log == {
        "fn": "summarizer",
        "event": "received",
        "board_id": "cse_notice",
        "post_id": 1234,
    }
