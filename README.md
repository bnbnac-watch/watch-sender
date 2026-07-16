# watch-sender

`crawler_id`를 destination(discord/slack/telegram)으로 라우팅하고 실제 발송을 담당한다. 크롤링이나 중복 감지, 요약에는 관여하지 않는다 — `watch-runner`가 이미 걸러낸 아이템을 그대로 메시지로 포맷해서 보낸다.

## API

### POST /notify

```json
{"crawler_id": 1, "items": [{"id": "...", "title": "...", "url": "...", "summary": "..."}]}
```

`crawler_id`에 연결된 destination(`crawler_destinations` JOIN `destinations`, `enabled=true`)마다 병렬로 발송한다.

### POST /notify/batch

```json
{"entries": [{"crawler_id": 1, "items": [...]}, {"crawler_id": 2, "items": [...]}]}
```

배치 그룹(`watch-runner`의 `run_batch`)이 한 번에 넘기는 형태. `crawler_id`별로 destination을 조회한 뒤, **같은 destination을 공유하는 여러 crawler의 메시지를 하나로 합쳐서** 한 번만 발송한다(`route_notify_batch`) — 같은 시간대에 여러 채널이 동시에 새 글을 발견해도 destination당 메시지가 한 번만 나가게 하기 위함.

### POST /error

```json
{"crawler_id": 1, "error": "...", "fail_count": 3}
```

크롤러 실패 알림. 해당 crawler의 destination 전체에 발송.

### GET /health

`{"status": "ok"}`

## 메시지 포맷 (`formatters.py`)

- `format_items`: `[{crawler_id}] 새 글 {n}개` 헤더 + 아이템별 `제목` 다음 줄에 `url`(요약 있으면 제목 아래 요약 본문)
- `format_error`: `[{crawler_id}] 크롤러 오류 ({fail_count}회 연속)` + 에러 메시지
- `split_message`: 플랫폼별 글자 수 한도를 넘으면 줄바꿈 경계에서 잘라 여러 메시지로 분할 발송(문장 중간 절단 방지)

글자 수 한도는 `router.py`의 `_TYPE_LIMITS` 딕셔너리에 타입별로 하드코딩되어 있다(`discord: 2000`, `telegram: 4096`, `slack: 40000`). destination별로 `config.max_chars`를 따로 두는 방식은 아직 구현되지 않았다 — 현재는 타입 단위로만 제한된다.

## sender 구현 (`senders/`)

| type | 방식 |
|---|---|
| `discord` | webhook POST `{"content": message}` |
| `slack` | webhook POST `{"text": message}` |
| `telegram` | Bot API `sendMessage` (`config.bot_token`, `config.chat_id`) |

지원 타입은 위 3개뿐이다. `_SENDERS`에 없는 타입이 오면 로그만 남기고 조용히 스킵한다 — 예외를 던지지 않으므로 `/notify` 호출 자체는 성공(200)으로 끝나고, 실제로 아무 데도 발송되지 않았다는 건 로그를 봐야 알 수 있다.

## 환경변수

| 변수 | 설명 |
|---|---|
| `DATABASE_URL` | PostgreSQL 연결 문자열 (destinations/crawler_destinations 조회) |

## 포트

| 포트 | 용도 |
|---|---|
| 8080 | FastAPI — 컴포즈 내부에서만 노출, 외부 포트 매핑 없음 |

## 미구현: 방해금지 시간(DND)

`_dispatch()`는 현재 시간대와 무관하게 항상 즉시 발송한다 — 방해금지 시간(예: 밤 시간대엔 발송 보류)이나 발송 지연 큐 같은 기능은 아직 없다.
