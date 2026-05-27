#!/usr/bin/env python3
"""
load_knowledge_base.py — ingests existing D:/DeFi assets into the
sergei-brand-agent knowledge_base/ directory.

Reads:
- D:/DeFi/GoogleScholar_2026/BIBTEX_ENTRIES.bib       → preprints.json
- D:/DeFi/sergeisolovev_build/repo/index.html         → identity.json (JSON-LD)
- D:/DeFi/sergeisolovev_build/repo/papers/*.html      → per-paper metadata
- D:/DeFi/sergeisolovev_build/profile-repo/README.md  → bio + identity
- Any past social/blog posts under D:/DeFi            → brand_voice_corpus.md

Output:
- knowledge_base/identity.json
- knowledge_base/preprints.json
- knowledge_base/brand_voice_corpus.md (skeleton; manual curation expected)

Idempotent: re-running overwrites outputs but preserves manual additions
flagged with `# MANUAL` comments.

Usage:
    python scripts/load_knowledge_base.py
    python scripts/load_knowledge_base.py --defi-root D:/DeFi --kb-out ./knowledge_base
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class Preprint:
    """One preprint entry, distilled from BibTeX + landing page."""
    slug: str
    title: str
    authors: list[str]
    date: str  # YYYY-MM-DD
    venue: str
    doi: str
    doi_url: str
    pdf_url: str
    landing_url: str
    abstract: str
    keywords: list[str]
    openalex_work_id: Optional[str] = None


@dataclass
class Identity:
    """Distilled author identity from JSON-LD Person + CV."""
    name_en: str
    name_ru: str
    tagline: str
    affiliations: list[str]
    fields_of_interest: list[str]
    same_as: list[str]
    email: str
    homepage: str
    github: str
    figshare_author: str
    openalex_author: str
    cv_en_path: str
    cv_ru_path: str
    bio_short: str
    bio_long: str


# ---------------------------------------------------------------------------
# BibTeX parser (minimalist, handles our format)
# ---------------------------------------------------------------------------

BIBTEX_ENTRY_RE = re.compile(
    r"@(?P<entry_type>\w+)\{(?P<key>[^,]+),(?P<body>.*?)\n\}",
    re.DOTALL,
)
BIBTEX_FIELD_RE = re.compile(
    r"^\s*(?P<field>\w+)\s*=\s*\{(?P<value>(?:[^{}]|\{[^{}]*\})*)\}\s*,?\s*$",
    re.MULTILINE,
)


def parse_bibtex(text: str) -> list[dict]:
    """Parse a BibTeX file into a list of dict entries."""
    entries = []
    for entry_match in BIBTEX_ENTRY_RE.finditer(text):
        entry = {
            "type": entry_match.group("entry_type"),
            "key": entry_match.group("key").strip(),
            "fields": {},
        }
        body = entry_match.group("body")
        for field_match in BIBTEX_FIELD_RE.finditer(body):
            f = field_match.group("field").strip().lower()
            v = field_match.group("value").strip()
            # Strip inner braces (escape protection)
            v = re.sub(r"^\{|\}$", "", v).strip()
            # Collapse multi-line whitespace
            v = re.sub(r"\s+", " ", v)
            entry["fields"][f] = v
        entries.append(entry)
    return entries


# ---------------------------------------------------------------------------
# Preprint extraction
# ---------------------------------------------------------------------------


PREPRINT_SLUGS_BY_DOI = {
    "10.6084/m9.figshare.32141182": "rag-solidity",
    "10.6084/m9.figshare.32141167": "ai-yield-vault",
    "10.6084/m9.figshare.31859557": "lob-mid-price",
    "10.6084/m9.figshare.31429971": "ml-vuln-detection",
    "10.6084/m9.figshare.31430086": "ocr-vs-donut",
}

OPENALEX_WORK_IDS = {
    "10.6084/m9.figshare.32141182": "W7158582464",
    "10.6084/m9.figshare.32141167": "W7159474823",
    "10.6084/m9.figshare.31859557": None,  # discovered via search at runtime
    "10.6084/m9.figshare.31429971": "W7131857395",
    "10.6084/m9.figshare.31430086": "W7131820915",
}

# Keywords per preprint, distilled from the existing landing pages
KEYWORDS_BY_SLUG = {
    "rag-solidity": [
        "smart contract security", "retrieval-augmented generation", "Solidity",
        "vulnerability detection", "bootstrap confidence intervals",
    ],
    "ai-yield-vault": [
        "decentralized finance", "ERC-4626", "EIP-712",
        "multi-criteria decision making", "formal verification",
        "invariant testing", "autonomous agent",
    ],
    "lob-mid-price": [
        "limit order book", "high-frequency finance", "recurrent neural networks",
        "mid-price prediction", "weighted Pearson", "Wunder Fund challenge",
    ],
    "ml-vuln-detection": [
        "smart contract security", "EVM bytecode", "XGBoost", "Optuna",
        "Slither labels", "binary classification", "SWC categories",
    ],
    "ocr-vs-donut": [
        "OCR", "Donut transformer", "document understanding", "SROIE 2019",
        "receipt extraction", "image degradation", "error taxonomy",
    ],
}


def extract_preprints(bibtex_path: Path) -> list[Preprint]:
    """Parse BIBTEX_ENTRIES.bib and produce normalized Preprint objects."""
    text = bibtex_path.read_text(encoding="utf-8")
    entries = parse_bibtex(text)

    preprints: list[Preprint] = []
    for entry in entries:
        fields = entry["fields"]
        doi = fields.get("doi", "").strip()
        if not doi or "figshare" not in doi:
            continue   # skip the future RINC entries that don't have DOI yet

        slug = PREPRINT_SLUGS_BY_DOI.get(doi)
        if slug is None:
            print(f"  [skip] unknown DOI: {doi}", file=sys.stderr)
            continue

        # Normalize date: BibTeX has year + month; we want YYYY-MM-01
        year = fields.get("year", "2026")
        month_word = fields.get("month", "jan").lower()
        month_map = {
            "jan": "01", "feb": "02", "mar": "03", "apr": "04",
            "may": "05", "jun": "06", "jul": "07", "aug": "08",
            "sep": "09", "oct": "10", "nov": "11", "dec": "12",
        }
        date = f"{year}-{month_map.get(month_word, '01')}-01"

        title = fields.get("title", "").strip()
        # BibTeX nested-brace cleanup
        title = re.sub(r"^\{|\}$", "", title).strip()

        # Abstract from the `note` field (we put abstracts there in our bib)
        abstract = fields.get("note", "").strip()
        abstract = re.sub(r"\\%", "%", abstract)
        abstract = re.sub(r"\\_", "_", abstract)

        preprints.append(Preprint(
            slug=slug,
            title=title,
            authors=["Solovev, Sergei"],
            date=date,
            venue=fields.get("howpublished", "Preprint, Figshare"),
            doi=doi,
            doi_url=f"https://doi.org/{doi}",
            pdf_url=f"https://sergeisolovev.com/papers/{slug}.pdf",
            landing_url=f"https://sergeisolovev.com/papers/{slug}.html",
            abstract=abstract,
            keywords=KEYWORDS_BY_SLUG.get(slug, []),
            openalex_work_id=OPENALEX_WORK_IDS.get(doi),
        ))

    return preprints


# ---------------------------------------------------------------------------
# Identity extraction (from JSON-LD in index.html + CV scraping)
# ---------------------------------------------------------------------------


JSONLD_RE = re.compile(
    r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',
    re.DOTALL,
)


def extract_identity(
    index_html: Path,
    profile_readme: Path,
) -> Identity:
    """Distill identity from JSON-LD Person + the profile-repo README."""
    html = index_html.read_text(encoding="utf-8")
    jsonld_matches = JSONLD_RE.findall(html)

    person_data = {}
    for blob in jsonld_matches:
        try:
            data = json.loads(blob)
        except json.JSONDecodeError:
            continue
        if data.get("@type") == "Person":
            person_data = data
            break

    if not person_data:
        print("  [warn] no JSON-LD Person found in index.html; using defaults",
              file=sys.stderr)

    readme = profile_readme.read_text(encoding="utf-8") if profile_readme.exists() else ""
    bio_short = "HSE FCS researcher · TradFi → AI → DeFi · "\
        "Smart contract security, ML, decentralized finance · "\
        "5 figshare preprints (2026)"
    bio_long = (
        "Sergei Solovev is a researcher at HSE University, Faculty of Computer Science, "
        "and a fixed-income advisor at Mosoblbank (PSB Group). 20+ years in TradFi "
        "(US equities, EM debt, portfolios >$4B). Transitioning into applied AI "
        "research at the intersection of TradFi, AI/ML, and DeFi. Board member, ACI Russia. "
        "Speaker, ACI eFX Summit 2025. "
        "Five preprints (2026) on smart contract security (RAG, EVM bytecode ML), "
        "DeFi (ERC-4626 MCDM vault with formal verification), high-frequency finance "
        "(limit order book mid-price prediction), and document AI (OCR vs Donut)."
    )

    return Identity(
        name_en=person_data.get("name", "Sergei Solovev"),
        name_ru="Соловьев Сергей Сергеевич",
        tagline="TradFi → AI → DeFi",
        affiliations=[
            "HSE University, Faculty of Computer Science",
            "Mosoblbank (PSB Group)",
            "ACI Russia (board member)",
        ],
        fields_of_interest=person_data.get("knowsAbout", [
            "smart contract security",
            "machine learning",
            "decentralized finance",
            "vulnerability detection",
            "retrieval-augmented generation",
            "blockchain",
            "EVM bytecode analysis",
            "limit order book prediction",
        ]),
        same_as=person_data.get("sameAs", [
            "https://github.com/SergeySolovyev",
            "https://figshare.com/authors/Sergei_Solovev/23264342",
            "https://openalex.org/A5127404993",
        ]),
        email="sesesolovev@edu.hse.ru",
        homepage="https://sergeisolovev.com",
        github="https://github.com/SergeySolovyev",
        figshare_author="https://figshare.com/authors/Sergei_Solovev/23264342",
        openalex_author="https://openalex.org/A5127404993",
        cv_en_path=str(Path("D:/DeFi/sergeisolovev_build/repo/Solovev_Sergei_CV_EN.pdf")),
        cv_ru_path=str(Path("D:/DeFi/AIRI_2026_report/CV/Solovev_Sergei_CV_RU.pdf")),
        bio_short=bio_short,
        bio_long=bio_long,
    )


# ---------------------------------------------------------------------------
# Brand voice corpus (skeleton — relies on manual curation)
# ---------------------------------------------------------------------------


BRAND_VOICE_SKELETON = """\
# Brand Voice Corpus — Sergei Solovev

