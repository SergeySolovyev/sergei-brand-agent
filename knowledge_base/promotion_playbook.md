# Sergei Solovev — Brand Promotion Playbook (120+ tactics)

**Purpose**: Comprehensive catalog of channels, tactics, and opportunity-discovery patterns
that the **sergei-brand-agent** can discover, evaluate, and act on. Each entry is structured
so the agent's `Strategist` can rank by fit, the `Composer` can produce channel-native content,
and the `Critic` can apply channel-specific guardrails.

**Reading legend** (used in every entry):
- **Audience**: who this reaches (commercial / academic / both / Russian / EN / niche)
- **Effort**: ⚡ low (≤30 min one-shot) · ⚙️ medium (1-3 h) · 🏗️ high (10+ h)
- **Impact horizon**: ⏱️ days · 🗓️ weeks · 📅 months · 🎯 compound (years)
- **Autonomy**: 🤖 agent-only · 👤 human-only · 🤝 hybrid (draft auto, approve human) · 👥 RAH-escalate
- **Risk**: 🟢 low · 🟡 medium · 🔴 high (brand-damage risk)
- **Frequency cap**: how often you can do this before it becomes spam

---

## Category 1 — Owned Media (your sites, your channels)

> Why first: owned media is the only channel you fully control. SEO-compound + email list = compounding asset. Two great blog posts > twenty mediocre tweets.

### 1.1 sergeisolovev.com blog (`/blog/`)
- **Audience**: commercial + academic (EN, SEO-driven)
- **Effort**: 🏗️ high (3-8 h per post) · **Impact**: 🎯 compound
- **Autonomy**: 🤝 hybrid (Composer drafts → Critic gates → auto-publish via git PR)
- **Risk**: 🟢 low (revertable)
- **Frequency**: 1-2 posts/week max for SEO consistency
- **Recipe**: build pillar pages around 3-4 topics (smart contract security, DeFi MCDM, LOB prediction, RAG evaluation); internal link densely; each post has canonical_doi linking to figshare.

### 1.2 sergeisolovev.com case studies (`/case-studies/`)
- **Audience**: commercial (CTOs, VPs, VC analysts) · **Effort**: 🏗️ high · **Impact**: 📅 months · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: per project (ai-yield-vault, honest-rag-solidity, predictive-mcdm-defi) write 1500-3000 word case study with problem/approach/numbers/learnings/code.

### 1.3 Newsletter via Substack/beehiiv (`sergei.substack.com` or `sergei.beehiiv.com`)
- **Audience**: warm leads (subscribers > followers) · **Effort**: ⚙️ medium · **Impact**: 🎯 compound · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: monthly digest with 1 deep think + 3-5 curated links. Embed signup CTA on every sergeisolovev.com page.

### 1.4 RSS / Atom feed (already deployed at `/feed.xml`)
- **Audience**: Feedly/Inoreader power users (often investors/decision makers) · **Effort**: ⚡ (one-time) · **Impact**: 🎯 · **Autonomy**: 🤖 · **Risk**: 🟢
- **Recipe**: auto-generated from blog posts; cross-broadcast to Mastodon and BlueSky on update.

### 1.5 Personal podcast (`Sergei's TradFi→AI→DeFi`)
- **Audience**: niche commercial+academic (EN) · **Effort**: 🏗️ very high · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: 30-min monologue OR conversation; transcript on blog; YouTube video version; Spotify+Apple+RSS distribution. Defer to 2026Q4 if other tactics deliver first.

### 1.6 Notion / Obsidian Publish public garden
- **Audience**: power-users, researchers · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 🤖 · **Risk**: 🟢
- **Recipe**: publish reading notes, research log, projects roadmap. Garden-style (continuously updated, not "published"). Backlink to sergeisolovev.com.

### 1.7 Calendly / Cal.com booking page
- **Audience**: lead-gen · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤖 · **Risk**: 🟢
- **Recipe**: 15-min "ask me about smart contract security / MCDM / LOB" slots; embed on site; share in bio across channels.

### 1.8 Lead magnet: ERC-4626 audit checklist PDF
- **Audience**: smart contract auditors, DeFi founders · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: distill ai-yield-vault findings into 1-page checklist; gate behind email; auto-DM to subscribers.

### 1.9 Lead magnet: RAG eval bootstrap CI Python notebook
- **Audience**: ML practitioners · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: derivative of When Retrieval Hurts paper; one-click Colab; same email gate.

---

## Category 2 — Academic Identity (researcher profile networks)

### 2.1 Google Scholar profile
- **Audience**: academic + investors checking credentials · **Effort**: ⚡ (one-time setup) · **Impact**: 🎯 · **Autonomy**: 👤 (creation needs at least 1 indexed paper) · **Risk**: 🟢
- **Recipe**: deferred to ~July 2026 when RINC pubs index in eLibrary.

### 2.2 ORCID iD (`orcid.org/...`)
- **Audience**: ALL academic submissions · **Effort**: ⚡ (3 min) · **Impact**: 🎯 · **Autonomy**: 👤 (sign-up only) · **Risk**: 🟢
- **Recipe**: register → link all 5 figshare DOIs → set as `sameAs` in JSON-LD Person schema. Required for NIH Common Form Jan 2026.

### 2.3 ResearchGate profile
- **Audience**: academic (Russian academics use heavily) · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 👤 → 🤖 (after setup) · **Risk**: 🟢
- **Recipe**: register with HSE email; upload 5 preprints; join RG groups in smart-contract-security and DeFi-research.

### 2.4 Academia.edu profile
- **Audience**: academic backwater but still indexed by Google · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 👤 setup · **Risk**: 🟢
- **Recipe**: same as RG but lower priority. Set up only if RG stagnates.

### 2.5 Semantic Scholar (`semanticscholar.org/author/...`)
- **Audience**: academic ML community · **Effort**: ⚡ (passive — they crawl) · **Impact**: 🎯 · **Autonomy**: 🤖 (monitor) · **Risk**: 🟢
- **Recipe**: papers auto-indexed via OpenAlex bridge; just claim profile once visible.

### 2.6 OpenAlex author entity (`A5127404993` — already exists, 4/5 indexed)
- **Audience**: scholarly aggregators · **Effort**: 🤖 (auto) · **Impact**: 🎯 · **Autonomy**: 🤖 · **Risk**: 🟢
- **Recipe**: agent monitors weekly; submits correction if metadata wrong; uses OpenAlex API for "who cited me" detection.

### 2.7 dblp computer science bibliography
- **Audience**: CS academia · **Effort**: ⚡ (1 email submission) · **Impact**: 🎯 · **Autonomy**: 👤 once · **Risk**: 🟢
- **Recipe**: once a paper hits a CS conference/journal, email dblp to add. Until then defer.

### 2.8 HSE FCS faculty page
- **Audience**: institutional credibility · **Effort**: ⚡ · **Impact**: 🎯 · **Autonomy**: 👤 (admin) · **Risk**: 🟢
- **Recipe**: ask HSE FCS for student-researcher profile page; cross-link to sergeisolovev.com.

