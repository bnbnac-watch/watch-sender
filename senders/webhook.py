import httpx


async def send(config: dict, payload: dict):
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.post(config["url"], json=payload)
        res.raise_for_status()
