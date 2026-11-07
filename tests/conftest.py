from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def _fake_aws(monkeypatch: pytest.MonkeyPatch) -> None:
    """실수로 실제 AWS에 요청하지 않도록 가짜 자격증명·리전을 강제한다."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.delenv("AWS_PROFILE", raising=False)


@pytest.fixture
def fixture_bytes():
    """tests/fixtures/<name> 을 bytes로 읽는다 (게시판 HTML fixture용)."""

    def _read(name: str) -> bytes:
        return (FIXTURES / name).read_bytes()

    return _read
