import asyncio
import logging
import os
from collections import defaultdict
import httpx
import db
import formatters
from senders import slack, telegram, discord

logger = logging.getLogger(__name__)

_http_client: httpx.AsyncClient | None = None

# 운영 알림(오류·복구)은 소비자가 보는 크롤러 destination과 분리해 이 destination으로만 보낸다.
# 미설정이면 발송하지 않는다 — 크롤러 destination으로 폴백하면 내부 오류 원문이 공용 채널에 나간다.
ALERT_DESTINATION_ID = int(os.environ["ALERT_DESTINATION_ID"]) if os.getenv("ALERT_DESTINATION_ID") else None


def set_client(client: httpx.AsyncClient):
    global _http_client
    _http_client = client


_SENDERS = {
    "slack": slack.send,
    "telegram": telegram.send,
    "discord": discord.send,
}

_TYPE_LIMITS = {
    "discord": 2000,
    "telegram": 4096,
    "slack": 40000,
}


async def _dispatch(dest: dict, message: str):
    max_chars = _TYPE_LIMITS.get(dest["type"])
    messages = formatters.split_message(message, max_chars) if max_chars else [message]
    sender = _SENDERS.get(dest["type"])
    if sender is None:
        logger.error("[%s] 알 수 없는 destination 타입: %s", dest["id"], dest["type"])
        return
    try:
        for chunk in messages:
            await sender(dest["config"], chunk, _http_client)
        logger.info("[%s] 발송 성공 (%d 청크)", dest["id"], len(messages))
    except Exception as e:
        logger.error("[%s] 발송 실패: %s", dest["id"], e)


async def route_notify(crawler_id: str, items: list[dict]):
    destinations = await db.get_destinations(crawler_id)
    message = formatters.format_items(crawler_id, items)
    await asyncio.gather(*[_dispatch(dest, message) for dest in destinations])


async def route_notify_batch(entries: list[dict]):
    dest_map: dict[str, tuple[dict, list[str]]] = defaultdict(lambda: (None, []))

    for entry in entries:
        crawler_id = entry["crawler_id"]
        items = entry["items"]
        destinations = await db.get_destinations(crawler_id)
        message = formatters.format_items(crawler_id, items)
        for dest in destinations:
            existing = dest_map[dest["id"]]
            if existing[0] is None:
                dest_map[dest["id"]] = (dest, [message])
            else:
                existing[1].append(message)

    await asyncio.gather(*[
        _dispatch(dest, "\n\n".join(messages))
        for dest, messages in dest_map.values()
        if dest is not None
    ])


async def _dispatch_alert(message: str):
    if ALERT_DESTINATION_ID is None:
        logger.warning("ALERT_DESTINATION_ID 미설정, 운영 알림 발송 생략: %s", message.splitlines()[0])
        return
    dest = await db.get_destination(ALERT_DESTINATION_ID)
    if dest is None:
        logger.error("운영 알림 destination을 찾을 수 없음 (id=%s), 발송 생략", ALERT_DESTINATION_ID)
        return
    await _dispatch(dest, message)


async def route_error(crawler_id: int, error: str, fail_count: int, disabled: bool = False):
    await _dispatch_alert(formatters.format_error(crawler_id, error, fail_count, disabled))


async def route_recovered(crawler_id: int, previous_fail_count: int):
    await _dispatch_alert(formatters.format_recovery(crawler_id, previous_fail_count))
