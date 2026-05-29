#!/opt/brand-agent/venv/bin/python3
"""citer_thank_drafter — draft thank-you DM/email when a new citation is found.

Triggered by openalex_citation events (fires from emit_event hook).

  citer_thank_drafter.py <slug>

Pipeline:
  1. Read citation event from inbox
  2. Use OpenAlex to look up citer's affiliation, ORCID, email-if-public
  3. Compose two outputs: LinkedIn DM (short, friendly) + email follow-up (formal)
  4. Save drafts to /opt/reports/dms/{slug}/
  5. If Gmail token present → save email as Gmail draft via API
  6. TG notify with both drafts

Gmail draft path works without cookies. LinkedIn DM requires li_at cookie.
"""
import base64
import json
import re
import sqlite3
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

REPORTS_INBOX = Path("/opt/reports/reports/inbox")
DMS_DIR = Path("/opt/reports/dms")
SOUL_PATH = Path("/opt/brand-agent/SOUL.md")
IDENTITY_PATH = Path("/opt/brand-agent/knowledge_base/identity.json")
GMAIL_TOKEN = Path("/opt/brand-agent/secrets/gmail_token.json")
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def _find_inbox(slug):
    matches = sorted(REPORTS_INBOX.glob(f"*_{slug}*.md"))
    return matches[-1] if matches else None


def _parse_citation_event(path):
    text = path.read_text(encoding="utf-8")
    out = {"raw": text}
    m = re.search(r"OpenAlex work (W\d+)", text)
    if m:
        out["work_id"] = m.group(1)
    m = re.search(r"DOI:\s*(\S+)", text)
    if m:
        out["cited_doi"] = m.group(1)
    m = re.search(r"#\s*(.+)$", text, re.MULTILINE)
    if m:
        out["title"] = m.group(1).strip()
    return out


