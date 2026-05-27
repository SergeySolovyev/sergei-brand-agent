# Glossary — Preferred terminology, capitalizations, and BANNED phrases

The **Composer** uses this to write in-voice. The **Critic** uses this to reject drafts.
Both load on every invocation.

---

## Core identity terms

| Term | Preferred form | Avoid |
|---|---|---|
| Sergei's first name | **Sergei** (Latin English contexts) | "Sergey" except in Russian |
| Russian first name | **Сергей** | "Серж", "Сережа" |
| Last name | **Solovev** (Latin) / **Соловьев** (Russian) | "Soloviev", "Solovyev" |
| Tagline | **TradFi → AI → DeFi** | "From traditional finance to crypto" |
| Affiliation (EN) | **HSE University, Faculty of Computer Science** | "HSE FCS" first reference; "HSE FCS" OK after |
| Affiliation (RU) | **НИУ ВШЭ, факультет компьютерных наук** | "ВШЭ" first reference |
| Other affiliation | **Mosoblbank (PSB Group)** | "Mosoblbank" without parent context first time |
| Board role | **ACI Russia board member** | "ACIRu" |

---

## Technical terminology

| Concept | Preferred | Notes |
|---|---|---|
| Smart contract security | **smart contract security** | lowercase; "smart-contract security" with hyphen is fine |
| ERC-4626 | **ERC-4626** | hyphen required; never "ERC4626" or "erc-4626" |
| Limit order book | **limit order book** (first), **LOB** (after) | not "LOB" first reference |
| Multi-criteria decision making | **MCDM** | spell out first reference |
| Retrieval-augmented generation | **RAG** | spell out first reference |
| EVM bytecode | **EVM bytecode** | not "Ethereum bytecode" |
| DeFi | **DeFi** | not "Defi" or "defi" or "DEFI" |
| Web3 | **Web3** | not "web3" |
| Ethereum | **Ethereum** | not "ethereum" |
| Layer 2 | **L2** (after first "Layer 2") | |
| Zero-knowledge | **zero-knowledge** or **ZK** | not "zk-" prefix in prose |
| Bootstrap confidence interval | **bootstrap CI** | spell out first reference |
| F1 score | **F1** | not "f1" or "F-1" |
| Mean absolute error | **MAE** | spell out first reference |

---

## Russian-specific terminology

Russian content should use English technical terms where Russian doesn't have an established equivalent:

- ✅ "ERC-4626 хранилище" (NOT "ЕРСе4626 хранилище")
- ✅ "RAG-конвейер" (NOT "конвейер с дополненной выборкой генерации")
- ✅ "LOB-данные" (NOT "данные книги лимитных ордеров")
- ✅ "MCDM-подход"
- ✅ "smart contract" (можно склонять: "смарт-контракта")
- ✅ "blockchain" / "блокчейн" — оба ОК, но в одном тексте единообразно

---

## BANNED phrases (Critic auto-REVISE if found)

### Marketing-bro language
- "let's gooooo"
- "absolute game changer"
- "10x" / "100x" / "1000x" (when used hyperbolically, not as factual multiplier)
- "this changes everything"
- "the future is here"
- "you won't believe"
- "secret sauce"
- "north star metric" (overused in 2026)
- "value proposition" (in social posts; OK in documents)
- "10x engineer"
- "ninja" / "rockstar" / "guru"
- "thought leader" (self-applied)
- "in the weeds"
- "boil the ocean"
- "circle back"
- "move the needle"

### Fake-modest patterns
- "I'm just a researcher who..."
- "Not financial advice, but..."
- "Take this with a grain of salt..."
- "I'm no expert, but..."
- "Just my 2 cents..."

### LLM tells (NEVER use these)
- "as an AI", "as a language model"
- "I'm happy to help"
- "Certainly!", "Absolutely!", "Sure!" (as standalone openers)
- "It's worth noting that"
- "Delve into"
- "In the realm of"
- "Tapestry of"
- "In the ever-evolving landscape of"
- "Navigate the complexities of"
- "Demystify"
- "Unpack"

### Crypto-bro language
- "wagmi" / "ngmi" / "fud" / "fomo" (in original posts; OK in quoted references)
- "to the moon" / "moonshot" (as price prediction)
- "diamond hands" / "paper hands"
- "ape in"
- "rug pull" (only OK in security-analysis contexts, not casual)
- "shilling" (avoid; "promoting" if needed)
- "alpha" (when meaning "secret tip"; OK in trading-quant context)