### 2.9 Russian Science Index (RSCI/РИНЦ) author profile
- **Audience**: Russian academic credentialing · **Effort**: ⚡ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: appears automatically after first eLibrary publication (June 2026); claim and link to ORCID.

### 2.10 arXiv author identifier
- **Audience**: ML/CS researchers · **Effort**: ⚡ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: need endorsement in cs.CR; ask HSE supervisor; first arXiv submission unlocks the ID.

---

## Category 3 — Code Portfolios

### 3.1 GitHub profile (✅ DONE — `SergeySolovyev/SergeySolovyev` magic repo)
- **Audience**: developers, recruiters, investors checking technical credibility · **Effort**: ⚡ (ongoing maintenance) · **Impact**: 🎯 · **Autonomy**: 🤖 (agent commits updates) · **Risk**: 🟢

### 3.2 GitHub pinned repos (6 slots)
- **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 👤 (manual UI) · **Risk**: 🟢
- **Recipe**: pin honest-rag-solidity, ai-yield-vault, predictive-mcdm-defi, airi-2026-finagent-probe, sergeisolovev.com, SergeySolovyev. Sergei does this in UI; agent reminds.

### 3.3 GitHub Sponsors
- **Audience**: open-source backers · **Effort**: ⚡ setup · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: enable; signal commercial seriousness. Even 1-2 sponsors is social proof.

### 3.4 HuggingFace profile / Spaces / Models
- **Audience**: ML community · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: upload OCR vs Donut model + RAG-eval Spaces demo + DA-BiGRU-CNN reference impl. Each release = social post material.

### 3.5 Kaggle profile + competition history
- **Audience**: ML practitioners · **Effort**: 🏗️ (per competition) · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: already exists (Google AI Agent Week per memory). Polish bio; cross-link.

### 3.6 GitLab mirror
- **Audience**: enterprise (some shops only use GitLab) · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤖 · **Risk**: 🟢
- **Recipe**: mirror top 5 repos via GitLab pull-mirroring; signal cross-platform availability.

### 3.7 Codeberg mirror (FOSS-friendly)
- **Audience**: open-source purists · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤖 · **Risk**: 🟢
- **Recipe**: same as GitLab.

### 3.8 Replit profile
- **Audience**: beginners-to-mid developers, agentic-AI builders · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: publish 1-2 interactive demos (e.g. ERC-4626 vault sim playground).

### 3.9 npm / PyPI published packages
- **Audience**: developers · **Effort**: ⚙️ per release · **Impact**: 🎯 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: ship reusable utilities from research (e.g. `bootstrap-ci-eval` Python package from RAG paper).

### 3.10 awesome-list contribution
- **Audience**: domain communities · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: submit ai-yield-vault to `awesome-defi`, `awesome-evm-security`; honest-rag-solidity to `awesome-rag`. PRs to each.

### 3.11 GitHub star-list curation (public)
- **Audience**: developer community · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: maintain "Smart Contract Security tools (curated)" list publicly; becomes resource people link.

---

## Category 4 — Long-form Social (EN, professional)

### 4.1 LinkedIn newsletter (LinkedIn-native)
- **Audience**: professionals, recruiters, investors · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 🤝 · **Risk**: 🟡
- **Recipe**: enable LinkedIn newsletter feature; biweekly; cross-post sergeisolovev.com long-forms as LI articles.

### 4.2 LinkedIn personal feed
- **Audience**: professionals · **Effort**: ⚡-⚙️ · **Impact**: 🗓️-📅 · **Autonomy**: 🤝 (Composer drafts, human posts) · **Risk**: 🟡
- **Recipe**: 2-4 posts/week. Mix of: case-study breakdowns, contrarian takes, project milestones, signal-from-noise re-shares.

### 4.3 LinkedIn carousels
- **Audience**: LinkedIn algorithm-loved format · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟡
- **Recipe**: 8-12 slides per carousel; visualization-heavy content (e.g. "8 EVM bytecode vulnerabilities and how to detect them"). PDF format works.

### 4.4 LinkedIn videos
- **Audience**: LinkedIn algo-prefers (5.60% engagement rate) · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: 1-3 min phone-shot explainers; 1/week max; subtitles required.

### 4.5 Substack publication
- **Audience**: subscribers (durable asset) · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: cross-post blog with Substack as primary newsletter; build subscriber list.

### 4.6 Medium publication
- **Audience**: general tech readership · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: cross-post (with canonical link to sergeisolovev.com); submit to top publications (Towards Data Science, Better Programming, Cointelegraph Magazine if accepting).

### 4.7 Mirror.xyz publication (Web3-native long-form)
- **Audience**: crypto-native readers · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: cross-post DeFi-themed posts; mint as NFT (some collectors).

### 4.8 Paragraph.xyz publication
- **Audience**: similar to Mirror but newer, more builder-focused · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: cross-post with crypto-tipping enabled.

---

## Category 5 — Developer Long-form Publishing

### 5.1 dev.to (DEV Community)
- **Audience**: ~3.5M monthly developer views · **Effort**: ⚡ (cross-post) · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: cross-post technical blogs; use `canonical_url` to preserve SEO; tag `#defi #ml #python`. Self-publish, get social-like engagement.

### 5.2 Hashnode
- **Audience**: developers, custom-domain friendly · **Effort**: ⚡ (cross-post) · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: same as dev.to; some prefer Hashnode for cleaner UX.

### 5.3 In Plain English (JavaScript/Python/Stackademic etc.)
- **Audience**: 3.5M monthly views across publications · **Effort**: ⚙️ (submission process) · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: pitch a blog post to JavaScript IPE or Python IPE; editorial review; canonical-backed reach.

### 5.4 freeCodeCamp News
- **Audience**: huge developer reach · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: submit deep tutorial (e.g. "ML for Smart Contract Vulnerability Detection: A Practical Guide"); high editorial bar.

### 5.5 Hacker Noon
- **Audience**: tech generalists · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: submission-based; editorial review.

### 5.6 SitePoint
- **Audience**: web developers · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: pitch Solidity/web3 tutorials.

### 5.7 Smashing Magazine
- **Audience**: front-end heavy · **Effort**: 🏗️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: lower fit for DeFi/ML; defer.

### 5.8 Towards Data Science (Medium publication)
- **Audience**: ML/DS practitioners · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: pitch ML/data-science angles of preprints (esp. RAG eval, LOB prediction, OCR comparison).

### 5.9 Cointelegraph (guest column or quoted source)
- **Audience**: crypto press readership · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: pitch via Cointelegraph Magazine editor; expert commentary on smart-contract security.

### 5.10 The Block / Decrypt / Coindesk research desks
- **Audience**: crypto institutional · **Effort**: 🏗️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: pitch as expert source for stories on RAG/ML in security audits.

