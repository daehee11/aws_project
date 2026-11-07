"""게시판 레지스트리.

새 게시판 추가 시: 여기 등록 + tests/fixtures/<board_id>_list.html, _detail.html + 파서 테스트.
이 모듈은 Early Exit 경로에서 로드되므로 정규식·표준 라이브러리만 사용한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Board:
    board_id: str  # 예: "cse_notice"
    list_url: str
    id_regex: re.Pattern[bytes]  # 목록 HTML(bytes)에서 게시글 번호를 뽑는 정규식, 그룹 1 = 번호
    parser: str  # 새 글이 있을 때만 importlib로 로드할 모듈 (예: "crawler.parsers.k2web")


# M0에서 게시판 조사 후 채운다.
BOARDS: tuple[Board, ...] = ()
