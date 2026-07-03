import httpx


async def send(config: dict, message: str, client: httpx.AsyncClient):
    url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
    res = await client.post(url, json={"chat_id": config["chat_id"], "text": message})
    res.raise_for_status()
