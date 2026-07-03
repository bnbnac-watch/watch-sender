import httpx


async def send(config: dict, message: str, client: httpx.AsyncClient):
    res = await client.post(config["url"], json={"content": message})
    res.raise_for_status()
