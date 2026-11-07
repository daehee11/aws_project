"""notifier Lambda (C 담당) — Walking Skeleton용 스텁.

M4에서 C가 구현: Notices 변경 이벤트 → Discord Webhook Embed → status=NOTIFIED 조건부 갱신.
트리거(DynamoDB Streams vs SQS notify-queue)는 docs/contracts.md의 미결 사항 참고.
"""

from __future__ import annotations

import json
from typing import Any


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    records = event.get("Records", [])
    print(json.dumps({"fn": "notifier", "event": "received", "records": len(records)}))
    return {"batchItemFailures": []}
