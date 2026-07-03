import asyncio
import logging
from collections import defaultdict
import db
import formatters
from senders import slack, telegram, discord

logger = logging.getLogger(__name__)

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
            await sender(dest["config"], chunk)
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


async def route_error(crawler_id: str, error: str, fail_count: int):
    destinations = await db.get_destinations(crawler_id)
    message = formatters.format_error(crawler_id, error, fail_count)
    await asyncio.gather(*[_dispatch(dest, message) for dest in destinations])