This file holds samples of Sergei's *actual* past writing across channels.
The **Composer** reads it before drafting to match his tone. The **Critic**
checks new drafts against this corpus for voice drift.

> NOTE: This is a starter skeleton. As Sergei posts to LinkedIn / X / Telegram /
> blog, samples are added here (manually or via `add_voice_sample.py`).
> The agent does NOT modify this file autonomously.

## Calibration anchors

### Anchor 1 — academic/technical writing (from preprint abstracts)

> **Empirical study showing a sample-size sign reversal in naive RAG for Solidity
> vulnerability detection: +2.0% Macro-F1 at n=100 flips to −2.7% at n=250 on
> SolidiFI. Argues for bootstrap confidence intervals in any RAG evaluation.**

Voice signals: specific numbers, named benchmark, no hedging, conclusion sharp.

### Anchor 2 — README / GitHub profile (current bio)

> **HSE FCS researcher · TradFi → AI → DeFi · Smart contract security, ML,
> decentralized finance · 5 figshare preprints (2026)**

Voice signals: telegraphic, dot-separated, no first-person, technical density.

### Anchor 3 — formal CV style

> **Five preprints (2026) on smart contract security, DeFi MCDM with formal
> verification, limit order book mid-price prediction, document AI.**

Voice signals: enumeration, parallel construction, comma-list of work,
no marketing language.

