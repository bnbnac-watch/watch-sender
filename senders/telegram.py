import httpx


async def send(config: dict, message: str):
    # config: {"bot_token": "...", "chat_id": "..."}
    url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.post(url, json={"chat_id": config["chat_id"], "text": message})
        res.raise_for_status()