def _lookup_citer(work_id):
    """Find who cited Sergei's work via OpenAlex."""
    if not work_id:
        return None
    try:
        req = urllib.request.Request(
            f"https://api.openalex.org/works?filter=cites:{work_id}"
            f"&per-page=1&select=id,authorships,doi,title,publication_year",
            headers={"User-Agent": "sergei-brand-agent/citer-lookup"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        results = data.get("results", [])
        if not results:
            return None
        citer_work = results[0]
        authors = citer_work.get("authorships", [])
        first = authors[0] if authors else {}
        author = first.get("author", {})
        institutions = first.get("institutions", [])
        return {
            "citer_work_doi": citer_work.get("doi"),
            "citer_work_title": citer_work.get("title", "")[:120],
            "year": citer_work.get("publication_year"),
            "author_name": author.get("display_name"),
            "author_orcid": author.get("orcid"),
            "affiliation": (institutions[0] if institutions else {}).get("display_name"),
        }
    except Exception as e:
        print(f"openalex citer lookup failed: {e}")
        return None


def _compose_drafts(citation, citer, soul):
    citer_str = (
        f"{citer.get('author_name', 'researcher')} "
        f"at {citer.get('affiliation', 'unknown')}, "
        f"work: '{citer.get('citer_work_title', '')}'"
        if citer else "researcher (citer info unavailable)"
    )

    prompt = (
        "You are Sergei Solovev. Someone just cited one of your preprints. "
        "Write TWO outputs: a short LinkedIn DM (3 sentences max, warm, genuine) "
        "AND a formal email follow-up (5-6 sentences, suggest exchange of preprints "
        "or call). English unless citer's affiliation is clearly Russian.\n\n"
        f"YOUR VOICE (from SOUL.md):\n{soul[:1000]}\n\n"
        f"YOUR CITED WORK: {citation.get('title', '?')}\n"
        f"CITED DOI: {citation.get('cited_doi', '?')}\n\n"
        f"CITER: {citer_str}\n"
        f"CITER ORCID: {(citer or {}).get('author_orcid', 'unknown')}\n\n"
        "Output format:\n"
        "=== LINKEDIN DM ===\n"
        "<3 sentences>\n"
        "=== EMAIL ===\n"
        "Subject: <line>\n\n"
        "<body 5-6 sentences>\n"
        "—\nSergei Solovev\n"
        "=== END ===\n\n"
        "Do NOT use exclamation marks. No marketing fluff. Reference one specific "
        "thing from the citer's work if known."
    )
    try:
        r = subprocess.run(
            ["claude", "-p", "--model", "claude-sonnet-4-6", prompt],
            capture_output=True, text=True, timeout=90,
        )
        return r.stdout if r.returncode == 0 else ""
    except Exception as e:
        print(f"compose error: {e}")
        return ""


def _split_drafts(text):
    """Split combined Composer output into LinkedIn DM + email parts."""
    dm = ""
    email_subj = ""
    email_body = ""
    m_dm = re.search(r"=== LINKEDIN DM ===(.+?)=== EMAIL ===", text, re.DOTALL)
    if m_dm:
        dm = m_dm.group(1).strip()
    m_email = re.search(r"=== EMAIL ===(.+?)=== END ===", text, re.DOTALL)
    if m_email:
        email_text = m_email.group(1).strip()
        m_subj = re.match(r"Subject:\s*(.+?)\n", email_text)
        if m_subj:
            email_subj = m_subj.group(1).strip()
            email_body = email_text[m_subj.end():].strip()
        else:
            email_body = email_text
    return dm, email_subj, email_body


def _save_gmail_draft(subject, body, to):
    """Save the email as a Gmail draft (not send — Sergei reviews + sends)."""
    if not GMAIL_TOKEN.exists() or not to:
        return None
    try:
        creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN), SCOPES)
        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        msg = EmailMessage()
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        draft = service.users().drafts().create(
            userId="me", body={"message": {"raw": raw}},
        ).execute()
        return draft.get("id")
    except Exception as e:
        print(f"gmail draft save failed: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print("usage: citer_thank_drafter.py <slug>")
        return 1
    slug = sys.argv[1]
    inbox = _find_inbox(slug)
    if not inbox:
        print(f"no inbox file for slug={slug}")
        return 1
    citation = _parse_citation_event(inbox)
    citer = _lookup_citer(citation.get("work_id"))
    soul = SOUL_PATH.read_text(encoding="utf-8") if SOUL_PATH.exists() else ""

    text = _compose_drafts(citation, citer, soul)
    dm, subject, body = _split_drafts(text)

    DMS_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-z0-9-]+", "-", slug.lower())[:50]
    today = datetime.utcnow().date().isoformat()
    out_dir = DMS_DIR / safe
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"{today}-linkedin-dm.md").write_text(dm or "(empty)", encoding="utf-8")
    (out_dir / f"{today}-email.md").write_text(
        f"Subject: {subject}\nTo: {(citer or {}).get('author_orcid', '?')}\n\n{body}",
        encoding="utf-8",
    )

    # Try to find email — OpenAlex doesn't expose, but we can search for ORCID
    # public email later. For now save draft to Gmail with placeholder TO.
    gmail_draft_id = None
    if subject and body and citer and citer.get("author_orcid"):
        # Placeholder recipient — Sergei fills in actual email when opening draft
        gmail_draft_id = _save_gmail_draft(
            subject, body + "\n\n(Auto-drafted by agent — verify recipient before send)",
            "draft@example.com",  # placeholder; opens in Gmail UI for edit
        )

    # TG notify
    summary = (
        f"📨 *Citer thank-you drafts ready*\n\n"
        f"Cited work: {citation.get('title', '?')[:80]}\n"
        f"Citer: {citer_str_short(citer)}\n\n"
        f"LinkedIn DM:\n{(dm or '(failed)')[:300]}\n\n"
        f"Email subject: {subject}\n"
        f"Gmail draft: "
        + (f"[draft saved, edit in Gmail UI]" if gmail_draft_id else "[no token, file-only]")
        + f"\n\nFiles:\n"
        f"https://github.com/SergeySolovyev/sergei-brand-agent-reports/tree/main/dms/{safe}"
    )
    subprocess.run(["/usr/local/bin/tg_send", summary], check=False)

    # Git commit
    for fname in (f"{today}-linkedin-dm.md", f"{today}-email.md"):
        try:
            subprocess.run(
                ["git", "-C", "/opt/reports", "add",
                 f"dms/{safe}/{fname}"], check=False,
            )
        except Exception:
            pass
    subprocess.run(
        ["git", "-C", "/opt/reports", "-c", "user.name=openclaw-agent",
         "-c", "user.email=agent@sergeisolovev.com",
         "commit", "-m", f"citer thank-you drafts: {slug[:50]}", "--quiet"],
        check=False,
    )
    subprocess.run(["git", "-C", "/opt/reports", "push", "--quiet"], check=False)
    return 0


def citer_str_short(citer):
    if not citer:
        return "unknown"
    return f"{citer.get('author_name', '?')} ({citer.get('affiliation', '?')[:30]})"


if __name__ == "__main__":
    sys.exit(main())
