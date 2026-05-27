"""
telegram_bot.py — sergei-brand-agent control interface.

Provides Sergei with a small command surface inside Telegram:
  /status         — agent state, pending approvals
  /approve <id>   — approve a pending Tier-3 draft
  /reject <id> <reason>  — reject and pass back to Composer for revision
  /pause          — emergency stop (sets agent_state.emergency_pause = true)
  /resume         — clear pause
  /digest         — manually trigger weekly digest
  /pulse          — manually trigger monitoring pass

Designed for polling mode (works behind NAT, no webhook server required).
Run alongside orchestrator.py in Docker Compose.

Requires: python-telegram-bot >= 21.0
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Wiring
# ---------------------------------------------------------------------------
try:
    from telegram import Update
    from telegram.ext import (
        Application,
        ApplicationBuilder,
        CommandHandler,
        ContextTypes,
    )
except ImportError as exc:
    print("Install python-telegram-bot: pip install 'python-telegram-bot>=21'", file=sys.stderr)
    raise SystemExit(1) from exc

REPO_ROOT = Path(__file__).resolve().parent
STATE_DB = REPO_ROOT / "data" / "state.sqlite"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s | %(message)s",
)
log = logging.getLogger("telegram-bot")


@contextmanager
def db():
    conn = sqlite3.connect(STATE_DB)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def allowed_user(update: Update) -> bool:
    """Reject messages from non-allowlisted users."""
    allowed_ids = {
        int(uid) for uid in os.environ.get("TELEGRAM_ALLOWED_USERS", "").split(",") if uid
    }
    if not allowed_ids:
        return True  # if not set, allow (dev mode)
    return update.effective_user and update.effective_user.id in allowed_ids


def require_auth(handler):
    """Decorator: silently drop messages from unauthorized users."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not allowed_user(update):
            log.warning(f"Unauthorized user {update.effective_user.id} tried {handler.__name__}")
            return
        return await handler(update, context)
    return wrapper


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------
@require_auth
async def cmd_start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "sergei-brand-agent control interface\n\n"
        "Commands:\n"
        "  /status        agent state + pending approvals\n"
        "  /approve <id>  approve a Tier-3 draft\n"
        "  /reject <id> <reason>  reject a draft\n"
        "  /pause         emergency stop\n"
        "  /resume        clear pause\n"
        "  /digest        manually trigger weekly digest\n"
        "  /pulse         manually run monitoring"
    )


@require_auth
async def cmd_status(update: Update, _: ContextTypes.DEFAULT_TYPE):
    with db() as conn:
        events = conn.execute(
            "SELECT source, kind, subject, severity, ts FROM events "
            "WHERE ts >= datetime('now', '-24 hours') ORDER BY ts DESC LIMIT 10"
        ).fetchall()
        pending = conn.execute(
            """
            SELECT d.draft_path, d.channel, d.topic
            FROM drafts d
            LEFT JOIN critic_verdicts cv ON d.draft_path = cv.draft_path
            LEFT JOIN approvals a ON d.draft_path = a.draft_path
            WHERE a.id IS NULL AND cv.verdict = 'PASS'
            ORDER BY d.created_at DESC LIMIT 10
            """
        ).fetchall()
        paused = conn.execute(
            "SELECT value FROM agent_state WHERE key = 'emergency_pause'"
        ).fetchone()

    state = "🔴 PAUSED" if paused and paused["value"] == "true" else "🟢 RUNNING"
    body = f"*Agent*: {state}\n"
    body += f"*Events (24h)*: {len(events)}\n"
    body += f"*Pending approve*: {len(pending)}\n\n"

    if pending:
        body += "*Awaiting /approve*:\n"
        for d in pending[:5]:
            slug = Path(d["draft_path"]).stem
            body += f"  • `{slug}` — {d['channel']} — {d['topic']}\n"
    if events:
        body += "\n*Recent events*:\n"
        for e in events[:5]:
            sev = {"low": "·", "medium": "•", "high": "❗", "critical": "🚨"}.get(e["severity"], "•")
            body += f"  {sev} {e['source']} → {e['kind']}: {e['subject']}\n"

    await update.message.reply_text(body, parse_mode="Markdown")


@require_auth
async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /approve <draft_slug>")
        return
    slug = context.args[0]
    with db() as conn:
        row = conn.execute(
            "SELECT draft_path, channel, topic FROM drafts WHERE draft_path LIKE ?",
            (f"%{slug}%",),
        ).fetchone()
        if not row:
            await update.message.reply_text(f"❌ No draft matching `{slug}`", parse_mode="Markdown")
            return
        # Verify Critic PASS
        verdict_row = conn.execute(
            "SELECT verdict FROM critic_verdicts WHERE draft_path = ? ORDER BY ts DESC LIMIT 1",
            (row["draft_path"],),
        ).fetchone()
        if not verdict_row or verdict_row["verdict"] != "PASS":
            await update.message.reply_text(
                f"⚠️ Draft `{slug}` doesn't have Critic PASS yet (verdict: {verdict_row['verdict'] if verdict_row else 'NONE'})",
                parse_mode="Markdown",
            )
            return
        conn.execute(
            "INSERT INTO approvals (draft_path, verdict, approver, ts) VALUES (?, 'approved', ?, ?)",
            (row["draft_path"], update.effective_user.username or str(update.effective_user.id),
             datetime.now(timezone.utc).isoformat()),
        )
    await update.message.reply_text(
        f"✅ Approved: *{row['channel']}* — {row['topic']}\nPublisher will fire in next cycle.",
        parse_mode="Markdown",
    )


