from __future__ import annotations

import json

import pytest

from common.schema import (
    Importance,
    Notice,
    NoticeStatus,
    SchemaError,
    SummarizeMessage,
    SummaryStatus,
)

MSG = {
    "board_id": "cse_notice",
    "post_id": 1234,
    "title": "장학금 신청 안내",
    "url": "https://example.ac.kr/notice/1234",
    "posted_at": "2026-11-06",
}


def _notice(**overrides):
    base = {
        **MSG,
        "summary": "요약",
        "category": "장학",
        "importance": "high",
        "ttl": 1_800_000_000,
    }
    return {**base, **overrides}


class TestSummarizeMessage:
    def test_json_round_trip(self):
        msg = SummarizeMessage(**MSG)
        assert SummarizeMessage.from_json(msg.to_json()) == msg

    def test_korean_is_not_escaped(self):
        assert "장학금" in SummarizeMessage(**MSG).to_json()

    def test_unknown_fields_are_ignored(self):
        body = json.dumps({**MSG, "added_later": "x"})
        assert SummarizeMessage.from_json(body) == SummarizeMessage(**MSG)

    def test_missing_field_raises(self):
        body = json.dumps({k: v for k, v in MSG.items() if k != "url"})
        with pytest.raises(SchemaError, match="url"):
            SummarizeMessage.from_json(body)

    @pytest.mark.parametrize("bad", ["1234", 12.0, True])
    def test_post_id_must_be_int(self, bad):
        with pytest.raises(SchemaError, match="post_id"):
            SummarizeMessage(**{**MSG, "post_id": bad})


class TestNotice:
    def test_defaults(self):
        n = Notice.from_dict(_notice())
        assert n.status == NoticeStatus.SUMMARIZED
        assert n.summary_status == SummaryStatus.OK
        assert n.deadline is None

    def test_to_dict_drops_none_deadline(self):
        assert "deadline" not in Notice.from_dict(_notice()).to_dict()

    def test_to_dict_keeps_deadline(self):
        d = Notice.from_dict(_notice(deadline="2026-11-20")).to_dict()
        assert d["deadline"] == "2026-11-20"

    def test_round_trip(self):
        n = Notice.from_dict(_notice(deadline="2026-11-20", summary_status="FALLBACK"))
        assert Notice.from_dict(n.to_dict()) == n

    @pytest.mark.parametrize(
        "field, value",
        [("importance", "urgent"), ("status", "DONE"), ("summary_status", "FAILED")],
    )
    def test_enum_fields_validated(self, field, value):
        with pytest.raises(SchemaError, match=field):
            Notice.from_dict(_notice(**{field: value}))

    def test_importance_values(self):
        assert {i.value for i in Importance} == {"high", "medium", "low"}
