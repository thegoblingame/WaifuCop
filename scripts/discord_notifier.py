# Claude, please note that this file is not currently being used. 

import os
import requests
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

if not WEBHOOK_URL:
    raise RuntimeError("DISCORD_WEBHOOK_URL env var is not set")


def send_discord_message(content: str) -> None:
    resp = requests.post(
        WEBHOOK_URL,
        json={
            "content": content,
            # optional extras:
            "username": "waifucop",
            "avatar_url": "https://i.imgur.com/zxLfvT3.jpeg",
        },
        timeout=10,
    )
    resp.raise_for_status()