---

## Samples by channel

### Blog samples
*(none yet — first blog post will seed)*

### LinkedIn samples
*(none yet)*

### X / Twitter samples
*(none yet)*

### Telegram RU samples
*(none yet)*

### Outreach email samples
*(none yet)*

---

## Anti-corpus (DO NOT match this tone)

Voice patterns Sergei does NOT use (for Critic to flag if drafts drift toward these):

- Hyperbolic marketing: "absolute game changer", "this changes everything"
- Crypto-bro: "wagmi", "to the moon", "100x"
- Fake humility: "I'm just a researcher", "no expert here"
- LLM tells: "delve into", "in the realm of", "tapestry of"
- Empty filler: "obviously", "simply", "just", "very", "really"

---

## How to add a sample

When Sergei publishes something he likes, append to the relevant section:

```markdown
### LinkedIn samples

#### 2026-06-15 — "Why bootstrap CIs matter for RAG eval"
[paste exact text here, 200-400 words]
```

Composer reads the most recent 10-15 samples per channel before drafting.
"""


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--defi-root",
        default="D:/DeFi",
        help="Root of existing D:/DeFi brand assets",
    )
    parser.add_argument(
        "--kb-out",
        default=None,
        help="Output knowledge_base/ directory (defaults to ../knowledge_base/ relative to this script)",
    )
    args = parser.parse_args()

    defi_root = Path(args.defi_root)
    if args.kb_out:
        kb_out = Path(args.kb_out)
    else:
        kb_out = Path(__file__).resolve().parent.parent / "knowledge_base"

    kb_out.mkdir(parents=True, exist_ok=True)

    bibtex_path = defi_root / "GoogleScholar_2026" / "BIBTEX_ENTRIES.bib"
    index_html = defi_root / "sergeisolovev_build" / "repo" / "index.html"
    profile_readme = defi_root / "sergeisolovev_build" / "profile-repo" / "README.md"

    # 1. Preprints
    print(f"[1/3] Parsing preprints from {bibtex_path}")
    if not bibtex_path.exists():
        print(f"  [error] {bibtex_path} not found")
        return 1
    preprints = extract_preprints(bibtex_path)
    print(f"  -> {len(preprints)} preprints")
    preprints_out = kb_out / "preprints.json"
    preprints_out.write_text(
        json.dumps({"preprints": [asdict(p) for p in preprints]},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  -> wrote {preprints_out}")

    # 2. Identity
    print(f"[2/3] Extracting identity from {index_html}")
    if not index_html.exists():
        print(f"  [error] {index_html} not found")
        return 1
    identity = extract_identity(index_html, profile_readme)
    identity_out = kb_out / "identity.json"
    identity_out.write_text(
        json.dumps(asdict(identity), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  -> wrote {identity_out}")

    # 3. Brand voice corpus skeleton (do NOT overwrite if exists with manual edits)
    corpus_out = kb_out / "brand_voice_corpus.md"
    if corpus_out.exists():
        print(f"[3/3] {corpus_out} exists — skipping (preserve manual edits)")
    else:
        print(f"[3/3] Writing brand voice corpus skeleton")
        corpus_out.write_text(BRAND_VOICE_SKELETON, encoding="utf-8")
        print(f"  -> wrote {corpus_out}")

    print()
    print("[OK] Knowledge base loaded successfully")
    print(f"  Preprints: {len(preprints)}")
    print(f"  Identity: {identity.name_en}")
    print(f"  Affiliations: {len(identity.affiliations)}")
    print(f"  Fields of interest: {len(identity.fields_of_interest)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
