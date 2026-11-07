"""crawler Lambda — EventBridge Rule(rate(30 minutes))로 실행.

Early Exit 규칙 (CLAUDE.md):
- 모듈 최상단에서 bs4, google-genai 등 무거운 라이브러리를 import 하지 않는다.
- 새 글 판정은 정규식 + max(게시글 번호)로만 한다.
- 새 글이 있을 때만 importlib로 board.parser를 로드한다.

M2에서 구현 예정. 지금은 Walking Skeleton용 스텁.
"""

from __future__ import annotations

import json
from typing import Any

from crawler.boards import BOARDS


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    _log("no_new", boards=len(BOARDS))
    return {"result": "no_new"}


def _log(event: str, **fields: Any) -> None:
    print(json.dumps({"fn": "crawler", "event": event, **fields}, ensure_ascii=False))
