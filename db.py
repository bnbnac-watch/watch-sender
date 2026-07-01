import os
import asyncpg

_pool: asyncpg.Pool | None = None


async def init():
    global _pool
    _pool = await asyncpg.create_pool(os.environ["DATABASE_URL"])


def get_pool() -> asyncpg.Pool:
    return _pool


async def get_destinations(crawler_id: str) -> list[asyncpg.Record]:
    async with _pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT d.id, d.type, d.config
            FROM destinations d
            JOIN crawler_destinations cd ON cd.destination_id = d.id
            WHERE cd.crawler_id = $1 AND cd.enabled = true
            """,
            crawler_id,
        )
