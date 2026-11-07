# 모듈 간 계약

코드상 원본은 `src/common/schema.py`. 이 문서와 어긋나면 **둘 다** 고친다. 변경 시 A·B·C 합의 필수.

## 1. Lambda

| 함수 | 핸들러 | 트리거 | 메모리 / 타임아웃 |
|---|---|---|---|
| CrawlerFunction | `crawler.handler.handler` | EventBridge Rule `rate(30 minutes)` | 256MB / 30s |
| SummarizerFunction | `summarizer.handler.handler` | SQS summarize-queue (batch 1~5, `MaximumConcurrency` 2, `ReportBatchItemFailures`) | 256MB / 60s |
| NotifierFunction | `notifier.handler.handler` | **미정** (아래 미결 사항) | 128MB / 30s |
| DiscordBotFunction (선택) | `discord_bot.handler.handler` | API Gateway | 128MB / 3s 내 응답 |

- `CodeUri: src/` — 모든 함수가 `src`를 루트로 import (`from common.schema import ...`)
- Role: 모두 기존 `LabRole` ARN
- Layer: crawler → bs4 / summarizer → bs4 + google-genai / discord_bot → pynacl

## 2. 환경변수 (`common.schema.EnvVar`)

| 이름 | 값 | 사용 함수 |
|---|---|---|
| `STATE_TABLE` | BoardState 테이블 이름 | crawler |
| `NOTICES_TABLE` | Notices 테이블 이름 | summarizer, notifier, discord_bot |
| `SUBSCRIPTIONS_TABLE` | Subscriptions 테이블 이름 | notifier, discord_bot |
| `SUMMARIZE_QUEUE_URL` | summarize-queue URL | crawler |
| `GEMINI_API_KEY_PARAM` | SSM 파라미터 **이름** (예: `/noticebot/gemini-api-key`) | summarizer |
| `DISCORD_WEBHOOK_PARAM` | SSM 파라미터 **이름** (예: `/noticebot/discord-webhook`) | notifier |

시크릿 값은 환경변수에 넣지 않는다. 함수가 cold start 시 SSM에서 `WithDecryption=True`로 1회 읽어 캐시.

## 3. DynamoDB (모두 On-Demand)

### BoardState
| 속성 | 타입 | 설명 |
|---|---|---|
| `board_id` (PK) | S | |
| `last_post_id` | N | 처리 완료한 최대 게시글 번호. 갱신은 `last_post_id < :new` 조건부 |
| `etag` | S | 조건부 GET용 (선택) |
| `updated_at` | S | ISO8601 |

### Notices — `common.schema.Notice`
| 속성 | 타입 | 설명 |
|---|---|---|
| `board_id` (PK) | S | |
| `post_id` (SK) | N | |
| `title`, `url` | S | |
| `posted_at` | S | `YYYY-MM-DD` |
| `summary` | S | 3줄 요약. FALLBACK이면 본문 앞 300자 |
| `category` | S | 장학 / 학사 / 채용 / 행사 / 기타 |
| `importance` | S | `high` / `medium` / `low` |
| `deadline` | S | `YYYY-MM-DD`, 없으면 속성 자체가 없음 |
| `status` | S | `SUMMARIZED` → `NOTIFIED` (조건부 갱신) |
| `summary_status` | S | `OK` / `FALLBACK` |
| `ttl` | N | epoch seconds, 저장 시점 + 90일 (TTL 활성화) |

저장은 `attribute_not_exists(post_id)` 조건부 PutItem.

### Subscriptions (C, 선택)
`channel_id` (PK, S), `boards` (SS), `webhook_param` (S)

## 4. SQS

### summarize-queue (+ DLQ, maxReceiveCount 5, visibility timeout 120s)
본문 = `SummarizeMessage.to_json()`
```json
{"board_id": "cse_notice", "post_id": 1234, "title": "...", "url": "https://...", "posted_at": "2026-11-06"}
```
- 수신 측은 모르는 필드를 무시한다 (필드 추가는 하위 호환).
- 필드 삭제·이름 변경·타입 변경은 3명 합의.

## 5. 로그 형식
`print(json.dumps({"fn": "<함수>", "event": "<이벤트>", ...}))` 한 줄.
crawler는 게시판별 `result` = `not_modified` / `no_new` / `new` / `error`.

## 6. 미결 사항
- [ ] **notifier 트리거**: DynamoDB Streams vs SQS notify-queue (B·C 결정)
- [ ] 대상 게시판 4~5개 URL 확정 + 게시판별 조사 결과 (A, 아래 표 채우기)
- [ ] SSM 파라미터 경로 prefix 확정 (B)

| board_id | URL | CMS/파서 | JS 렌더링 | ETag/RSS | robots.txt | 비고 |
|---|---|---|---|---|---|---|
| | | | | | | |
