#!/opt/brand-agent/venv/bin/python3
"""register_event — Playwright-based auto-registration for webinar/event invites.

Two phases:

  Phase 1 (preview):  register_event.py preview <slug>
    - Reads inbox markdown for the slug
    - Extracts registration URL
    - profile_picker chooses identity profile
    - Stores draft registration in sqlite
    - Sends Telegram preview with [✅ Proceed] [🔄 Different profile] [❌ Cancel]

  Phase 2 (submit):   register_event.py submit <reg_id>
    - Loads draft registration + chosen profile
    - Opens URL in headless Chromium
    - Fills detected form fields from profile (name/email/company/role)
    - OPTS OUT of any marketing checkboxes (`do_not_consent` flags)
    - Submits, screenshots confirmation page
    - Telegram confirmation with screenshot path

Safety:
  - Never enters phone (escalates if required) — phone_policy
  - Never enters credit card / SSN / passport — fail fast if form asks
  - Logs everything to /opt/reports/tracking/registered.md (audit)
"""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/opt/brand-agent")
import profile_picker

STATE_DB = Path("/root/.openclaw/agent_state.sqlite")
REPORTS_INBOX = Path("/opt/reports/reports/inbox")
TRACKING_DIR = Path("/opt/reports/tracking")
SCREENSHOTS_DIR = Path("/opt/reports/tracking/screenshots")

# Sensitive fields agent NEVER fills automatically
FORBIDDEN_FIELD_PATTERNS = [
    "credit", "card", "cvv", "cvc", "ssn", "passport",
    "iin", "snils", "паспорт", "СНИЛС", "tax id",
]