---

## Category 6 — Short-form Social (EN)

### 6.1 X / Twitter feed
- **Audience**: technical peers, VCs scout for technical credibility · **Effort**: ⚡ · **Impact**: 🗓️-📅 · **Autonomy**: 🤝 · **Risk**: 🟡
- **Recipe**: 3-6 posts/week. Mix: paper takes, code release announcements, contrarian-but-defensible technical takes.

### 6.2 X / Twitter threads
- **Audience**: same as feed, deeper engagement · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟡
- **Recipe**: 5-10 tweet thread. Hook in T1, build, link to long-form at end.

### 6.3 X Spaces (live audio)
- **Audience**: live, deep-engagement subset · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: host monthly Space on "DeFi security walkthrough"; co-host with established voices.

### 6.4 BlueSky
- **Audience**: ex-Twitter tech, growing (40M users by Nov 2025) · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: cross-post X feed with adjustments (BlueSky audience less crypto, more general tech).

### 6.5 Mastodon (fosstodon, infosec.exchange, sigmoid.social)
- **Audience**: open-source/academic-leaning · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤖 · **Risk**: 🟢
- **Recipe**: pick infosec.exchange for security work; auto-broadcast via RSS-to-Mastodon bot from feed.xml.

### 6.6 Threads (Meta)
- **Audience**: general · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: low priority; cross-post X content if time permits.

---

## Category 7 — Web3-native Social

### 7.1 Farcaster account
- **Audience**: crypto builders, EF folks, web3 founders · **Effort**: ⚡ (setup) · **Impact**: 🗓️-📅 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: register on Warpcast; post technical takes about DeFi/EVM/ZK; participate in /defi, /developers channels.

### 7.2 Farcaster Frames
- **Audience**: in-feed interactive · **Effort**: 🏗️ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: deploy a "ERC-4626 vault risk scorer" Frame; users tap → see your tool inline.

### 7.3 Lens Protocol
- **Audience**: web3 social-graph builders · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: secondary to Farcaster; cross-post.

### 7.4 ENS domain (`sergeisolovev.eth`)
- **Audience**: web3-native credentialing · **Effort**: ⚡ (one-time, ~$5/year) · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: register; set `url=sergeisolovev.com`, `email=sesesolovev@edu.hse.ru`, `github=SergeySolovyev`. Use as crypto-native identity card.

### 7.5 Lensfrens.xyz / Hey.xyz profiles
- **Audience**: Lens-native discovery · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: claim handle matching `sergeisolovev`.

---

## Category 8 — Russian / CIS Platforms

### 8.1 Telegram own channel (e.g. `@sergei_solovev`)
- **Audience**: Russian DeFi/research community · **Effort**: ⚡-⚙️ · **Impact**: 🎯 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: post 3-5/week in Russian; mix project updates, paper announcements, opinion-takes.

### 8.2 Telegram active participation in 10-15 RU communities
- **Audience**: niche Russian crypto/research · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: identify 10-15 RU TG groups (МФТИ-crypto, DeFi-RU, BitFiBoy, ProBlockchain); thoughtful answers, not spam. Linkbacks earned.

### 8.3 Habr article publication
- **Audience**: Russian engineers · **Effort**: 🏗️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: monthly Russian-language deep technical post; Habr's algorithm rewards substance. Cross-link from sergeisolovev.com.

### 8.4 VK (ВКонтакте) page
- **Audience**: broad Russian-speaking · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: simple page, link to TG channel.

### 8.5 Tinkoff Journal (Т—Ж) expert column
- **Audience**: Russian finance-curious mainstream · **Effort**: 🏗️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: pitch piece on crypto/AI fundamentals for non-experts; Т—Ж has huge reach.

### 8.6 Yandex.Zen (Дзен) channel
- **Audience**: Russian mainstream readers · **Effort**: ⚡ (cross-post) · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: cross-post Russian Habr articles.

### 8.7 РБК / Forbes Russia expert quote
- **Audience**: Russian business establishment · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: respond to journalist inquiries (HARO-equivalent for RU press); register on Pressfeed.ru as expert.

### 8.8 Pressfeed.ru expert profile
- **Audience**: Russian journalists looking for sources · **Effort**: ⚡ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: register; respond to 1-3 inquiries per week; gets you into Russian press.

### 8.9 Pikabu / Lenta.ru op-ed
- **Audience**: Russian mainstream · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: very low priority; only if a piece goes mega-viral organically.

### 8.10 Russian DAO governance participation (e.g. ProBlockchain)
- **Audience**: Russian crypto community leaders · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: participate thoughtfully in governance forums of Russian crypto projects.

---

## Category 9 — Q&A / Tech Discussion Sites

### 9.1 Stack Overflow answers (smart-contract / web3 / ML tags)
- **Audience**: developers searching solutions · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: 2-3 quality answers/month in `solidity`, `ethereum`, `evm`, `smart-contracts`, `xgboost`; SO answers rank well in Google for years.

### 9.2 Ethereum Stack Exchange
- **Audience**: Ethereum dev community · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: same as SO but more crypto-niche; build reputation in `vault`, `erc-4626`, `security` tags.

### 9.3 Cryptography Stack Exchange
- **Audience**: cryptography researchers · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: occasional answers on RAG/EVM/security topics with crypto angles.

