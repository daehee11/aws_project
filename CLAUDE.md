# 서버리스 AI 공지 요약 알림 봇

학교·학과·취업 공지 게시판(4~5개)을 30분마다 크롤링 → 새 글만 Gemini로 요약 → 디스코드 알림.
AWS Learner Lab(us-east-1) 위에서 Lambda + DynamoDB + SQS + EventBridge로 동작.

## 구조와 담당
- `src/crawler/`, `src/summarizer/` — A (크롤링·요약)
- `template.yaml`, `scripts/`, `layers/` — B (AWS 인프라)
- `src/notifier/`, `src/discord_bot/` — C (디스코드)
- `src/common/schema.py` — 모듈 간 메시지 계약. 변경 시 3명 합의 필수
- 상세 설계: `docs/contracts.md`

흐름: EventBridge → crawler → SQS(summarize) → summarizer → DynamoDB Notices → notifier → Discord

## 명령어
- 테스트: `pytest`
- 린트/포맷: `ruff check . ; ruff format .`
- 빌드/배포: `sam build ; sam deploy` (Learner Lab 세션 시작 후 자격증명 갱신 필요)
- 로컬 실행: `sam local invoke CrawlerFunction -e events/schedule.json`

## 반드시 지킬 규칙
### Early Exit (crawler)
- `src/crawler/handler.py` 모듈 최상단에서 `bs4`, `google-genai` 등 무거운 라이브러리를 import 하지 말 것.
  새 글이 있을 때만 `importlib`로 파서를 지연 로드한다.
- 새 글 판정은 정규식 + `max(게시글 번호)`로만 한다(고정 공지 대응). 판정 단계에서 bs4 사용 금지.
- `BoardState` 갱신은 반드시 조건부 업데이트(`last_post_id < :new`).

### 멱등성
- SQS는 중복 전달될 수 있다. Notices 저장은 `attribute_not_exists`, 알림 상태 변경은 조건부 업데이트로 처리.

### Learner Lab 제약
- IAM Role 생성 불가 → 모든 Lambda는 기존 `LabRole` ARN 사용. CDK 사용 금지(bootstrap이 Role 생성).
- EventBridge Scheduler 대신 EventBridge Rule 사용.
- 리전은 us-east-1 고정. 비용 절약: DynamoDB On-Demand, Lambda 256MB 이하, 로그 보존 7일.

### 시크릿
- Gemini API 키, Discord Webhook URL은 SSM Parameter Store(SecureString)에서만 읽는다.
  코드·테스트·커밋·로그에 실제 값을 넣지 말 것.

## 테스트 규칙
- 테스트에서 실제 학교/취업 사이트, Gemini, Discord에 요청하지 않는다.
  HTML은 `tests/fixtures/`, AWS는 `moto`, 외부 API는 mock 사용.
- 새 게시판 추가 시: `boards.py` 등록 + 목록/상세 fixture + 파서 테스트를 함께 추가.

## 코드 스타일
- Python 3.12, 타입 힌트 사용, ruff 기본 규칙.
- Lambda 로그는 `print(json.dumps({...}))` 형태의 JSON 한 줄 (CloudWatch Logs Insights 집계용).
- 커밋 메시지: `[crawler] ...`, `[infra] ...`, `[discord] ...` 처럼 영역 접두어.
