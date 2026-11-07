"""summarizer Lambda — SQS summarize-queue 트리거.

M3에서 구현 예정: 상세 페이지 → bs4 본문 추출 → Gemini 구조화 출력 → Notices PutItem
(attribute_not_exists 조건). 마지막 재시도에서도 실패하면 FALLBACK 저장.
지금은 메시지 계약만 검증하는 Walking Skeleton용 스텁.
"""

from __future__ import annotations

import json
from typing import Any

from common.schema import SummarizeMessage


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    for record in event.get("Records", []):
        msg = SummarizeMessage.from_json(record["body"])
        _log("received", board_id=msg.board_id, post_id=msg.post_id)
    # SQS 부분 배치 실패 응답 형식 (ReportBatchItemFailures)
    return {"batchItemFailures": []}


def _log(event: str, **fields: Any) -> None:
    print(json.dumps({"fn": "summarizer", "event": event, **fields}, ensure_ascii=False))
