"""telegram_user_monitor — Telethon daemon for Sergei's personal Telegram.

Distinct from telegram_bot.py: that uses the Bot API. This uses the User API
via Telethon (acts AS Sergei to read his DMs + channel mentions).

What it does:
  - Listens for incoming messages to Sergei's account
  - Filters: private DMs + @mentions in subscribed channels + replies to his
    messages in groups
  - Runs each through triage.py
  - For non-skip: emits event via emit_event with kind=mention
  - Buttons in the resulting Telegram bot notification let Sergei [Reply/Mute/Skip]

Session lives at /opt/brand-agent/secrets/telethon.session — encrypted file
keyed to Sergei's phone number. Revocable any time via Telegram → Settings →
Active Sessions.

Usage:
  python telegram_user_monitor.py auth      # one-time SMS-code auth
  python telegram_user_monitor.py run       # daemon mode (systemd)
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/opt/brand-agent")

from telethon import TelegramClient, events  # noqa: E402
from telethon.tl.types import User  # noqa: E402

import triage  # noqa: E402

SECRETS = Path("/opt/brand-agent/secrets")
SESSION_PATH = SECRETS / "telethon"   # Telethon adds .session itself
ENV_PATH = Path("/opt/brand-agent/.env")


def _load_env() -> dict:
    env = {}
    for line in ENV_PATH.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def _emit(severity: str, subject: str, body: str) -> None:
    subprocess.run(
        ["/usr/local/bin/emit_event", severity, "mention",
         f"💬 {subject[:60]}", body],
        check=False,
    )


async def _on_new_message(event):
    """Handle one incoming message."""
    msg = event.message
    if not msg.text:
        return

    sender = await event.get_sender()
    sender_name = ""
    if isinstance(sender, User):
        sender_name = (
            (sender.username and f"@{sender.username}")
            or f"{sender.first_name or ''} {sender.last_name or ''}".strip()
            or str(sender.id)
        )
    else:
        sender_name = getattr(sender, "title", "") or str(getattr(sender, "id", "?"))

    chat = await event.get_chat()
    chat_title = getattr(chat, "title", None) or "(DM)"
    is_private = event.is_private

    # Reduce noise: only act on private DMs OR mentions in groups/channels
    text = msg.text
    sergei_handles = ["sergei", "solovev", "сергей", "соловьёв", "соловьев"]
    is_mention = any(h.lower() in text.lower() for h in sergei_handles)

    if not is_private and not is_mention:
        return

    decision = triage.triage(sender_name, chat_title, text)
    if decision["decision"] == "skip":
        return

    body = (
        f"From: {sender_name}\n"
        f"Chat: {chat_title} ({'DM' if is_private else 'channel/group'})\n"
        f"Triage: {decision['reason']}\n\n"
        f"{text[:1500]}"
    )
    _emit(decision["severity"], f"{sender_name}: {text[:50]}", body)


async def auth_flow():
    """One-time auth — prompts for SMS code from Telegram."""
    env = _load_env()
    api_id = env.get("TG_USER_API_ID") or os.environ.get("TG_USER_API_ID")
    api_hash = env.get("TG_USER_API_HASH") or os.environ.get("TG_USER_API_HASH")
    phone = env.get("TG_USER_PHONE") or os.environ.get("TG_USER_PHONE")
    if not all([api_id, api_hash, phone]):
        print("ERROR: TG_USER_API_ID, TG_USER_API_HASH, TG_USER_PHONE must be in .env")
        return 1
    SECRETS.mkdir(parents=True, exist_ok=True)
    client = TelegramClient(str(SESSION_PATH), int(api_id), api_hash)
    await client.start(phone=phone)  # prompts for SMS code on stdin
    me = await client.get_me()
    print(f"✓ authenticated as @{me.username} ({me.first_name})")
    await client.disconnect()
    return 0


async def run_daemon():
    env = _load_env()
    api_id = env.get("TG_USER_API_ID") or os.environ.get("TG_USER_API_ID")
    api_hash = env.get("TG_USER_API_HASH") or os.environ.get("TG_USER_API_HASH")
    if not all([api_id, api_hash]):
        print("ERROR: TG_USER_API_ID, TG_USER_API_HASH must be in .env")
        return 1

    client = TelegramClient(str(SESSION_PATH), int(api_id), api_hash)
    await client.start()  # no phone needed — uses cached session
    me = await client.get_me()
    print(f"telegram_user_monitor running as @{me.username}")

    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        try:
            await _on_new_message(event)
        except Exception as e:
            print(f"handler error: {e}")

    await client.run_until_disconnected()
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    if sys.argv[1] == "auth":
        return asyncio.run(auth_flow())
    elif sys.argv[1] == "run":
        return asyncio.run(run_daemon())
    else:
        print(f"Unknown command: {sys.argv[1]}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
