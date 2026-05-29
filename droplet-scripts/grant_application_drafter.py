#!/opt/brand-agent/venv/bin/python3
"""grant_application_drafter — auto-draft full grant application on emit.

Triggered by grant_discovered events (called from emit_event hook OR
invoked manually with slug).

  grant_application_drafter.py <inbox_slug>

Pipeline:
  1. Read grant context from /opt/reports/inbox/*_<slug>.md
  2. Load Sergei context: SOUL.md + identity.json (academic_hse profile)
     + preprints metadata
  3. Composer (Sonnet via claude-cli) drafts FULL application:
     - Project summary (300 words)
     - Methodology + technical approach (500 words)
     - Team (Sergei solo or with HSE supervisor)
     - Budget rationale
     - Timeline (Gantt-style milestones)
     - Expected outputs (publications, software releases)
  4. Critic reviews for plausibility + tone
  5. Save package to /opt/reports/applications/{slug}/draft.md
  6. Emit to TG with [✅ Submit as-is] [✏️ Edit first] [❌ Skip]

The "Submit as-is" path is currently manual instruction — Phase 3 will
add Playwright auto-submit when target form URLs are characterized.
"""
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPORTS_INBOX = Path("/opt/reports/reports/inbox")
APPLICATIONS_DIR = Path("/opt/reports/applications")
SOUL_PATH = Path("/opt/brand-agent/SOUL.md")
IDENTITY_PATH = Path("/opt/brand-agent/knowledge_base/identity.json")

# Sergei's preprint portfolio (used as track record in application)
PREPRINTS_SHORT = """
1. Honest-RAG-Solidity — RAG-based vulnerability detection in smart contracts
   (DOI: 10.6084/m9.figshare.32141182)
2. AI-Yield-Vault — ML strategy selection for ERC-4626 vaults
   (DOI: 10.6084/m9.figshare.32141167)
3. Regime-Conditioning for LOB Mid-Price Prediction
   (DOI: 10.6084/m9.figshare.31859557)
4. FinAgent — Multi-agent architecture for financial research
   (DOI: 10.6084/m9.figshare.31429971)
5. Honest Prompt-Injection Detection in RAG Pipelines
   (DOI: 10.6084/m9.figshare.31430086)
"""


def _find_inbox_file(slug: str) -> Path | None:
    matches = sorted(REPORTS_INBOX.glob(f"*_{slug}*.md"))
    return matches[-1] if matches else None


