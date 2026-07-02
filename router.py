import asyncio
import logging
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
        lines.append(f"• {item['title']} - {item['url']}")
    return "\n".join(lines)


def _format_error(crawler_id: str, error: str, fail_count: int) -> str:
    return f"[{crawler_id}] 크롤러 오류 ({fail_count}회 연속)\n{error}"


async def _dispatch(dest: dict, message: str, payload: dict):
    try:
        if dest["type"] == "webhook":
            await webhook.send(dest["config"], payload)
        else:
            sender = _SENDERS.get(dest["type"])
            if sender:
                await sender(dest["config"], message)
        logger.info("[%s] 발송 성공", dest["id"])
    except Exception as e:
        logger.error("[%s] 발송 실패: %s", dest["id"], e)


async def route_notify(crawler_id: str, items: list[dict]):
    destinations = await db.get_destinations(crawler_id)
    message = _format_items(crawler_id, items)
    payload = {"crawler_id": crawler_id, "items": items}
    await asyncio.gather(*[_dispatch(dest, message, payload) for dest in destinations])


async def route_error(crawler_id: str, error: str, fail_count: int):
    destinations = await db.get_destinations(crawler_id)
    message = _format_error(crawler_id, error, fail_count)
    payload = {"crawler_id": crawler_id, "error": error, "fail_count": fail_count}
    await asyncio.gather(*[_dispatch(dest, message, payload) for dest in destinations])
