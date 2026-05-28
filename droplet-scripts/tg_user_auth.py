#!/opt/brand-agent/venv/bin/python3
"""tg_user_auth — two-step non-interactive Telethon auth helper.

Standard `client.start(phone=...)` is interactive (prompts stdin). For our
remote-driven flow we need:

  tg_user_auth.py send_code <phone>
      → connects, requests SMS code, saves phone_code_hash to /tmp/tg_auth_state

  tg_user_auth.py sign_in <code> [password]
      → reads /tmp/tg_auth_state, completes sign-in
      → 2FA password optional (only if account has 2FA enabled)

After sign_in succeeds, session lives in /opt/brand-agent/secrets/telethon.session
and `systemctl start telegram-user-monitor` brings up the daemon.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

SECRETS = Path("/opt/brand-agent/secrets")
SESSION_PATH = SECRETS / "telethon"
STATE_PATH = Path("/tmp/tg_auth_state.json")
ENV_PATH = Path("/opt/brand-agent/.env")


def _load_env() -> dict:
    env = {}
    for line in ENV_PATH.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


async def send_code(phone: str) -> int:
    env = _load_env()
    api_id = int(env.get("TG_USER_API_ID") or os.environ["TG_USER_API_ID"])
    api_hash = env.get("TG_USER_API_HASH") or os.environ["TG_USER_API_HASH"]

    SECRETS.mkdir(parents=True, exist_ok=True)
    client = TelegramClient(str(SESSION_PATH), api_id, api_hash)
    await client.connect()
    sent = await client.send_code_request(phone)
    STATE_PATH.write_text(json.dumps({
        "phone": phone,
        "phone_code_hash": sent.phone_code_hash,
    }))
    os.chmod(STATE_PATH, 0o600)
    print(f"✓ code sent to {phone}")
    print(f"  next: tg_user_auth.py sign_in <code> [2fa_password]")
    await client.disconnect()
    return 0


async def sign_in(code: str, password: str | None = None) -> int:
    if not STATE_PATH.exists():
        print(f"FAIL: {STATE_PATH} missing — run send_code first")
        return 1
    state = json.loads(STATE_PATH.read_text())
    env = _load_env()
    api_id = int(env.get("TG_USER_API_ID") or os.environ["TG_USER_API_ID"])
    api_hash = env.get("TG_USER_API_HASH") or os.environ["TG_USER_API_HASH"]

    client = TelegramClient(str(SESSION_PATH), api_id, api_hash)
    await client.connect()
    try:
        await client.sign_in(
            phone=state["phone"],
            code=code,
            phone_code_hash=state["phone_code_hash"],
        )
    except SessionPasswordNeededError:
        if not password:
            print("FAIL: account has 2FA — pass password as second arg")
            await client.disconnect()
            return 1
        await client.sign_in(password=password)

    me = await client.get_me()
    print(f"✓ authenticated as @{me.username or me.first_name} (id={me.id})")
    STATE_PATH.unlink(missing_ok=True)  # clear hash
    await client.disconnect()
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    cmd = sys.argv[1]
    if cmd == "send_code":
        return asyncio.run(send_code(sys.argv[2]))
    elif cmd == "sign_in":
        return asyncio.run(sign_in(
            sys.argv[2],
            sys.argv[3] if len(sys.argv) > 3 else None,
        ))
    else:
        print(f"Unknown command: {cmd}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