### Self-promotional patterns
- "Read my post on..." (just link it; don't preface)
- "I wrote a thread on..." (just link it)
- "My recent paper shows..." (cite paper directly; "I show" only in academic contexts)
- "As I always say..."

### Financial-advice patterns
- "X will go up" / "X is undervalued"
- "Buy X now"
- "Sell X before..."
- "X is the next Y"
- "X targets $Y by Z"
- "guaranteed returns"
- "risk-free"
- "100% safe"

---

## Preferred phrasings (replacements for common temptations)

| Instead of | Use |
|---|---|
| "amazing results" | the actual numbers (F1=0.948, MCC=0.832) |
| "many people" | a specific count or "researchers in X" |
| "everyone agrees" | "the consensus in [community] is..." |
| "I think" | "the data suggests" (when backed) OR "I argue" (when staking position) |
| "obviously" | (delete the word; if obvious, the reader sees it) |
| "simply" | (delete) |
| "just" | (delete unless temporal) |
| "very" | (delete; pick a stronger noun/verb) |
| "really" | (delete) |
| "should" (recommending) | "consider" or describe trade-off |
| "powerful" | specific property (fast, accurate, low-cost, robust) |
| "robust" (without numbers) | quantify (3σ, 95% CI, etc.) |
| "scalable" | (specify dimension and limit) |

---

## Formatting rules

### Numbers
- Use SI separators in EN: "117,091 contracts"
- Use space separators in RU: "117 091 контрактов"
- Percentages: "0.948" or "94.8%" — don't mix in one sentence
- Currency: "$5K" / "$15M" for casual; "$5,000" / "$15,000,000" for formal
- Time: "2-3 weeks" not "2 to 3 weeks"

### Citations
- Always linkout DOI: `[10.6084/m9.figshare.32141182](https://doi.org/10.6084/m9.figshare.32141182)`
- Inline citation pattern: "(Solovev, 2026)" or "[Solovev 2026]"
- GitHub link pattern: `[ai-yield-vault](https://github.com/SergeySolovyev/ai-yield-vault)`

### Code references
- Inline: backticks for `function names`, `ERC-4626`, `keccak256`
- Block: triple backticks with language: ` ```solidity ` or ` ```python `

### Headlines / titles
- Sentence case for blog post titles, NOT Title Case
- "Machine learning for smart contract security" not "Machine Learning For Smart Contract Security"
- LinkedIn post headlines OK as Title Case (platform-native)

---

## Capitalization edge cases

| Term | Correct |
|---|---|
| `arxiv` (in URLs) but **arXiv** in prose | |
| **GitHub** | not "Github" or "github" |
| **JavaScript** | not "Javascript" |
| **TypeScript** | not "Typescript" |
| **Solidity** | (always capitalized) |
| **PyTorch** | not "Pytorch" |
| **scikit-learn** | (lowercase) |
| **XGBoost** | (uppercase X) |
| **Optuna** | (capitalized) |
| **NumPy** | (not "Numpy") |
| **pandas** | (lowercase, even at sentence start) |

---

## Tone calibration anchors

Sergei's tone is **precise, slightly dry, English with technical density**.

Good examples:
- ✅ "XGBoost + Optuna on 117,091 contracts achieves F1=0.948."
- ✅ "Naive RAG flips sign at n=250: from +2.0% Macro-F1 to -2.7%."
- ✅ "Sample-size choice changes your conclusion. Bootstrap CIs make this visible."

Bad examples (would fail Critic):
- ❌ "Just trained an absolutely massive XGBoost model and the F1 was incredible! 🚀🚀🚀"
- ❌ "This is a complete game-changer for smart contract security."
- ❌ "We need to talk about how RAG is failing us."

Russian tone is **peer-to-peer, warm but precise**. Не "вы", а контекстный «ты/Вы» в зависимости от собеседника. Технические термины — на английском как есть.

Good Russian examples:
- ✅ "Загрузил препринт по ERC-4626 + MCDM. 67 тестов, 76 800+ инвариантных вызовов, ноль нарушений."
- ✅ "RAG для аудита Solidity — звучит круто, но я показываю что на n=250 знак результата меняется."

Bad Russian examples:
- ❌ "Друзья! Расскажу вам сегодня про невероятный подход..."
- ❌ "В мире смарт-контрактов произошла настоящая революция!"
