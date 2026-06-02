#!/opt/brand-agent/venv/bin/python3
"""arxiv_prep — generate arXiv submission kits for Sergei's 5 preprints.

ORCID now lists all 5 figshare preprints. arXiv gives them far more academic
reach + Google Scholar indexing. Sergei must do the final upload himself (arXiv
account + endorsement), but this prepares everything so it's a 10-min paste job
per paper instead of an hour.

For each preprint (from preprints.json) it pulls the canonical abstract from
DataCite and writes a submission kit:
  /opt/reports/arxiv-prep/<n>-<slug>/SUBMISSION.md
containing: title, abstract, suggested primary+cross categories, comments line,
license suggestion, and a step-by-step checklist.

Run once (or after adding a preprint).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

PREPRINTS = Path("/opt/brand-agent/knowledge_base/preprints.json")
OUT = Path("/opt/reports/arxiv-prep")

# Map domain tags → arXiv categories
CAT_MAP = {
    "smart contract security": ("cs.CR", ["cs.LG", "cs.SE"]),
    "DeFi": ("cs.CR", ["q-fin.TR", "cs.LG"]),
    "quant": ("q-fin.TR", ["cs.LG", "stat.ML"]),
    "document AI": ("cs.CV", ["cs.CL", "cs.LG"]),
}
DEFAULT_CAT = ("cs.LG", ["cs.AI"])


def _datacite_abstract(doi: str) -> str:
    try:
        req = urllib.request.Request(
            f"https://api.datacite.org/dois/{doi}",
            headers={"User-Agent": "sergei-brand-agent/arxiv-prep"})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read())["data"]["attributes"]
        descs = d.get("descriptions", [])
        for x in descs:
            if x.get("descriptionType", "").lower() in ("abstract", ""):
                return x.get("description", "")
        return descs[0].get("description", "") if descs else ""
    except Exception as e:
        return f"(could not fetch abstract: {e})"


def main() -> int:
    data = json.loads(PREPRINTS.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    for i, p in enumerate(data.get("preprints", []), 1):
        doi = p["doi"]
        title = p["title"]
        tag = p.get("tag", "")
        primary, cross = CAT_MAP.get(tag, DEFAULT_CAT)
        abstract = _datacite_abstract(doi)
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower())[:45]
        d = OUT / f"{i}-{slug}"
        d.mkdir(parents=True, exist_ok=True)
        kit = (
            f"# arXiv submission kit — paper {i}\n\n"
            f"## Title\n{title}\n\n"
            f"## Authors\nSergei Solovev (HSE University, Faculty of Computer Science)\n"
            f"ORCID: 0009-0008-4494-0447\n\n"
            f"## Abstract\n{abstract}\n\n"
            f"## arXiv categories\n"
            f"- Primary: **{primary}**\n"
            f"- Cross-list: {', '.join(cross)}\n\n"
            f"## Comments line (for arXiv)\n"
            f"Preprint. Also available at figshare: https://doi.org/{doi}\n\n"
            f"## License\nCC BY 4.0 (recommended — matches figshare, max reach)\n\n"
            f"## Submission checklist\n"
            f"1. Sign in at https://arxiv.org (register if needed; first submission "
            f"may require endorsement in {primary})\n"
            f"2. Start New Submission → paste Title + Abstract above\n"
            f"3. Set primary category {primary}, cross-list {', '.join(cross)}\n"
            f"4. Upload the PDF (from sergeisolovev.com/papers/ or figshare)\n"
            f"5. Paste the Comments line; pick CC BY 4.0\n"
            f"6. Add ORCID 0009-0008-4494-0447 in author profile\n"
            f"7. Submit → arXiv ID issued → add it back to ORCID + sergeisolovev.com\n\n"
            f"## Source figshare\nhttps://doi.org/{doi}\n"
        )
        (d / "SUBMISSION.md").write_text(kit, encoding="utf-8")
        n += 1
        print(f"  kit {i}: {title[:50]} → {primary}")

    # Index
    idx = "# arXiv prep — 5 preprints ready to submit\n\n"
    idx += ("ORCID now lists all 5. arXiv adds Scholar indexing + academic reach.\n"
            "Each folder has a SUBMISSION.md with paste-ready title/abstract/"
            "categories + checklist. You do the final upload (needs your arXiv "
            "account; first one may need endorsement).\n\n")
    for i, p in enumerate(data.get("preprints", []), 1):
        slug = re.sub(r"[^a-z0-9]+", "-", p["title"].lower())[:45]
        idx += f"{i}. [{p['title'][:60]}]({i}-{slug}/SUBMISSION.md)\n"
    (OUT / "README.md").write_text(idx, encoding="utf-8")

    try:
        subprocess.run(["git", "-C", "/opt/reports", "add", "arxiv-prep/"], check=False)
        subprocess.run(
            ["git", "-C", "/opt/reports", "-c", "user.name=openclaw-agent",
             "-c", "user.email=agent@sergeisolovev.com",
             "commit", "-m", "arxiv prep kits for 5 preprints", "--quiet"], check=False)
        subprocess.run(["git", "-C", "/opt/reports", "push", "--quiet"], check=False)
    except Exception:
        pass
    print(f"arxiv_prep: {n} kits written to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
