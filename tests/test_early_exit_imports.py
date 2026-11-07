"""CLAUDE.md의 Early Exit 규칙을 강제하는 가드 테스트.

crawler.handler를 import 하는 것만으로 bs4·google-genai가 로드되면 실패한다.
pytest 프로세스에는 다른 테스트가 이미 bs4를 로드했을 수 있으므로 새 인터프리터에서 확인한다.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
HEAVY = ["bs4", "google.genai", "google", "lxml"]

CHECK = f"""
import json, sys
import crawler.handler
print(json.dumps([m for m in {HEAVY!r} if m in sys.modules]))
"""


def test_crawler_handler_does_not_import_heavy_libs():
    out = subprocess.run(
        [sys.executable, "-c", CHECK],
        cwd=SRC,
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "PYTHONPATH": str(SRC)},
    )
    loaded = json.loads(out.stdout.strip().splitlines()[-1])
    assert loaded == [], f"crawler.handler import 시 무거운 모듈 로드됨: {loaded}"


def test_skeleton_handler_returns_no_new(capsys):
    from crawler.handler import handler

    assert handler({}, None) == {"result": "no_new"}
    log = json.loads(capsys.readouterr().out.strip())
    assert log["fn"] == "crawler"
