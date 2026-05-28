"""gmail_pluck — fetch most recent message matching a query, return text content.

Used for one-off email-driven flows: e.g., get magic link or one-time PIN
from a service email right after it arrives.

Usage:
  gmail_pluck.py "from:noreply@ethglobal.com"
  gmail_pluck.py "subject:ETHGlobal verification"
"""
import base64
import sys
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN = Path("/opt/brand-agent/secrets/gmail_token.json")
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def main():
    if len(sys.argv) < 2:
        print("usage: gmail_pluck.py '<gmail query>'")
        return 1
    query = sys.argv[1]
    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    svc = build("gmail", "v1", credentials=creds, cache_discovery=False)
    listing = svc.users().messages().list(
        userId="me", q=query, maxResults=1,
    ).execute()
    msgs = listing.get("messages", [])
    if not msgs:
        print(f"NO_MATCH for query: {query}")
        return 2
    msg = svc.users().messages().get(
        userId="me", id=msgs[0]["id"], format="full",
    ).execute()
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    print(f"=== From: {headers.get('From','?')}")
    print(f"=== Subject: {headers.get('Subject','?')}")
    print(f"=== Date: {headers.get('Date','?')}")
    print()

    def walk(part):
        # Prefer text/plain, fall back to text/html
        out = {"plain": "", "html": ""}
        def _w(p):
            mt = p.get("mimeType", "")
            if mt == "text/plain" and "data" in p.get("body", {}):
                try:
                    out["plain"] = base64.urlsafe_b64decode(
                        p["body"]["data"]).decode("utf-8", errors="ignore")
                except Exception:
                    pass
            elif mt == "text/html" and "data" in p.get("body", {}) and not out["html"]:
                try:
                    out["html"] = base64.urlsafe_b64decode(
                        p["body"]["data"]).decode("utf-8", errors="ignore")
                except Exception:
                    pass
            for sub in p.get("parts", []) or []:
                _w(sub)
        _w(part)
        return out

    bodies = walk(msg["payload"])
    print("--- text/plain ---")
    print(bodies["plain"][:4000])
    if not bodies["plain"]:
        print("--- text/html (no plain) ---")
        print(bodies["html"][:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