@require_auth
async def cmd_reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /reject <draft_slug> [reason]")
        return
    slug = context.args[0]
    reason = " ".join(context.args[1:]) if len(context.args) > 1 else "no reason given"
    with db() as conn:
        row = conn.execute(
            "SELECT draft_path FROM drafts WHERE draft_path LIKE ?",
            (f"%{slug}%",),
        ).fetchone()
        if not row:
            await update.message.reply_text(f"❌ No draft matching `{slug}`", parse_mode="Markdown")
            return
        conn.execute(
            "INSERT INTO approvals (draft_path, verdict, approver, ts, note) "
            "VALUES (?, 'rejected', ?, ?, ?)",
            (row["draft_path"],
             update.effective_user.username or str(update.effective_user.id),
             datetime.now(timezone.utc).isoformat(), reason),
        )
        # Emit event for Composer to pick up & revise
        conn.execute(
            "INSERT INTO events (source, kind, subject, severity, ts, raw) "
            "VALUES ('human', 'rejection', ?, 'medium', ?, ?)",
            (row["draft_path"], datetime.now(timezone.utc).isoformat(),
             json.dumps({"reason": reason, "approver": update.effective_user.username})),
        )
    await update.message.reply_text(f"❌ Rejected. Composer will revise.\nReason: {reason}")


@require_auth
async def cmd_pause(update: Update, _: ContextTypes.DEFAULT_TYPE):
    with db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO agent_state (key, value, updated_at) "
            "VALUES ('emergency_pause', 'true', ?)",
            (datetime.now(timezone.utc).isoformat(),),
        )
    await update.message.reply_text("🛑 *Agent paused.* All skills blocked until /resume.", parse_mode="Markdown")


@require_auth
async def cmd_resume(update: Update, _: ContextTypes.DEFAULT_TYPE):
    with db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO agent_state (key, value, updated_at) "
            "VALUES ('emergency_pause', 'false', ?)",
            (datetime.now(timezone.utc).isoformat(),),
        )
    await update.message.reply_text("✅ *Agent resumed.*", parse_mode="Markdown")


@require_auth
async def cmd_ack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Acknowledge a CRITICAL event so OpenClaw stops re-pinging."""
    if not context.args:
        await update.message.reply_text("Usage: /ack <slug>")
        return
    slug = context.args[0]
    with db() as conn:
        row = conn.execute(
            "SELECT slug, kind, title, severity FROM ack_pending "
            "WHERE slug = ? AND acked_at IS NULL",
            (slug,),
        ).fetchone()
        if not row:
            await update.message.reply_text(
                f"No pending critical event matching `{slug}` (already acked or expired)",
                parse_mode="Markdown",
            )
            return
        conn.execute(
            "UPDATE ack_pending SET acked_at = ?, acked_by = ? WHERE slug = ?",
            (datetime.now(timezone.utc).isoformat(),
             update.effective_user.username or str(update.effective_user.id),
             slug),
        )
    await update.message.reply_text(
        f"✅ ACKed: *{row['kind']}* — {row['title']}\nRetry loop stopped.",
        parse_mode="Markdown",
    )


@require_auth
async def cmd_digest(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Queuing weekly_digest...")
    # In production, push an event the scheduler picks up
    with db() as conn:
        conn.execute(
            "INSERT INTO events (source, kind, subject, severity, ts) "
            "VALUES ('human', 'manual_trigger', 'weekly_digest', 'low', ?)",
            (datetime.now(timezone.utc).isoformat(),),
        )
    await update.message.reply_text("Queued. Result will arrive shortly.")


@require_auth
async def cmd_pulse(update: Update, _: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Queuing monitoring pulse...")
    with db() as conn:
        conn.execute(
            "INSERT INTO events (source, kind, subject, severity, ts) "
            "VALUES ('human', 'manual_trigger', 'check_research_visibility', 'low', ?)",
            (datetime.now(timezone.utc).isoformat(),),
        )
    await update.message.reply_text("Queued. Watch /status for results.")


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
def build_application() -> Application:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN not set in environment")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("approve", cmd_approve))
    app.add_handler(CommandHandler("reject", cmd_reject))
    app.add_handler(CommandHandler("ack", cmd_ack))
    app.add_handler(CommandHandler("pause", cmd_pause))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("digest", cmd_digest))
    app.add_handler(CommandHandler("pulse", cmd_pulse))
    return app


def main() -> int:
    app = build_application()
    log.info("Telegram bot starting (polling mode)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
    return 0


if __name__ == "__main__":
    sys.exit(main())