### 9.4 Cross Validated (Stack Exchange — stats/ML)
- **Audience**: ML researchers · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: answer questions on bootstrap CIs (your paper's topic!), MCDM, LOB prediction methodology.

### 9.5 Hacker News submissions + comments
- **Audience**: tech-curious early adopters · **Effort**: ⚡ · **Impact**: 🗓️-📅 · **Autonomy**: 🤝 · **Risk**: 🟡
- **Recipe**: submit blog posts (Show HN: ai-yield-vault); thoughtful comments on related stories.

### 9.6 Lobste.rs submissions
- **Audience**: programmers (invite-only, high signal) · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: get invited; submit security/ML content; reputation rewards.

### 9.7 Reddit — r/ethereum, r/MachineLearning, r/defi
- **Audience**: subreddit-specific · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟡
- **Recipe**: top-level posts on novel work; thoughtful comments on others' threads. Karma-build slowly; never self-promo without value.

### 9.8 Reddit — r/ethdev, r/solidity, r/cryptocurrency (carefully)
- **Audience**: niche Ethereum dev community · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟡
- **Recipe**: target r/ethdev primarily; r/cryptocurrency has spam-detection.

### 9.9 Indie Hackers
- **Audience**: builders monetizing products · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: post about commercial products built (ai-yield-vault if commercialized); "milestones" thread.

### 9.10 Quora answers
- **Audience**: long tail SEO traffic · **Effort**: ⚡ · **Impact**: 🎯 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: 1-2 deep answers/month on "what is RAG", "how do smart contract audits work"; Quora ranks well for years.

---

## Category 10 — Communities (Discord, Slack, Matrix)

### 10.1 Ethereum R&D Discord
- **Audience**: core protocol researchers · **Effort**: ⚡ (passive presence) · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: join, lurk, occasionally contribute. Citation+credibility goldmine.

### 10.2 EthSecurity Discord/Slack
- **Audience**: smart contract security pros · **Effort**: ⚡ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: contribute to discussions; cite your bytecode-feature work.

### 10.3 ML Collective Discord
- **Audience**: ML researchers · **Effort**: ⚡ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: join Reading Group, present 1-2 papers/year.

### 10.4 Allen Institute / Semantic Scholar Discord
- **Audience**: research-tool builders · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: niche, but relevant given your tooling work.

### 10.5 Russian DeFi Telegram macro (multiple groups)
- **Audience**: Russian crypto · **Effort**: ⚡ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: identify 10-15 RU TG groups; thoughtful answers without spam.

### 10.6 MIPT alumni / blockchain master applicants TG group
- **Audience**: peers / future colleagues · **Effort**: ⚡ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: introduce yourself; share path-experience.

### 10.7 HSE FCS internal Slack / portal
- **Audience**: own institution · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: announce papers/projects internally first.

---

## Category 11 — Video Channels

### 11.1 YouTube channel (educational)
- **Audience**: SEO-discoverable, durable · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: 10-15 min tutorials; "ERC-4626 audit walkthrough", "RAG eval methodology", "EVM bytecode features for ML"; closed-caption subtitles; blog companions.

### 11.2 YouTube Shorts (5.91% engagement — top format)
- **Audience**: same as YT but viral · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: 60s explainer clips; one technical insight per clip; reused from longer YouTube + LinkedIn videos.

### 11.3 Twitch coding streams
- **Audience**: dev community in-the-moment · **Effort**: 🏗️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: 2-hour live coding sessions; OR live audit walkthrough of an open contract.

### 11.4 RuTube channel
- **Audience**: Russian audience YouTube-blocked · **Effort**: ⚡ (mirror) · **Impact**: 🗓️ · **Autonomy**: 🤖 · **Risk**: 🟢
- **Recipe**: mirror Russian-language content from YT.

### 11.5 Vimeo professional portfolio
- **Audience**: clients seeking polished portfolio · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: archive demo videos in high quality.

---

## Category 12 — Audio Channels

### 12.1 Podcast guest appearances
- **Audience**: domain-specific subscribers · **Effort**: ⚙️ (per appearance) · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: pitch self to 3-5 podcasts/quarter: DeFi-focused (Bankless, The Defiant), academic (Talking Machines, Linear Digressions), Russian (НеТо.ML, Mind Match).

### 12.2 X Spaces appearances (as guest)
- **Audience**: live, engaged · **Effort**: ⚡ per session · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: be invited or DM Space hosts who cover smart-contract topics.

### 12.3 Twitter / X Live monthly AMA
- **Audience**: own audience · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: monthly "ask me anything about smart-contract security"; share recording afterwards.

### 12.4 Clubhouse (declining but still relevant in CIS)
- **Audience**: Russian-speaking audio · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: low priority; only if active CIS rooms found.

### 12.5 Discord stage events
- **Audience**: web3 community · **Effort**: ⚡ per event · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: speak at EF / Aave / Compound community stages.

---

## Category 13 — Public Speaking (Academic)

### 13.1 Invited university talks
- **Audience**: academic researchers · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: reach out to HSE, ITMO, MIPT, MSU CS departments to give 1-hour invited talk on bytecode-feature engineering. "If you give a talk, they know you exist" — direct cite from research.

### 13.2 Academic conference paper presentation
- **Audience**: peers in research community · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: target ICSE / S&P / IEEE Blockchain / NeurIPS workshops; submit RAG-Solidity + ai-yield-vault.

### 13.3 Workshop tutorial at conference
- **Audience**: motivated learners · **Effort**: 🏗️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: propose 3-hour tutorial "ML for Smart Contract Vulnerability Detection" at IEEE Blockchain / ICSE / DSN.

### 13.4 Keynote invitation
- **Audience**: top-tier · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: track record builds toward this; usually invited by conference chairs after years of contribution.

### 13.5 PhD/MSc dissertation defense (your own)
- **Audience**: small but credentialing · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: when you defend, record + publish video.

### 13.6 Seminar series at HSE FCS
- **Audience**: institutional · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: arrange 30-min seminar in FCS lab; recorded; share clips.

### 13.7 PhD reading group facilitation
- **Audience**: PhD students at your university · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: organize weekly RAG/security paper reading group.

---

## Category 14 — Public Speaking (Industry)

### 14.1 ETHGlobal hackathon presentation
- **Audience**: web3 builders worldwide · **Effort**: 🏗️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: enter ETHGlobal events; even non-winning projects get demo time.

### 14.2 DevConnect side events
- **Audience**: EF / serious devs · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: propose talk at any DevConnect satellite event; smaller bar.

### 14.3 EthCC (Paris) lightning talks
- **Audience**: European web3 · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: 5-min lightning talk slot; relatively easy to get.

### 14.4 PyData / PyCon talks
- **Audience**: Python community · **Effort**: 🏗️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: submit talk on ML evaluation methodology (bootstrap CIs) to PyData; high visibility.

### 14.5 Local meetups (Moscow Crypto, MoscowJS, etc.)
- **Audience**: local · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: start with smaller venues to build comfort; lots of meetups in Moscow.

### 14.6 Conference panel
- **Audience**: industry · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: lower bar than solo talk; pitch panel idea or volunteer.

### 14.7 Fireside chat with notable figure
- **Audience**: warm large · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: invite a respected researcher for a recorded conversation; mutual amplification.

### 14.8 Lightning talk at any meetup
- **Audience**: small but receptive · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: 5 min, 5 slides max; great for first speaking experience.

### 14.9 Demo Day at incubator (if accepted)
- **Audience**: investors · **Effort**: 🏗️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: apply to incubators (Outlier Ventures, Antler) with ai-yield-vault.

---

## Category 15 — Reviewer / Editorial / Judge Roles

### 15.1 Conference paper reviewer (PC member)
- **Audience**: research community credentialing · **Effort**: ⚙️ per round · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: volunteer for sub-PC at IEEE Blockchain / DSN; track record builds over years.

### 15.2 Journal editor (Associate Editor)
- **Audience**: top-tier credential · **Effort**: 🏗️ ongoing · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: invited usually; emerges from sustained PC service. Long horizon.

### 15.3 Grant peer review
- **Audience**: institutional credentialing · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: register as reviewer with EF Academic Grants, RFBR, EU Horizon. Reviewer pool sign-up.

### 15.4 Hackathon judging
- **Audience**: web3 community · **Effort**: ⚙️ per event · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: pitch yourself to ETHGlobal as judge; sign up as DoraHacks judge.

### 15.5 Awards committee membership
- **Audience**: institutional · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: usually invited.

### 15.6 OpenReview peer review (active reviewer)
- **Audience**: ML community · **Effort**: ⚙️ per cycle · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: register reviewer on NeurIPS/ICLR; selected via author profile.

---

## Category 16 — Open Source — Contribution Tactics

### 16.1 OpenZeppelin core PRs
- **Audience**: smart-contract dev community · **Effort**: ⚙️-🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: contribute test cases, security improvements; merged PRs = strong cred.

### 16.2 Foundry core contribution
- **Audience**: smart-contract devs · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: file detailed issues, contribute fixes; high visibility.

### 16.3 Slither security tool contribution
- **Audience**: security researchers · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: contribute custom detectors (you already have feature-engineering experience).

### 16.4 ethers.js / viem core PR
- **Audience**: JS/TS web3 community · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: smaller PRs for typing / docs.

### 16.5 PyTorch / scikit-learn issue resolution
- **Audience**: ML community · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: triage issues, file reproducibles.

### 16.6 Hermes Agent contributions (agent we're building on)
- **Audience**: AI agent community · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: contribute upstream once agent is running; positions you in agentic-AI community.

---

## Category 17 — Open Source — Releasing Assets

### 17.1 Public dataset release (Solidity contracts labeled for ML)
- **Audience**: ML researchers · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: release on HuggingFace Datasets; 100k+ Slither-labeled contracts from your ML Vuln paper.

### 17.2 Public model release (XGBoost ensemble from ML Vuln paper)
- **Audience**: practitioners · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: HuggingFace model card with weights; ONNX format for portability.

### 17.3 Benchmark suite release
- **Audience**: research community · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: package RAG-eval bootstrap CI methodology as `solidifi-bench`; reference impl + leaderboard.

### 17.4 Python library on PyPI
- **Audience**: developers · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: `evm-feature-engineering` library extracted from paper code.

### 17.5 Solidity library on npm / forge
- **Audience**: smart contract devs · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: extract reusable patterns from ai-yield-vault as `@sergei/vault-utils`.

### 17.6 Awesome-list authorship (one of your own)
- **Audience**: niche community · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: create `awesome-ml-smart-contract-security`; SEO-magnet for the topic.

### 17.7 Open course (free)
- **Audience**: learners · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: 8-10 video lectures on "ML for Smart Contract Auditing"; host on YouTube + sergeisolovev.com.

### 17.8 GitHub Pages docs site
- **Audience**: tool users · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: each released library has its own docs site; SEO win.

---

## Category 18 — Awards & Recognitions

### 18.1 30 Under 30 lists (Forbes Russia, Forbes Crypto, etc.)
- **Audience**: brand-recognition gold · **Effort**: ⚙️ (nomination) · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: prepare nomination dossier; ask network to nominate.

### 18.2 IEEE Computer Society awards
- **Audience**: academic CS · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: apply for early-career awards; have HSE/Mosoblbank co-nominate.

### 18.3 Best paper award nomination
- **Audience**: research community · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: target venues with best paper awards; emerge as candidate.

### 18.4 Ethereum Foundation grant recipient (badge)
- **Audience**: web3 cred · **Effort**: 🏗️ (proposal) · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: apply for ESP grant or Academic Grant Round; recipient credential strong.

### 18.5 Hackathon prize / honourable mention
- **Audience**: web3 · **Effort**: 🏗️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: enter ETHGlobal, ETHIndia, DoraHacks rounds.

### 18.6 ACI Russia board recognition
- **Audience**: Russian financial community · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: already on board; leverage for speaking + media.

### 18.7 Listed in industry reports as expert
- **Audience**: investors · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: respond to Gartner / Forrester / Messari analyst inquiries.

---

## Category 19 — Grants & Funding Programs

### 19.1 Ethereum Foundation Academic Grants
- **Audience**: academic credibility + funding · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: apply with smart contract security or DeFi research proposal; quarterly rounds.

### 19.2 Ethereum Foundation Ecosystem Support Program (ESP)
- **Audience**: builders · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: apply with open-source tooling proposal (e.g. ml-smart-contract-audit toolkit).

### 19.3 Ethereum Foundation PhD Fellowship ($24K, deadline April 22 each year)
- **Audience**: PhD students · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: requires PhD enrollment; relevant when Sergei starts PhD.

### 19.4 Protocol-specific grants (Optimism, Arbitrum, Aave Grants DAO, Compound Grants)
- **Audience**: ecosystem builders · **Effort**: ⚙️-🏗️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: monthly review; agent can scan grants.com / a16z aggregator.

### 19.5 Russian innovation grants (RFBR equivalents, Сколково, ФСИ)
- **Audience**: Russian academic + commercial · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: ФСИ "УМНИК" grant for early-career researchers (₽500K); apply via Sколково Tech.

### 19.6 EU Horizon Europe Marie Skłodowska-Curie
- **Audience**: top academic · **Effort**: 🏗️ very high · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: 2-year individual fellowships; requires academic host in EU country.

### 19.7 Gitcoin Grants
- **Audience**: web3 public goods · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: submit any open-source project to quarterly rounds; community matching.

### 19.8 Filecoin Foundation / IPFS grants
- **Audience**: decentralized storage · **Effort**: 🏗️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: if storing research data on IPFS; project for permanent preprint hosting.

### 19.9 a16z crypto research grants
- **Audience**: top-tier VC · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: invite-only; route via researcher network.

### 19.10 Mosoblbank R&D budget (your employer)
- **Audience**: internal · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: propose internal R&D projects.

---

## Category 20 — Hackathons & Competitions

### 20.1 ETHGlobal events (online + IRL)
- **Audience**: web3 builders · **Effort**: 🏗️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: enter 2-3/year; build on existing project (ai-yield-vault).

### 20.2 ETHIndia hackathon (annual large)
- **Audience**: large web3 · **Effort**: 🏗️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: virtual entry; high-quality competition.

### 20.3 DoraHacks bounty hunts
- **Audience**: web3 builders · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: rolling bounties; pick small wins.

### 20.4 Devpost competitions (AI/ML)
- **Audience**: AI/ML community · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: AWS / Google / OpenAI-sponsored AI hackathons.

### 20.5 Kaggle competitions
- **Audience**: ML practitioners · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: pick ones aligned with your strengths; medals = strong cred.

### 20.6 Sigma Squared / Code4rena audit contests
- **Audience**: smart contract auditors · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: participate in audit contests; even non-winning H findings = cred.

### 20.7 Bug bounties on Immunefi
- **Audience**: web3 security · **Effort**: 🏗️ · **Impact**: 🎯 (esp. monetary) · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: hunt $50K+ bounties on covered contracts.

### 20.8 Encode Club hackathons / education programs
- **Audience**: developers (often newer) · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: judge or mentor; visibility multiplier.

### 20.9 VK AllCups hackathons (already won "Ritmy Prodazh")
- **Audience**: Russian engineering · **Effort**: 🏗️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: continue Russian hackathon circuit; cumulative prizes = brand.

---

## Category 21 — Education / Knowledge Products

### 21.1 Coursera / edX course as instructor
- **Audience**: massive · **Effort**: 🏗️ very high · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: usually requires institutional backing; partner via HSE.

### 21.2 Udemy / LinkedIn Learning course
- **Audience**: self-paced learners · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: "Smart Contract Audits with ML"; income + brand.

### 21.3 LearnWeb3 / Buildspace / Alchemy University course-let
- **Audience**: web3 learners · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: contribute course materials.

### 21.4 Mentorship programs (CryptoChicks, Web3Bridge)
- **Audience**: future builders · **Effort**: ⚙️ ongoing · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: sign up as mentor; 1-2 mentees ongoing.

### 21.5 University TA-ing
- **Audience**: HSE students · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: ask HSE FCS for TA position; long-term institutional ties.

### 21.6 Office hours (your own, public)
- **Audience**: open · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: 1 hour/week public Zoom; anyone can join; record.

### 21.7 Book / ebook
- **Audience**: depth credential · **Effort**: 🏗️ very high · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: long-term project; "Machine Learning for Smart Contract Security" with Manning / O'Reilly / Packt.

### 21.8 Workshop at company offsite
- **Audience**: corporate · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: pitch to fintech/crypto companies; paid speaking.

---

## Category 22 — Press / Media Outreach

### 22.1 HARO (Help A Reporter Out) replies
- **Audience**: English-speaking journalists · **Effort**: ⚡ · **Impact**: 📅 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: subscribe HARO; respond to 2-3 inquiries/week on AI/crypto/security; ~5% hit rate; cumulative.

### 22.2 Featured.com (HARO alternative)
- **Audience**: same as HARO · **Effort**: ⚡ · **Impact**: 📅 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: redundant with HARO; pick one or both.

### 22.3 Pressfeed.ru (Russian HARO)
- **Audience**: Russian journalists · **Effort**: ⚡ · **Impact**: 📅 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: register, respond to inquiries in DeFi/AI/blockchain.

### 22.4 Op-ed pitch to TechCrunch / The Information / Forbes
- **Audience**: tech-media establishment · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: warm intro via network; pitch unusual angle (e.g. "Why RAG is wrong for security audits").

### 22.5 Cointelegraph Magazine guest piece
- **Audience**: crypto press · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: pitch via editor; emphasize researcher credibility.

### 22.6 Decrypt expert quote source
- **Audience**: crypto journalists · **Effort**: ⚡ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: cultivate 2-3 crypto journalists; offer expert quotes on smart-contract incidents.

### 22.7 Press release for project launches
- **Audience**: news aggregators · **Effort**: ⚡-⚙️ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: use Coingape / Crypto.News PR services for product launches.

### 22.8 Wikipedia author page (when notable)
- **Audience**: massive long-term · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: requires verifiable third-party coverage; defer until press citations exist.

### 22.9 ResearchGate news / press tagging
- **Audience**: academic-press cross-pollination · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: when paper cited in news, tag in RG.

### 22.10 Industry analyst engagement (Messari, Delphi Digital, Token Terminal)
- **Audience**: institutional investors · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: pitch to analyst desks as expert source; respond to their open queries.

---

## Category 23 — Partnership / Collaboration

### 23.1 Co-authored papers with established researchers
- **Audience**: academic cred · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: identify 3-5 researchers whose work overlaps; propose collaboration starting with small joint piece.

### 23.2 Co-organized workshop at conference
- **Audience**: research community · **Effort**: 🏗️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: propose workshop with 2-3 co-organizers; shared promotion.

### 23.3 Industry advisory boards (DAOs, startups)
- **Audience**: ecosystem cred · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: accept advisor positions at audited protocols; vet for reputation risk.

### 23.4 Audit partnerships (sign off on real audits)
- **Audience**: smart contract pros · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: do paid audits via OpenZeppelin / Code4rena / solo; publish summary reports.

### 23.5 Cross-promotion swaps with peer researchers
- **Audience**: cumulative reach · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: tweet-thread retweet swaps with 3-5 peer-tier researchers (similar follower counts).

### 23.6 Newsletter swaps
- **Audience**: warm subscribers · **Effort**: ⚡ · **Impact**: 📅 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: 1-2 newsletter swaps/quarter; "if you like X newsletter, you'll like Sergei's".

### 23.7 Joint open-source library with peer
- **Audience**: dev community · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: co-author tooling with 1 other researcher; shared credit, shared promotion.

### 23.8 Conference co-keynote or panel
- **Audience**: same as solo · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: lower bar than solo keynote.

---

## Category 24 — Direct Outreach (1:1)

### 24.1 Cold email to potential commercial clients
- **Audience**: target buyer · **Effort**: ⚙️ per recipient · **Impact**: 📅 · **Autonomy**: 🤝 · **Risk**: 🟡
- **Recipe**: < 150 words; specific to recipient; lead with insight not pitch.

### 24.2 LinkedIn InMail to investors
- **Audience**: warm tier VC · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 🤝 · **Risk**: 🟡
- **Recipe**: 3-5 sentences; reference shared connection or specific portfolio interest.

### 24.3 Cold reach to journalists for source-relationship
- **Audience**: 5-10 target journalists · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: "I read your piece on X; here's a related angle you might find interesting" — no ask first time.

### 24.4 DM to podcast hosts (guest pitch)
- **Audience**: 10-20 target podcasts · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 🤝 · **Risk**: 🟡
- **Recipe**: 3-paragraph pitch; specific episode topic; explain why your angle is novel.

### 24.5 Conference DM-network
- **Audience**: in-event peers · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: at any conference / DevConnect, DM 5-10 attendees for coffee chat.

### 24.6 Warm intro through ACI Russia / HSE network
- **Audience**: established contacts · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: leverage ACI / HSE existing relationships; ask for double opt-in intros.

### 24.7 Office hours request (to senior researchers)
- **Audience**: research credibility builders · **Effort**: ⚡ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: ask for 20-min calls; researchers often say yes.

---

## Category 25 — Lead-gen Mechanics

### 25.1 Newsletter signup form on every site page
- **Audience**: visitor → subscriber · **Effort**: ⚡ · **Impact**: 🎯 · **Autonomy**: 🤖 · **Risk**: 🟢
- **Recipe**: footer + inline + exit-intent (sparingly); use Substack widget or beehiiv embed.

### 25.2 Free tool (e.g. ERC-4626 risk checker web app)
- **Audience**: lead-generation · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: spin up small tool from ai-yield-vault learnings; collect emails on use.

### 25.3 Free calculator (e.g. MCDM weight optimizer)
- **Audience**: lead-gen · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: simple interactive tool; web app or notebook.

### 25.4 PDF report (e.g. "Bytecode-Feature Vulnerability Detection: State of 2026")
- **Audience**: enterprise prospects · **Effort**: 🏗️ · **Impact**: 📅 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: 20-page report with original data; gated download.

### 25.5 Cohort-based course (small, paid)
- **Audience**: serious learners · **Effort**: 🏗️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: 4-week paid cohort on "Smart Contract Audits with ML"; ~$500-2K per seat.

### 25.6 Free Discord community (your own)
- **Audience**: cultivated · **Effort**: ⚙️ ongoing · **Impact**: 🎯 · **Autonomy**: 🤝 · **Risk**: 🟡
- **Recipe**: launch Discord around "ML+Smart Contract Security"; only when other tactics show traction.

### 25.7 Webinar series (free, signup-gated)
- **Audience**: lead-gen · **Effort**: ⚙️ per session · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: monthly 45-min webinar; collect email; replay → blog post → social.

---

## Category 26 — SEO / Technical Discoverability

### 26.1 Sitemap submission to Google + Bing Webmaster Tools (✅ done for sergeisolovev.com)
- **Audience**: search engines · **Effort**: ⚡ · **Impact**: 🎯 · **Autonomy**: 🤖 · **Risk**: 🟢

### 26.2 IndexNow submission on content updates (✅ wired)
- **Audience**: Bing / Yandex priority crawl · **Effort**: 🤖 · **Impact**: 🎯 · **Autonomy**: 🤖 · **Risk**: 🟢

### 26.3 Schema.org JSON-LD on every page (✅ done for landing pages)
- **Audience**: rich results in Google · **Effort**: 🤖 · **Impact**: 🎯 · **Autonomy**: 🤖 · **Risk**: 🟢

### 26.4 Highwire Press citation_* meta tags (✅ done for 5 papers)
- **Audience**: Google Scholar · **Effort**: 🤖 · **Impact**: 🎯 · **Autonomy**: 🤖 · **Risk**: 🟢

### 26.5 Backlink building (guest posts → backlink to sergeisolovev.com)
- **Audience**: search rank · **Effort**: ⚙️ per guest post · **Impact**: 🎯 · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: every guest post on dev.to / Hashnode / Medium has canonical + backlink.

### 26.6 Wikipedia citation (cite your work in relevant articles)
- **Audience**: massive · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: edit Wikipedia articles where your paper is a legitimate citation; not self-promo.

### 26.7 Wikipedia article about your project (if notable)
- **Audience**: massive · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: requires third-party press coverage; defer.

### 26.8 Internal link clusters (pillar pages)
- **Audience**: search engines · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 🤖 · **Risk**: 🟢
- **Recipe**: every blog post links to 2-3 pillar pages on sergeisolovev.com.

### 26.9 Anchor text optimization
- **Audience**: SEO · **Effort**: 🤖 · **Impact**: 🎯 · **Autonomy**: 🤖 · **Risk**: 🟢
- **Recipe**: agent uses descriptive anchor text on all internal/external links.

### 26.10 Mobile-friendly + Core Web Vitals
- **Audience**: search rank · **Effort**: ⚙️ (one-time) · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: check via PageSpeed Insights; sergeisolovev.com already lean.

### 26.11 hreflang for Russian content
- **Audience**: RU search · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤖 · **Risk**: 🟢
- **Recipe**: when you have RU pages, add hreflang.

---

## Category 27 — Verifications / Trust Signals

### 27.1 LinkedIn verified profile (badge)
- **Audience**: LinkedIn · **Effort**: ⚡ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: verify via Microsoft Entra (free).

### 27.2 X verified (paid)
- **Audience**: X · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: $8/mo X Premium; signals seriousness.

### 27.3 ENS reverse-resolution + .eth profile
- **Audience**: web3 · **Effort**: ⚡ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: register sergeisolovev.eth; set as primary; on-chain identity.

### 27.4 keyOxide / GPG cross-verification
- **Audience**: technical purists · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤖 · **Risk**: 🟢
- **Recipe**: sign social media handles with GPG; publish via keyOxide.

### 27.5 GitHub verified domain (sergeisolovev.com)
- **Audience**: GitHub UI · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: add DNS TXT record; GitHub shows "verified" badge.

### 27.6 figshare verified ORCID (✅ partial)
- **Audience**: academia · **Effort**: ⚡ · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢

### 27.7 Trusted-reviewer badges (Semantic Scholar / Publons)
- **Audience**: research · **Effort**: ⚡ per review · **Impact**: 🎯 · **Autonomy**: 👤 · **Risk**: 🟢

### 27.8 Speaker reel / professional headshots
- **Audience**: conference organizers · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: invest in 1-2 professional headshots; speaker reel from any talk.

---

## Category 28 — Live formats (AMA, office hours, streams)

### 28.1 Monthly Reddit AMA
- **Audience**: 100-10K depending subreddit · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: schedule AMAs in r/ethereum, r/MachineLearning quarterly.

### 28.2 Twitter/X Spaces hosting
- **Audience**: live followers · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: monthly host on a focused topic.

### 28.3 Office hours (public Zoom)
- **Audience**: open · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: 1 h/week; anyone can drop in.

### 28.4 Live coding streams (Twitch/YT)
- **Audience**: dev community · **Effort**: 🏗️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: weekly 1-2 hour live coding.

### 28.5 Live debate / discussion (cross-promote)
- **Audience**: combined audiences · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: structured debate with a peer who has opposing view.

---

## Category 29 — Localization

### 29.1 Translate top blog posts to Russian
- **Audience**: RU readers · **Effort**: ⚙️ per post · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: top-3 EN posts → Russian on Habr / Дзен. Don't translate everything.

### 29.2 Translate top posts to Chinese / Korean
- **Audience**: APAC web3 · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: top-1 post per quarter via Fiverr translator; post on WeChat / Velog.

### 29.3 Subtitled videos
- **Audience**: international · **Effort**: ⚙️ per video · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟢
- **Recipe**: auto-caption via OpenAI Whisper; human review for accuracy.

---

## Category 30 — Paid Promotion (consider only after organic plateau)

### 30.1 LinkedIn promoted post
- **Audience**: targeted professionals · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: $200-500 boost for proven organic posts; tight targeting (job title + company).

### 30.2 Google Ads on niche keywords
- **Audience**: searchers for "ERC-4626 audit" etc. · **Effort**: ⚙️ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: low-budget search ads; only target high-intent.

### 30.3 Podcast sponsorship (mid-tier shows)
- **Audience**: warm audience · **Effort**: ⚡ · **Impact**: 📅 · **Autonomy**: 👤 · **Risk**: 🟢
- **Recipe**: sponsor 1-2 podcasts/quarter relevant to TradFi-to-AI/DeFi.

### 30.4 Newsletter sponsorship (e.g. The Defiant, Bankless Citizen)
- **Audience**: warm subscribers · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 👤 · **Risk**: 🟡
- **Recipe**: paid mentions; expensive but quality.

### 30.5 Twitter/X promoted tweet
- **Audience**: targeted · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟡
- **Recipe**: only boost organic winners; not for cold content.

### 30.6 Retargeting (site visitors)
- **Audience**: warm leads · **Effort**: ⚙️ · **Impact**: 📅 · **Autonomy**: 🤖 · **Risk**: 🟢
- **Recipe**: install Facebook Pixel + LI Insight Tag; retarget site visitors with newsletter signup ads.

---

## Category 31 — Cross-promotion / Syndication

### 31.1 Cross-post all blog content to dev.to / Hashnode / Medium with canonical
- **Audience**: distributed reach · **Effort**: ⚡ auto · **Impact**: 🎯 · **Autonomy**: 🤖 · **Risk**: 🟢

### 31.2 Submit blog posts to relevant aggregators (Hacker News, Lobste.rs, Reddit)
- **Audience**: developer discovery · **Effort**: ⚡ · **Impact**: 🗓️ · **Autonomy**: 🤝 · **Risk**: 🟡

### 31.3 RSS → Mastodon / BlueSky / Threads auto-broadcast
- **Audience**: distributed · **Effort**: 🤖 auto · **Impact**: 🗓️ · **Autonomy**: 🤖 · **Risk**: 🟢

### 31.4 Podcast → YouTube → Spotify → Apple → Substack post syndication
- **Audience**: omni-channel · **Effort**: 🤖 · **Impact**: 🎯 · **Autonomy**: 🤖 · **Risk**: 🟢

### 31.5 Newsletter "in case you missed it" weekly digest from social
- **Audience**: newsletter list · **Effort**: ⚡ · **Impact**: 📅 · **Autonomy**: 🤖 · **Risk**: 🟢

### 31.6 Content atomization (1 blog → 5 LI posts → 10 X tweets → 1 video → 3 shorts)
- **Audience**: cumulative · **Effort**: ⚙️ · **Impact**: 🎯 · **Autonomy**: 🤖 · **Risk**: 🟢
- **Recipe**: from each blog post, generate atomized content for all channels.

---

## Sources

- [Personal brand building 2026 (Robert Walters)](https://www.robertwalters.com.au/insights/career-advice/blog/how-to-build-a-strong-personal-brand.html)
- [How to Build a Personal Brand in Academia (Researcher.Life)](https://researcher.life/blog/article/how-to-build-a-personal-brand-in-academia/)
- [Content Distribution Strategy 2026 (beehiiv)](https://www.beehiiv.com/blog/content-distribution-strategies)
- [Content Distribution Strategy 2026 (Backlinko)](https://backlinko.com/content-distribution)
- [LinkedIn vs Twitter for Founders 2026 (Monolit)](https://monolit.sh/blog/linkedin-vs-twitter-x-for-founders-2026-pros-cons-which-platform-grows-your-business)
- [Crypto PR Marketing 2026 (EAK Digital)](https://eakdigital.com/crypto-pr-marketing-content-strategy-for-web3/)
- [DeFi Marketing Strategies 2026 (Surgence)](https://surgence.io/blog/defi-marketing)
- [Top Crypto Influencers 2026 (Crowdcreate)](https://crowdcreate.us/defi-influencers/)
- [B2B Thought Leadership 2026 (TopRank)](https://www.toprankmarketing.com/blog/b2b-thought-leadership-2026/)
- [Thought Leadership Strategies for B2B Tech (a88lab)](https://www.a88lab.com/blog/thought-leadership-strategies-b2b-tech)
- [Hashnode vs dev.to vs Medium (In Plain English)](https://resources.plainenglish.io/in-plain-english-vs-devto-hashnode-medium-and-hackernoon-best-platform-for-reach-in-2026)
- [Web3 Marketing Playbook (Formo)](https://formo.so/blog/the-web3-marketing-playbook-strategies-channels-and-tools-for-scalable-growth)
- [Decentralized SocialFi Farcaster vs Lens (BlockEden)](https://blockeden.xyz/blog/2026/01/15/decentralized-socialfi-farcaster-lens-protocol-web3-social-graph/)
- [Ethereum Foundation PhD Fellowship 2026](https://esp.ethereum.foundation/rounds/phdfp26)
- [Ethereum Foundation Q1 2026 Grants (Crypto News)](https://crypto.news/ethereum-foundation-q1-2026-grants-double-down-on-zk-cryptography-and-core-protocol-infrastructure/)
- [Ethereum Foundation Academic Grants](https://esp.ethereum.foundation/academic-grants)
- [ORCID for Researchers (info.orcid.org)](https://info.orcid.org/researchers/)
- [Researcher Profiles Building (ResearchMate)](https://researchmate.net/building-a-strong-academic-profile/)
- [The Hidden Power of the Invited Talk (Chronicle)](https://www.chronicle.com/article/the-hidden-power-of-the-invited-talk/)

---

## Quick-start sequence for sergei-brand-agent

Based on this catalog, the agent's **Strategist** should prioritize these tactics for Phase 1 (first 60 days):

**Already done** (✅): 26.1-26.4 (SEO foundation), 3.1 (GitHub README), 1.1 (blog mechanism)

**Phase 1 priorities (high-impact / low-effort / agent-friendly):**
1. 5.1 + 5.2 — Cross-post existing blog content to dev.to + Hashnode (agent: full auto)
2. 6.5 — Mastodon RSS auto-broadcast (agent: full auto)
3. 9.1, 9.2 — Answer 2-3 Stack Overflow / Ethereum Stack Exchange questions/week (agent: drafts, human verifies)
4. 22.1 / 22.3 — HARO + Pressfeed daily monitoring (agent: drafts replies)
5. 31.1, 31.3, 31.6 — Cross-post + atomization (agent: full auto for non-public-facing routes)

**Phase 1 priorities (high-impact / high-effort / human-required):**
6. 13.6 — HSE FCS seminar (Sergei arranges; agent drafts pitch)
7. 19.1, 19.4 — EF Academic Grants + Optimism / Arbitrum monthly review (agent scans, Sergei applies)
8. 20.1 — ETHGlobal upcoming event (agent identifies; Sergei builds)
9. 12.1 — Pitch 3-5 podcasts (agent drafts; Sergei sends)
10. 23.1 — Identify 3-5 co-authorship candidates (agent finds via OpenAlex; Sergei reaches out)

**Phase 2 priorities (months 2-3):**
- Newsletter launch (1.3)
- Russian Habr + Telegram channel (8.3, 8.1)
- YouTube channel (11.1)
- Farcaster + Lens (7.1, 7.3)
- HuggingFace dataset/model release (17.1, 17.2)

**Phase 3 priorities (months 4-6):**
- Cohort course (25.5)
- Open-source course (17.7)
- Conference workshop proposal (13.3)
- Industry advisory positions (23.3)
- Bug bounty hunting (20.7)
