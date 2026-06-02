import sys
from importlib.machinery import SourceFileLoader
sys.path.insert(0, "/opt/brand-agent")
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import triage
etg = SourceFileLoader("etg", "/usr/local/bin/email_triage_gmail").load_module()

creds = Credentials.from_authorized_user_file(
    "/opt/brand-agent/secrets/gmail_token.json",
    ["https://www.googleapis.com/auth/gmail.modify"],
)
svc = build("gmail", "v1", credentials=creds, cache_discovery=False)
lst = svc.users().messages().list(
    userId="me", labelIds=["INBOX", "UNREAD"], maxResults=15
).execute()
for ref in lst.get("messages", [])[:15]:
    m = svc.users().messages().get(userId="me", id=ref["id"], format="full").execute()
    H = {h["name"]: h["value"] for h in m["payload"]["headers"]}
    subj = H.get("Subject", "(no subj)")[:50]
    sender = H.get("From", "?")[:33]
    body = etg._extract_body(m["payload"])
    if etg._is_marketing(H, sender, subj):
        print("  MKT-SKIP  | {:33} | {}".format(sender, subj))
    else:
        d = triage.triage(sender, subj, body)
        print("  {:8}/{:6} | {:33} | {}".format(
            d["decision"], d["severity"], sender, subj))
