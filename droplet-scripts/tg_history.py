"""tg_history — dump recent messages from a Telegram chat via Telethon.

Usage:
  tg_history.py [chat_handle] [n_messages]

Default: last 30 messages from @sergei_brand_agent_bot
"""
import asyncio
import os
import sys
from pathlib import Path

from telethon import TelegramClient

SECRETS = Path("/opt/brand-agent/secrets")
SESSION_PATH = SECRETS / "telethon"
ENV_PATH = Path("/opt/brand-agent/.env")


def _load_env() -> dict:
    env = {}
    for line in ENV_PATH.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


async def dump_history(chat: str, n: int):
    env = _load_env()
    api_id = int(env["TG_USER_API_ID"])
    api_hash = env["TG_USER_API_HASH"]
    client = TelegramClient(str(SESSION_PATH), api_id, api_hash)
    await client.connect()
    if not await client.is_user_authorized():
        print("NOT AUTHORIZED — session file invalid")
        return 1
    entity = await client.get_entity(chat)
    msgs = []
    async for msg in client.iter_messages(entity, limit=n):
        msgs.append(msg)
    msgs.reverse()  # oldest first
    for m in msgs:
        ts = m.date.strftime("%H:%M") if m.date else "??:??"
        direction = "→" if m.out else "←"
        text = (m.text or "").replace("\n", " ").strip()[:200]
        print(f"[{ts}] {direction} msg{m.id}: {text}")
    await client.disconnect()
    return 0


def main():
    chat = sys.argv[1] if len(sys.argv) > 1 else "@sergei_brand_agent_bot"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    return asyncio.run(dump_history(chat, n))


if __name__ == "__main__":
    sys.exit(main())
