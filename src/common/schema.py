"""모듈 간 메시지 계약 (crawler → summarizer → notifier).

이 파일을 바꾸면 A·B·C 3명 합의가 필요하다. 바꿀 때는 docs/contracts.md도 같은 PR에서 고친다.
무거운 라이브러리를 import 하지 말 것 (crawler의 Early Exit 경로에서도 로드된다).
"""

from __future__ import annotations

import json
from dataclasses import MISSING, asdict, dataclass, fields
from enum import StrEnum
from typing import Any, Self


# ---------------------------------------------------------------------------
# 환경변수 이름 (template.yaml의 Environment.Variables와 일치해야 함)
# ---------------------------------------------------------------------------
class EnvVar(StrEnum):
    STATE_TABLE = "STATE_TABLE"  # DynamoDB BoardState
    NOTICES_TABLE = "NOTICES_TABLE"  # DynamoDB Notices
    SUBSCRIPTIONS_TABLE = "SUBSCRIPTIONS_TABLE"  # DynamoDB Subscriptions (C, 선택)
    SUMMARIZE_QUEUE_URL = "SUMMARIZE_QUEUE_URL"  # SQS summarize-queue
    GEMINI_API_KEY_PARAM = "GEMINI_API_KEY_PARAM"  # SSM 파라미터 "이름" (값 아님)
    DISCORD_WEBHOOK_PARAM = "DISCORD_WEBHOOK_PARAM"  # SSM 파라미터 "이름" (값 아님)


# ---------------------------------------------------------------------------
# 상태 값
# ---------------------------------------------------------------------------
class NoticeStatus(StrEnum):
    SUMMARIZED = "SUMMARIZED"
    NOTIFIED = "NOTIFIED"


class SummaryStatus(StrEnum):
    OK = "OK"
    FALLBACK = "FALLBACK"  # 요약 최종 실패 → summary = 본문 앞 300자


class Importance(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


FALLBACK_SUMMARY_CHARS = 300
NOTICE_TTL_DAYS = 90


class SchemaError(ValueError):
    """메시지가 계약과 맞지 않을 때."""


def _check_types(obj: Any) -> None:
    """dataclass 필드의 런타임 타입을 확인한다 (str / int / str | None 만 지원)."""
    for f in fields(obj):
        value = getattr(obj, f.name)
        allowed = {"str": (str,), "int": (int,), "str | None": (str, type(None))}[f.type]
        # bool은 int의 하위 타입이라 따로 막는다.
        if isinstance(value, bool) or not isinstance(value, allowed):
            raise SchemaError(f"{type(obj).__name__}.{f.name}: {f.type} 필요, {value!r} 받음")


def _from_dict[T](cls: type[T], data: dict[str, Any]) -> T:
    names = {f.name for f in fields(cls)}
    required = {
        f.name for f in fields(cls) if f.default is MISSING and f.default_factory is MISSING
    }
    missing = required - data.keys()
    if missing:
        raise SchemaError(f"{cls.__name__}: 필수 필드 누락 {sorted(missing)}")
    # 모르는 필드는 무시 → 한쪽이 필드를 추가해도 다른 쪽이 깨지지 않음
    return cls(**{k: v for k, v in data.items() if k in names})


# ---------------------------------------------------------------------------
# crawler → summarizer : SQS summarize-queue 메시지 본문
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class SummarizeMessage:
    board_id: str
    post_id: int
    title: str
    url: str
    posted_at: str  # YYYY-MM-DD

    def __post_init__(self) -> None:
        _check_types(self)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, body: str) -> Self:
        return _from_dict(cls, json.loads(body))


# ---------------------------------------------------------------------------
# summarizer → Notices 테이블 → notifier : 공지 1건
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class Notice:
    board_id: str  # PK
    post_id: int  # SK
    title: str
    url: str
    posted_at: str  # YYYY-MM-DD
    summary: str
    category: str  # 예: 장학, 학사, 채용, 행사, 기타
    importance: str  # Importance 값
    ttl: int  # epoch seconds (DynamoDB TTL)
    deadline: str | None = None  # YYYY-MM-DD, 없으면 None
    status: str = NoticeStatus.SUMMARIZED
    summary_status: str = SummaryStatus.OK

    def __post_init__(self) -> None:
        _check_types(self)
        if self.importance not in set(Importance):
            raise SchemaError(f"Notice.importance: {list(Importance)} 중 하나, {self.importance!r}")
        if self.status not in set(NoticeStatus):
            raise SchemaError(f"Notice.status: {list(NoticeStatus)} 중 하나, {self.status!r}")
        if self.summary_status not in set(SummaryStatus):
            raise SchemaError(
                f"Notice.summary_status: {list(SummaryStatus)} 중 하나, {self.summary_status!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        """deadline이 None이면 키를 뺀다 (DynamoDB에 NULL 저장 방지)."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return _from_dict(cls, data)