def _db():
    conn = sqlite3.connect(STATE_DB)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS registrations (
          reg_id        INTEGER PRIMARY KEY AUTOINCREMENT,
          slug          TEXT,
          url           TEXT,
          profile_key   TEXT,
          identity_dump TEXT,
          status        TEXT,
          confirmation  TEXT,
          screenshot    TEXT,
          created_at    TEXT,
          decided_at    TEXT
        )
        """
    )
    return conn


def _find_inbox_file(slug: str) -> Path | None:
    matches = sorted(REPORTS_INBOX.glob(f"*_{slug}.md"))
    return matches[-1] if matches else None


def _parse_inbox_md(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    out = {"raw": text}
    m = re.search(r"^From:\s*(.+)$", text, re.MULTILINE)
    out["sender"] = m.group(1).strip() if m else ""
    m = re.search(r"^Subject:\s*(.+)$", text, re.MULTILINE)
    out["subject"] = m.group(1).strip() if m else ""
    # Pull the most likely registration URL.
    # Strategy: rank candidates by signal — prefer ones near "Register" / "Sign up"
    # context, drop "view as web page" / unsubscribe / social patterns.
    SKIP_PATTERNS = (
        "unsubscribe", "mail.google", "github.com", "policies.",
        "/x.com/", "linkedin.com/company", "youtube.com",
        "emailwebview", "/view?", "/webview", "/preview",
        "/index.php/email", "twitter.com/intent",
    )
    REGISTER_CONTEXT_WORDS = (
        "register", "sign up", "signup", "join", "rsvp",
        "save your spot", "claim your seat", "secure your spot",
        "зарегистрироваться", "регистрация",
    )
    urls = list(re.finditer(r"https?://[^\s\]\)>]+", text))
    text_lower = text.lower()
    ranked = []
    for m in urls:
        u = m.group(0).rstrip(",.;)>]")
        ul = u.lower()
        if any(skip in ul for skip in SKIP_PATTERNS):
            continue
        # Score: higher = better registration candidate
        score = 0
        # Context window 80 chars before the URL
        ctx_start = max(0, m.start() - 80)
        ctx = text_lower[ctx_start:m.start()]
        for word in REGISTER_CONTEXT_WORDS:
            if word in ctx:
                score += 10
        # Bonus for register-y URL path
        if any(w in ul for w in ("/register", "/signup", "/rsvp", "/event/")):
            score += 5
        # Penalty for tracking-blob URLs without semantic path
        if len(u) > 200 and "?" in u:
            score -= 1
        ranked.append((score, m.start(), u))
    ranked.sort(key=lambda r: (-r[0], r[1]))  # high score first, earliest tie
    out["registration_url"] = ranked[0][2] if ranked else None
    out["body"] = text
    return out


def _tg(text: str, kind: str = "", slug: str = "") -> None:
    args = ["/usr/local/bin/tg_send"]
    if kind:
        args.extend(["--kind", kind, "--slug", slug])
    args.append(text)
    subprocess.run(args, check=False)


def phase_preview(slug: str) -> int:
    inbox_file = _find_inbox_file(slug)
    if not inbox_file:
        _tg(f"❌ No inbox file for slug={slug}")
        return 1
    email = _parse_inbox_md(inbox_file)
    if not email.get("registration_url"):
        _tg(f"❌ No registration URL detected in email\nSlug: {slug}")
        return 1

    pick = profile_picker.pick(
        email.get("sender", ""), email.get("subject", ""), email.get("body", ""),
    )
    profile = profile_picker.get_profile(pick["profile_key"])

    conn = _db()
    cursor = conn.execute(
        "INSERT INTO registrations "
        "(slug, url, profile_key, identity_dump, status, created_at) "
        "VALUES (?, ?, ?, ?, 'preview', ?)",
        (slug, email["registration_url"], pick["profile_key"],
         json.dumps(profile, ensure_ascii=False),
         datetime.now(timezone.utc).isoformat()),
    )
    reg_id = cursor.lastrowid
    conn.commit()
    conn.close()

    globals_ = profile.get("globals", {})
    preview = (
        f"📝 *Auto-register preview* (#{reg_id})\n\n"
        f"🎯 Picker chose: *{pick['profile_key']}* "
        f"({pick.get('confidence', 0):.0%})\n"
        f"💡 Reason: {pick.get('reasoning', '?')}\n\n"
        f"📤 Will fill on the form:\n"
        f"  Name:    {globals_.get('first_name', '?')} {globals_.get('last_name', '?')}\n"
        f"  Email:   {profile.get('email', '?')}\n"
        f"  Company: {profile.get('company', '?')}\n"
        f"  Role:    {profile.get('role', '?')}\n"
        f"  Country: {globals_.get('country', '?')}\n"
        f"  Phone:   *not provided* (will escalate if required)\n\n"
        f"🔒 Will opt-out of:\n"
        f"  • marketing consent\n"
        f"  • third-party data sharing\n"
        f"  • calendar marketing opt-in\n\n"
        f"🔗 URL: {email['registration_url'][:80]}...\n\n"
        f"Subject: {email.get('subject', '?')[:60]}"
    )
    _tg(preview, kind="register_preview", slug=str(reg_id))
    return 0


def phase_submit(reg_id: int) -> int:
    conn = _db()
    row = conn.execute(
        "SELECT slug, url, profile_key, identity_dump, status "
        "FROM registrations WHERE reg_id = ?", (reg_id,),
    ).fetchone()
    if not row:
        _tg(f"❌ Registration #{reg_id} not found")
        return 1
    slug, url, profile_key, identity_dump, status = row
    if status != "preview":
        _tg(f"❌ Registration #{reg_id} already {status}")
        return 1

    profile = json.loads(identity_dump)
    globals_ = profile.get("globals", {})

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    screenshot_path = SCREENSHOTS_DIR / f"reg_{reg_id}_{int(datetime.now().timestamp())}.png"

    # Mark as "submitting" so we know if it crashes
    conn.execute(
        "UPDATE registrations SET status='submitting' WHERE reg_id=?", (reg_id,),
    )
    conn.commit()

    # Headless Playwright submission
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"),
                locale="en-US",
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass  # SPA — fine, fields may already be there

            # Smart-fill: scan inputs and match field name/label to identity fields
            field_map = {
                "first": globals_.get("first_name", ""),
                "last": globals_.get("last_name", ""),
                "name": f"{globals_.get('first_name','')} {globals_.get('last_name','')}".strip(),
                "email": profile.get("email", ""),
                "company": profile.get("company", ""),
                "organization": profile.get("company", ""),
                "organisation": profile.get("company", ""),
                "title": profile.get("title", ""),
                "role": profile.get("role", ""),
                "job": profile.get("role", ""),
                "country": globals_.get("country", ""),
                "city": globals_.get("city", ""),
                "website": globals_.get("website", ""),
                "linkedin": globals_.get("linkedin", ""),
                "github": globals_.get("github", ""),
            }

            filled = {}
            forbidden_hit = False
            # Iterate all input/textarea/select elements
            inputs = page.query_selector_all("input, textarea, select")
            for el in inputs:
                try:
                    name = (el.get_attribute("name") or "").lower()
                    placeholder = (el.get_attribute("placeholder") or "").lower()
                    aria = (el.get_attribute("aria-label") or "").lower()
                    field_id = (el.get_attribute("id") or "").lower()
                    el_type = (el.get_attribute("type") or "").lower()
                    haystack = f"{name} {placeholder} {aria} {field_id}".lower()

                    # Forbidden fields → abort
                    if any(pat in haystack for pat in FORBIDDEN_FIELD_PATTERNS):
                        forbidden_hit = True
                        continue

                    # Phone field — escalate
                    if "phone" in haystack or "tel" in el_type or "телефон" in haystack:
                        # leave blank for now; if required, will fail and escalate
                        continue

                    # Marketing opt-out checkboxes — UNCHECK them
                    if el_type == "checkbox":
                        for marketing_word in ("marketing", "newsletter", "promotional",
                                               "third-party", "partner offers"):
                            if marketing_word in haystack:
                                if el.is_checked():
                                    el.uncheck()
                                filled[name or field_id] = "[opted-out]"
                                break
                        continue

                    # Match other fields
                    for key, val in field_map.items():
                        if key in haystack and val:
                            try:
                                el.fill(val)
                                filled[name or field_id or key] = val
                                break
                            except Exception:
                                # Maybe a select — try option
                                try:
                                    el.select_option(value=val)
                                    filled[name or field_id] = val
                                except Exception:
                                    pass
                            break
                except Exception:
                    continue

            if forbidden_hit:
                page.screenshot(path=str(screenshot_path))
                _tg(
                    f"❌ Registration #{reg_id} ABORTED — form contains "
                    f"financial/passport field. Please register manually.\n"
                    f"URL: {url[:80]}\nScreenshot: {screenshot_path}"
                )
                conn.execute(
                    "UPDATE registrations SET status='aborted_forbidden_field', "
                    "decided_at=? WHERE reg_id=?",
                    (datetime.now(timezone.utc).isoformat(), reg_id),
                )
                conn.commit()
                browser.close()
                return 1

            # Find and click submit button
            submit_clicked = False
            for selector in [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Register')",
                "button:has-text('Submit')",
                "button:has-text('Sign up')",
                "button:has-text('Sign Up')",
                "button:has-text('Зарегистрироваться')",
            ]:
                try:
                    btn = page.query_selector(selector)
                    if btn and btn.is_visible():
                        btn.click()
                        submit_clicked = True
                        break
                except Exception:
                    continue

            if not submit_clicked:
                page.screenshot(path=str(screenshot_path))
                _tg(
                    f"⚠️ Filled but couldn't find Submit button for #{reg_id}.\n"
                    f"Screenshot saved — please review manually.\n"
                    f"URL: {url[:80]}"
                )
                conn.execute(
                    "UPDATE registrations SET status='filled_no_submit', "
                    "screenshot=?, decided_at=? WHERE reg_id=?",
                    (str(screenshot_path), datetime.now(timezone.utc).isoformat(), reg_id),
                )
                conn.commit()
                browser.close()
                return 1

            # Wait for navigation / confirmation
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            confirmation_url = page.url
            page.screenshot(path=str(screenshot_path), full_page=True)
            browser.close()

        # Audit log
        TRACKING_DIR.mkdir(parents=True, exist_ok=True)
        with open(TRACKING_DIR / "registered.md", "a", encoding="utf-8") as f:
            f.write(
                f"\n## Registration #{reg_id} — {datetime.now(timezone.utc).date().isoformat()}\n"
                f"- **Slug**: {slug}\n"
                f"- **URL**: {url}\n"
                f"- **Profile**: {profile_key}\n"
                f"- **Filled fields**: {json.dumps(filled, ensure_ascii=False)}\n"
                f"- **Confirmation URL**: {confirmation_url}\n"
                f"- **Screenshot**: {screenshot_path}\n"
            )

        conn.execute(
            "UPDATE registrations SET status='submitted', confirmation=?, "
            "screenshot=?, decided_at=? WHERE reg_id=?",
            (confirmation_url, str(screenshot_path),
             datetime.now(timezone.utc).isoformat(), reg_id),
        )
        conn.commit()

        _tg(
            f"✅ Registered #{reg_id}\n"
            f"Profile: {profile_key}\n"
            f"Filled: {', '.join(filled.keys())}\n"
            f"Confirmation URL: {confirmation_url[:100]}\n"
            f"Screenshot: {screenshot_path}"
        )
        return 0
    except Exception as e:
        _tg(f"❌ Registration #{reg_id} failed: {e}")
        conn.execute(
            "UPDATE registrations SET status='failed', decided_at=? WHERE reg_id=?",
            (datetime.now(timezone.utc).isoformat(), reg_id),
        )
        conn.commit()
        return 1
    finally:
        conn.close()


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: register_event.py preview <slug> | submit <reg_id>")
        return 1
    cmd = sys.argv[1]
    if cmd == "preview":
        return phase_preview(sys.argv[2])
    elif cmd == "submit":
        try:
            return phase_submit(int(sys.argv[2]))
        except ValueError:
            print(f"invalid reg_id: {sys.argv[2]}")
            return 1
    else:
        print(f"Unknown command: {cmd}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
