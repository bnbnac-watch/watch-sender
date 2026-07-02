import asyncio
import logging
from collections import defaultdict
import db
from senders import slack, telegram, webhook, discord

logger = logging.getLogger(__name__)

_SENDERS = {
    "slack": slack.send,
    "telegram": telegram.send,
    "discord": discord.send,
}


def _format_items(crawler_id: str, items: list[dict]) -> str:
    lines = [f"[{crawler_id}] 새 글 {len(items)}개"]
    for item in items:
        if item.get("summary"):
            lines.append(f"• {item['title']}\n{item['summary']}")
        else:
            lines.append(f"• {item['title']} - {item['url']}")
    return "\n".join(lines)


def _format_error(crawler_id: str, error: str, fail_count: int) -> str:
    return f"[{crawler_id}] 크롤러 오류 ({fail_count}회 연속)\n{error}"


def _split_message(message: str, max_chars: int) -> list[str]:
    if len(message) <= max_chars:
        return [message]
    chunks = []
    current = []
    current_len = 0
    for line in message.splitlines(keepends=True):
        if current_len + len(line) > max_chars and current:
            chunks.append("".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += len(line)
    if current:
        chunks.append("".join(current))
    return chunks


async def _dispatch(dest: dict, message: str, payload: dict):
    max_chars = dest["config"].get("max_chars")
    messages = _split_message(message, max_chars) if max_chars else [message]
    try:
        for chunk in messages:
            if dest["type"] == "webhook":
                await webhook.send(dest["config"], payload)
            else:
                sender = _SENDERS.get(dest["type"])
                if sender:
                    await sender(dest["config"], chunk)
        logger.info("[%s] 발송 성공 (%d 청크)", dest["id"], len(messages))
    except Exception as e:
        logger.error("[%s] 발송 실패: %s", dest["id"], e)


async def route_notify(crawler_id: str, items: list[dict]):
    destinations = await db.get_destinations(crawler_id)
    message = _format_items(crawler_id, items)
    payload = {"crawler_id": crawler_id, "items": items}
    await asyncio.gather(*[_dispatch(dest, message, payload) for dest in destinations])


async def route_notify_batch(entries: list[dict]):
    dest_map: dict[str, tuple[dict, list[str]]] = defaultdict(lambda: (None, []))

    for entry in entries:
        crawler_id = entry["crawler_id"]
        items = entry["items"]
        destinations = await db.get_destinations(crawler_id)
        message = _format_items(crawler_id, items)
        for dest in destinations:
            existing = dest_map[dest["id"]]
            if existing[0] is None:
                dest_map[dest["id"]] = (dest, [message])
            else:
                existing[1].append(message)

    payload = {"entries": entries}
    await asyncio.gather(*[
        _dispatch(dest, "\n\n".join(messages), payload)
        for dest, messages in dest_map.values()
        if dest is not None
    ])


async def route_error(crawler_id: str, error: str, fail_count: int):
    destinations = await db.get_destinations(crawler_id)
    message = _format_error(crawler_id, error, fail_count)
    payload = {"crawler_id": crawler_id, "error": error, "fail_count": fail_count}
    await asyncio.gather(*[_dispatch(dest, message, payload) for dest in destinations])