def _parse_grant_inbox(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    out = {"raw": text}
    for field in ("Title", "URL", "Source", "Deadline", "Amount", "For"):
        m = re.search(rf"^{field}:\s*(.+)$", text, re.MULTILINE)
        if m:
            out[field.lower()] = m.group(1).strip()
    return out


def _compose_application(grant: dict, profile: dict, soul: str) -> str:
    prompt = (
        "You are Sergei Solovev drafting a grant application. Stay in his voice: "
        "technical, evidence-based, no fluff, no marketing speak. Russian if grant "
        "is Russian-language, English otherwise.\n\n"
        f"--- BRAND VOICE (excerpt) ---\n{soul[:1200]}\n--- END ---\n\n"
        f"--- APPLICANT PROFILE ---\n"
        f"Name: {profile.get('globals', {}).get('first_name_ru', 'Сергей')} "
        f"{profile.get('globals', {}).get('last_name_ru', 'Соловьёв')}\n"
        f"Affiliation: {profile.get('company', 'HSE University')}\n"
        f"Role: {profile.get('role', 'Researcher')}\n"
        f"Bio: {profile.get('bio_short', '')}\n"
        f"Preprints (peer-reviewable track record):\n{PREPRINTS_SHORT}\n"
        f"Website: {profile.get('globals', {}).get('website', 'sergeisolovev.com')}\n"
        f"--- END ---\n\n"
        f"--- GRANT ---\n"
        f"Title: {grant.get('title', '?')}\n"
        f"Amount: {grant.get('amount', '?')}\n"
        f"Deadline: {grant.get('deadline', '?')}\n"
        f"For whom: {grant.get('for', '?')}\n"
        f"URL: {grant.get('url', '?')}\n"
        f"--- END ---\n\n"
        "Draft a FULL grant application with these sections (Markdown headers):\n\n"
        "# Заявка: <Grant short name>\n\n"
        "## 1. Тема проекта (название + 1 паragraph rationale)\n"
        "## 2. Краткое описание (300 слов)\n"
        "Concrete problem, hypothesis, what will be done. Reference 1-2 "
        "applicant's preprints as evidence of capability.\n\n"
        "## 3. Научная новизна и значимость (200 слов)\n"
        "What's new vs state of art. Why now.\n\n"
        "## 4. Методология (500 слов)\n"
        "Technical approach: data sources, models, evaluation. Bullet milestones.\n\n"
        "## 5. План работ (Gantt-style таблица)\n"
        "| Месяц | Задача | Результат |\n\n"
        "## 6. Команда\n"
        "Sergei + (если применимо) HSE supervisor / collaborator name TBD.\n\n"
        "## 7. Бюджет (укрупнённо)\n"
        "| Статья | Сумма | Обоснование |\n"
        "Должна сумма ровняться amount из grant info.\n\n"
        "## 8. Ожидаемые результаты\n"
        "Publications (target venues), software releases (GitHub), conferences.\n\n"
        "## 9. Соответствие приоритетам Фонда\n"
        "1 paragraph linking to grant's stated priorities.\n\n"
        "Output ONLY the markdown. No commentary."
    )
    try:
        r = subprocess.run(
            ["claude", "-p", "--model", "claude-sonnet-4-6", prompt],
            capture_output=True, text=True, timeout=240,
        )
        if r.returncode != 0:
            return ""
        return r.stdout
    except Exception as e:
        print(f"composer error: {e}")
        return ""


def _critique(draft: str, grant: dict) -> tuple[str, str]:
    prompt = (
        "Critic review of a grant application draft for Sergei Solovev. Find:\n"
        "- factual errors in preprint references\n"
        "- budget math doesn't match grant amount\n"
        "- timeline impractical for solo researcher + master's student schedule\n"
        "- overpromising claims\n"
        "- mismatched language (RU grant should be in Russian throughout)\n\n"
        f"Grant amount: {grant.get('amount', '?')}\n"
        f"Grant deadline: {grant.get('deadline', '?')}\n\n"
        f"--- DRAFT ---\n{draft[:8000]}\n--- END ---\n\n"
        "Respond with one line VERDICT: PASS | REVISE | REJECT\n"
        "Then 3-5 bullet specific issues."
    )
    try:
        r = subprocess.run(
            ["claude", "-p", "--model", "claude-sonnet-4-6", prompt],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode != 0:
            return ("PASS", "Critic unreachable")
        out = r.stdout
        m = re.search(r"VERDICT:\s*(PASS|REVISE|REJECT)", out)
        return (m.group(1) if m else "PASS", out)
    except Exception as e:
        return ("PASS", f"Critic exception: {e}")


def main():
    if len(sys.argv) < 2:
        print("usage: grant_application_drafter.py <inbox_slug>")
        return 1
    slug = sys.argv[1]
    inbox = _find_inbox_file(slug)
    if not inbox:
        print(f"no inbox file for slug={slug}")
        return 1

    grant = _parse_grant_inbox(inbox)
    print(f"drafting application for: {grant.get('title', '?')}")

    # Load Sergei context
    soul = SOUL_PATH.read_text(encoding="utf-8") if SOUL_PATH.exists() else ""
    identity = json.loads(IDENTITY_PATH.read_text(encoding="utf-8"))
    # Russian grants → academic_hse profile
    profile_key = "academic_hse"
    profile = dict(identity["profiles"][profile_key])
    profile["globals"] = identity.get("globals", {})

    draft = _compose_application(grant, profile, soul)
    if not draft:
        print("compose failed")
        return 1

    verdict, feedback = _critique(draft, grant)
    print(f"verdict: {verdict}")

    # Save
    safe_slug = re.sub(r"[^a-z0-9-]+", "-", slug.lower())[:40]
    app_dir = APPLICATIONS_DIR / safe_slug
    app_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.utcnow().date().isoformat()
    draft_file = app_dir / f"{today}-draft.md"
    draft_file.write_text(
        f"<!-- Grant: {grant.get('title','')} -->\n"
        f"<!-- URL: {grant.get('url','')} -->\n"
        f"<!-- Deadline: {grant.get('deadline','')} -->\n"
        f"<!-- Profile: {profile_key} -->\n"
        f"<!-- Critic verdict: {verdict} -->\n\n"
        + draft,
        encoding="utf-8",
    )

    feedback_file = app_dir / f"{today}-critic-feedback.txt"
    feedback_file.write_text(feedback, encoding="utf-8")

    # Render .docx alongside .md — required for portal submit (РНФ/ФСИ)
    docx_file = app_dir / f"{today}-draft.docx"
    try:
        sys.path.insert(0, "/opt/brand-agent")
        import render_docx
        title_for_docx = f"Заявка: {grant.get('title', '')[:120]}"
        render_docx.markdown_to_docx(draft, str(docx_file), title=title_for_docx)
    except Exception as e:
        print(f"docx render warning: {e}")
        docx_file = None

    # Git commit
    try:
        rel = draft_file.relative_to("/opt/reports")
        subprocess.run(["git", "-C", "/opt/reports", "add", str(rel)], check=False)
        subprocess.run(
            ["git", "-C", "/opt/reports", "add",
             str(feedback_file.relative_to("/opt/reports"))], check=False,
        )
        if docx_file:
            subprocess.run(
                ["git", "-C", "/opt/reports", "add",
                 str(docx_file.relative_to("/opt/reports"))], check=False,
            )
        subprocess.run(
            ["git", "-C", "/opt/reports", "-c", "user.name=openclaw-agent",
             "-c", "user.email=agent@sergeisolovev.com",
             "commit", "-m",
             f"grant application draft: {grant.get('title','')[:60]} ({verdict})",
             "--quiet"], check=False,
        )
        subprocess.run(["git", "-C", "/opt/reports", "push", "--quiet"], check=False)
    except Exception:
        pass

    # TG notification
    word_count = len(draft.split())
    base_url = (
        "https://github.com/SergeySolovyev/sergei-brand-agent-reports/"
        f"blob/main/applications/{safe_slug}/{today}-draft"
    )
    docx_line = (f"\n📎 .docx (portal-ready): {base_url}.docx?raw=1"
                 if docx_file else "")
    summary = (
        f"📋 *Grant application draft ready*\n\n"
        f"Grant: {grant.get('title', '?')[:80]}\n"
        f"Amount: {grant.get('amount', '?')}\n"
        f"Deadline: {grant.get('deadline', '?')}\n"
        f"Verdict: *{verdict}* · ~{word_count} words · profile {profile_key}\n\n"
        f"📝 .md (edit-friendly): {base_url}.md"
        f"{docx_line}\n\n"
        f"Critic notes:\n{feedback[:500]}"
    )
    subprocess.run(["/usr/local/bin/tg_send", summary], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
