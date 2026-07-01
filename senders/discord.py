import httpx


async def send(config: dict, message: str):
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.post(config["url"], json={"content": message})
        res.raise_for_status()
