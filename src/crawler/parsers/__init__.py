"""게시판 어댑터(파서). bs4는 여기서만 import 한다 — crawler.handler에서 지연 로드됨.

각 파서 모듈은 다음 함수를 제공한다:
    parse_list(html: bytes) -> list[common.schema.SummarizeMessage]
"""
