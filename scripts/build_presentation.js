/* =============================================================================
 * build_presentation.js — produces Solovev_Brand_Agent_Presentation.pptx
 *
 * 10-slide deck explaining the agent. Palette matches sergeisolovev.com:
 *   amber #b38a5a, slate #334155, dark slate #1f2937, off-white #f4f3ef
 *
 * Run:
 *   npm install -g pptxgenjs
 *   node scripts/build_presentation.js
 * ============================================================================= */

const pptxgen = require("pptxgenjs");

// -----------------------------------------------------------------------------
// Theme
// -----------------------------------------------------------------------------
const C = {
    bgDark: "1F2937",      // dark slate — title/closing background
    bgLight: "FFFFFF",     // pure white — content slides
    accentBg: "F4F3EF",    // cream — accent cards inside light slides
    text: "1F2937",        // primary text on light
    textInverted: "F4F3EF",
    textMuted: "64748B",
    amber: "B38A5A",       // accent (TradFi→AI→DeFi gold)
    slate: "334155",       // secondary
    stroke: "E2E8F0",      // subtle borders
};

const F = {
    title: "Cambria",      // serif, available on Windows/Mac/most systems
    body: "Calibri",
};

// -----------------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------------
function addHeader(slide, kicker, title) {
    slide.addText(kicker, {
        x: 0.5, y: 0.35, w: 9, h: 0.3,
        fontSize: 11, fontFace: F.body, color: C.amber,
        bold: true, charSpacing: 4,
        align: "left", valign: "top", margin: 0,
    });
    slide.addText(title, {
        x: 0.5, y: 0.65, w: 9, h: 0.7,
        fontSize: 32, fontFace: F.title, color: C.text,
        align: "left", valign: "top", margin: 0,
    });
}

function makeShadow() {
    return { type: "outer", color: "000000", blur: 8, offset: 2, angle: 90, opacity: 0.08 };
}

function addCard(slide, x, y, w, h, opts = {}) {
    slide.addShape("rect", {
        x, y, w, h,
        fill: { color: opts.fill || C.accentBg },
        line: { color: opts.border || C.stroke, width: 0.5 },
        shadow: makeShadow(),
    });
}

// -----------------------------------------------------------------------------
// Presentation
// -----------------------------------------------------------------------------
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Sergei Solovev";
pres.title = "Sergei Brand Agent — Architecture & Roadmap";
pres.company = "sergeisolovev.com";

// =============================================================================
// SLIDE 1 — Title (dark)
// =============================================================================
{
    const s = pres.addSlide();
    s.background = { color: C.bgDark };

    // Small kicker (amber)
    s.addText("PERSONAL BRAND · AUTONOMOUS AGENT", {
        x: 0.5, y: 1.2, w: 9, h: 0.3,
        fontSize: 11, fontFace: F.body, color: C.amber,
        bold: true, charSpacing: 6, align: "left", margin: 0,
    });

    // Main title
    s.addText("Sergei Brand Agent", {
        x: 0.5, y: 1.6, w: 9, h: 1.4,
        fontSize: 60, fontFace: F.title, color: C.textInverted,
        align: "left", valign: "top", margin: 0,
    });

    // Subtitle
    s.addText([
        { text: "Autonomous promotion of TradFi → AI → DeFi expertise", options: { breakLine: true, color: C.textInverted } },
        { text: "Triad architecture · Computer Use · RentAHuman escalation",  options: { color: C.amber, italic: true } },
    ], {
        x: 0.5, y: 3.1, w: 9, h: 1.1,
        fontSize: 18, fontFace: F.body, valign: "top", margin: 0,
    });

    // Footer
    s.addText([
        { text: "27 May 2026", options: { breakLine: true } },
        { text: "github.com/SergeySolovyev/sergei-brand-agent", options: { color: C.amber } },
    ], {
        x: 0.5, y: 4.8, w: 9, h: 0.6,
        fontSize: 11, fontFace: F.body, color: C.textMuted,
        align: "left", valign: "bottom", margin: 0,
    });
}

// =============================================================================
// SLIDE 2 — Problem
// =============================================================================
{
    const s = pres.addSlide();
    s.background = { color: C.bgLight };
    addHeader(s, "01 · THE PROBLEM", "Personal brand maintenance doesn't scale");

    // Left column: bottleneck description
    s.addText([
        { text: "Five preprints (figshare, 2026) need amplification.",  options: { bullet: true, breakLine: true } },
        { text: "Three RINC submissions in pipeline (Молодой учёный, Интернаука, Universum).", options: { bullet: true, breakLine: true } },
        { text: "MIPT Blockchain master deadline: 31 July 2026.",       options: { bullet: true, breakLine: true } },
        { text: "AIRI 2026 summer school submission active.",            options: { bullet: true, breakLine: true } },
        { text: "Commercial visibility for clients, grants, investors.", options: { bullet: true } },
    ], {
        x: 0.5, y: 1.7, w: 5.3, h: 3.2,
        fontSize: 14, fontFace: F.body, color: C.text,
        valign: "top", paraSpaceAfter: 6, margin: 0,
    });

    // Right column: big callout
    addCard(s, 6.2, 1.7, 3.3, 2.4);
    s.addText("4", {
        x: 6.2, y: 1.75, w: 3.3, h: 1.2,
        fontSize: 88, fontFace: F.title, color: C.amber,
        bold: true, align: "center", valign: "middle", margin: 0,
    });
    s.addText("channels to maintain", {
        x: 6.2, y: 3.0, w: 3.3, h: 0.4,
        fontSize: 14, fontFace: F.body, color: C.textMuted,
        align: "center", margin: 0,
    });
    s.addText("blog · LinkedIn · X · Telegram", {
        x: 6.2, y: 3.45, w: 3.3, h: 0.4,
        fontSize: 11, fontFace: F.body, color: C.slate,
        italic: true, align: "center", margin: 0,
    });

    // Bottom one-liner
    s.addText("One person · hundreds of opportunities · zero spare hours",  {
        x: 0.5, y: 4.7, w: 9, h: 0.4,
        fontSize: 14, fontFace: F.body, color: C.slate,
        italic: true, align: "left", margin: 0,
    });
}

// =============================================================================
// SLIDE 3 — Goal (three audiences)
// =============================================================================
{
    const s = pres.addSlide();
    s.background = { color: C.bgLight };
    addHeader(s, "02 · THE GOAL", "Commercial credibility for three audiences");

    const audiences = [
        ["Commercial clients", "CTOs · product VPs · fintech & crypto leadership", "They evaluate technical depth before signing contracts."],
        ["Grant committees",   "ETH Foundation · Сколково · innovation funds",     "They scout researchers with verifiable, citable output."],
        ["DeFi investors",     "VCs · angels · ecosystem treasuries",               "They look for builders with both code and credibility."],
    ];

    const cardY = 1.7, cardH = 2.3, cardW = 3.0, gap = 0.15;
    audiences.forEach(([title, who, why], i) => {
        const x = 0.5 + i * (cardW + gap);

        addCard(s, x, cardY, cardW, cardH);

        // Number tag
        s.addShape("ellipse", {
            x: x + 0.3, y: cardY + 0.25, w: 0.5, h: 0.5,
            fill: { color: C.amber }, line: { color: C.amber, width: 0 },
        });
        s.addText(String(i + 1), {
            x: x + 0.3, y: cardY + 0.25, w: 0.5, h: 0.5,
            fontSize: 18, fontFace: F.title, color: "FFFFFF", bold: true,
            align: "center", valign: "middle", margin: 0,
        });

        s.addText(title, {
            x: x + 0.3, y: cardY + 0.9, w: cardW - 0.6, h: 0.4,
            fontSize: 18, fontFace: F.title, color: C.text,
            bold: true, align: "left", margin: 0,
        });
        s.addText(who, {
            x: x + 0.3, y: cardY + 1.3, w: cardW - 0.6, h: 0.4,
            fontSize: 10, fontFace: F.body, color: C.amber,
            italic: true, align: "left", margin: 0,
        });
        s.addText(why, {
            x: x + 0.3, y: cardY + 1.65, w: cardW - 0.6, h: 0.6,
            fontSize: 11, fontFace: F.body, color: C.slate,
            align: "left", valign: "top", margin: 0,
        });
    });

    // Hub callout below
    s.addText("All paths converge on sergeisolovev.com — the long-lived asset.", {
        x: 0.5, y: 4.4, w: 9, h: 0.4,
        fontSize: 14, fontFace: F.body, color: C.slate,
        italic: true, align: "center", margin: 0,
    });
}

// =============================================================================
// SLIDE 4 — 3-layer architecture
// =============================================================================
{
    const s = pres.addSlide();
    s.background = { color: C.bgLight };
    addHeader(s, "03 · ARCHITECTURE", "Three-layer agent (Anthropic Managed Agents pattern)");

    const layers = [
        {
            label: "L1 · COGNITIVE AGENTS",
            tagline: "Strategist · Composer · Critic",
            detail: "Three LLM personas, event-triggered, Evaluator-Optimizer loop",
            color: C.amber,
        },
        {
            label: "L2 · TOOL CAPABILITIES",
            tagline: "Browser-Use · Computer Use · MCP · RentAHuman",
            detail: "Universal channel access — same affordances as a human at a PC",
            color: C.slate,
        },
        {
            label: "L3 · HARNESS",
            tagline: "Session · Sandbox · Trace/Eval · Credentials · Context",
            detail: "Production safety: Docker isolation, egress whitelist, audit log",
            color: C.bgDark,
        },
    ];

    const layerY = 1.7, layerH = 0.95, layerGap = 0.2;
    layers.forEach((layer, i) => {
        const y = layerY + i * (layerH + layerGap);

        // Layer bar
        s.addShape("rect", {
            x: 0.5, y, w: 6.5, h: layerH,
            fill: { color: layer.color },
            line: { color: layer.color, width: 0 },
            shadow: makeShadow(),
        });

        // Layer label (left)
        s.addText(layer.label, {
            x: 0.7, y: y + 0.1, w: 2.4, h: 0.35,
            fontSize: 11, fontFace: F.body, color: "FFFFFF",
            bold: true, charSpacing: 3, valign: "top", margin: 0,
        });

        // Tagline
        s.addText(layer.tagline, {
            x: 0.7, y: y + 0.4, w: 6.1, h: 0.3,
            fontSize: 14, fontFace: F.title, color: "FFFFFF",
            valign: "top", margin: 0,
        });

        // Detail
        s.addText(layer.detail, {
            x: 0.7, y: y + 0.68, w: 6.1, h: 0.25,
            fontSize: 10, fontFace: F.body, color: "FFFFFF",
            italic: true, valign: "top", margin: 0,
        });
    });

    // Right side: 5 Anthropic patterns
    s.addText("5 Anthropic patterns", {
        x: 7.3, y: 1.7, w: 2.4, h: 0.35,
        fontSize: 11, fontFace: F.body, color: C.amber,
        bold: true, charSpacing: 3, valign: "top", margin: 0,
    });
    const patterns = [
        "Orchestrator-Workers",
        "Evaluator-Optimizer",
        "Routing",
        "Parallelization",
        "Prompt Chaining",
    ];
    s.addText(patterns.map((p, i) => ({
        text: p,
        options: { bullet: { code: "25CF" }, breakLine: i < patterns.length - 1 },
    })), {
        x: 7.3, y: 2.1, w: 2.4, h: 2.5,
        fontSize: 11, fontFace: F.body, color: C.text,
        valign: "top", paraSpaceAfter: 4, margin: 0,
    });
}

// =============================================================================
// SLIDE 5 — Triad personas
// =============================================================================
{
    const s = pres.addSlide();
    s.background = { color: C.bgLight };
    addHeader(s, "04 · THE TRIAD", "Three cognitive agents, three distinct voices");

    const triad = [
        {
            tag: "STRATEGIST",
            role: "Editor-in-Chief lite",
            when: "Mondays 09:00 MSK + major events",
            duty: "Reads metrics, sets weekly themes, queues topics, drafts plans.",
            color: C.amber,
        },
        {
            tag: "COMPOSER",
            role: "Channel-aware writer",
            when: "Event-triggered",
            duty: "Four sub-voices: blog (long), LinkedIn (pro), X (terse), Telegram RU.",
            color: C.slate,
        },
        {
            tag: "CRITIC",
            role: "Adversarial reviewer",
            when: "After every draft",
            duty: "PASS · REVISE · REJECT. Catches fake DOIs, brand-drift, LLM tells.",
            color: C.bgDark,
        },
    ];

    const cardY = 1.7, cardH = 3.0, cardW = 3.0, gap = 0.15;
    triad.forEach((p, i) => {
        const x = 0.5 + i * (cardW + gap);

        // Card background
        s.addShape("rect", {
            x, y: cardY, w: cardW, h: cardH,
            fill: { color: C.accentBg },
            line: { color: C.stroke, width: 0.5 },
            shadow: makeShadow(),
        });

        // Top color band
        s.addShape("rect", {
            x, y: cardY, w: cardW, h: 0.6,
            fill: { color: p.color },
            line: { color: p.color, width: 0 },
        });

        // Tag
        s.addText(p.tag, {
            x, y: cardY + 0.15, w: cardW, h: 0.3,
            fontSize: 13, fontFace: F.body, color: "FFFFFF",
            bold: true, charSpacing: 4, align: "center", valign: "top", margin: 0,
        });

        // Role
        s.addText(p.role, {
            x: x + 0.3, y: cardY + 0.85, w: cardW - 0.6, h: 0.45,
            fontSize: 18, fontFace: F.title, color: C.text,
            bold: true, align: "left", valign: "top", margin: 0,
        });

        // When
        s.addText("Invoked: " + p.when, {
            x: x + 0.3, y: cardY + 1.35, w: cardW - 0.6, h: 0.3,
            fontSize: 10, fontFace: F.body, color: C.amber,
            italic: true, align: "left", margin: 0,
        });

        // Duty
        s.addText(p.duty, {
            x: x + 0.3, y: cardY + 1.75, w: cardW - 0.6, h: 1.1,
            fontSize: 12, fontFace: F.body, color: C.slate,
            align: "left", valign: "top", margin: 0,
        });
    });

    // Flow caption
    s.addText("Strategist → Composer → Critic (loop max 2 rounds) → publish or escalate", {
        x: 0.5, y: 4.9, w: 9, h: 0.3,
        fontSize: 11, fontFace: F.body, color: C.textMuted,
        italic: true, align: "center", margin: 0,
    });
}

// =============================================================================
// SLIDE 6 — Tool capabilities
// =============================================================================
{
    const s = pres.addSlide();
    s.background = { color: C.bgLight };
    addHeader(s, "05 · CAPABILITIES", "Same toolkit a human has at a PC");

    const tools = [
        ["Browser-Use",        "Universal channel access",  "LinkedIn · X · GitHub · OpenAlex · CFP sites · grant portals — agent navigates them as a human would. Playwright + LLM driver."],
        ["Computer Use",       "Anthropic API (Phase 2)",   "Desktop fallback for non-browser tasks: file uploads, native dialogs, IDE operations. Used when Browser-Use insufficient."],
        ["MCP Servers",        "Typed integrations",        "GitHub · Telegram · filesystem · SQLite. Direct API calls where faster than browsing."],
        ["RentAHuman MCP",     "Judgment escalation",       "Real humans for: captcha, phone verification, subjective brand-tone calls, edge cases agent shouldn't decide alone. (Phase 2)"],
    ];

    const cardY = 1.7, cardW = 4.4, cardH = 1.45, gapX = 0.2, gapY = 0.2;
    tools.forEach(([name, sub, desc], i) => {
        const row = Math.floor(i / 2), col = i % 2;
        const x = 0.5 + col * (cardW + gapX);
        const y = cardY + row * (cardH + gapY);

        addCard(s, x, y, cardW, cardH);

        // Numeric badge
        s.addShape("ellipse", {
            x: x + 0.25, y: y + 0.25, w: 0.45, h: 0.45,
            fill: { color: C.amber }, line: { color: C.amber, width: 0 },
        });
        s.addText(String(i + 1), {
            x: x + 0.25, y: y + 0.25, w: 0.45, h: 0.45,
            fontSize: 14, fontFace: F.title, color: "FFFFFF",
            bold: true, align: "center", valign: "middle", margin: 0,
        });

        // Name
        s.addText(name, {
            x: x + 0.85, y: y + 0.22, w: cardW - 1.05, h: 0.32,
            fontSize: 16, fontFace: F.title, color: C.text,
            bold: true, align: "left", margin: 0,
        });

        // Subtitle
        s.addText(sub, {
            x: x + 0.85, y: y + 0.52, w: cardW - 1.05, h: 0.25,
            fontSize: 10, fontFace: F.body, color: C.amber,
            italic: true, align: "left", margin: 0,
        });

        // Description
        s.addText(desc, {
            x: x + 0.25, y: y + 0.82, w: cardW - 0.5, h: 0.55,
            fontSize: 10, fontFace: F.body, color: C.slate,
            align: "left", valign: "top", margin: 0,
        });
    });
}

// =============================================================================
// SLIDE 7 — Tiered autonomy
// =============================================================================
{
    const s = pres.addSlide();
    s.background = { color: C.bgLight };
    addHeader(s, "06 · BRAND-SAFETY", "Tiered autonomy — control matched to risk");

    const tiers = [
        ["1", "Full auto",         "Telegram personal · internal state · audit log",            "Zero risk — no public surface",                C.amber],
        ["2", "Critic-gated",      "sergeisolovev.com /blog/ · paper landing pages",            "Critic adversarial PASS required",             C.amber],
        ["3", "Human-approved",    "LinkedIn · X · outreach emails · grant applications",       "Sergei /approve via Telegram inline keyboard", C.slate],
        ["4", "RAH-escalated",     "Captcha · phone verification · judgment edge cases",         "Real human (RentAHuman) decides",              C.bgDark],
    ];

    const tableY = 1.7;
    const tableData = [
        [
            { text: "TIER",     options: { bold: true, color: "FFFFFF", fill: { color: C.text },   align: "center", valign: "middle", fontSize: 11 } },
            { text: "MODE",     options: { bold: true, color: "FFFFFF", fill: { color: C.text },   align: "left",   valign: "middle", fontSize: 11 } },
            { text: "EXAMPLES", options: { bold: true, color: "FFFFFF", fill: { color: C.text },   align: "left",   valign: "middle", fontSize: 11 } },
            { text: "GATE",     options: { bold: true, color: "FFFFFF", fill: { color: C.text },   align: "left",   valign: "middle", fontSize: 11 } },
        ],
        ...tiers.map(([n, mode, examples, gate, col]) => [
            { text: n,        options: { bold: true, color: "FFFFFF", fill: { color: col }, align: "center", valign: "middle", fontSize: 18, fontFace: F.title } },
            { text: mode,     options: { bold: true, color: C.text,   align: "left", valign: "middle", fontSize: 13, fontFace: F.body } },
            { text: examples, options: { color: C.slate, align: "left", valign: "middle", fontSize: 11, fontFace: F.body } },
            { text: gate,     options: { color: C.textMuted, italic: true, align: "left", valign: "middle", fontSize: 10, fontFace: F.body } },
        ]),
    ];

    s.addTable(tableData, {
        x: 0.5, y: tableY, w: 9.0,
        colW: [0.8, 1.7, 3.5, 3.0],
        rowH: [0.45, 0.65, 0.65, 0.65, 0.65],
        border: { pt: 0.5, color: C.stroke },
    });

    s.addText("Brand asymmetry: one bad post can erase 50 good ones. Optimize for downside protection.", {
        x: 0.5, y: 4.85, w: 9, h: 0.3,
        fontSize: 11, fontFace: F.body, color: C.textMuted,
        italic: true, align: "center", margin: 0,
    });
}

// =============================================================================
// SLIDE 8 — Playbook 120+ tactics
// =============================================================================
{
    const s = pres.addSlide();
    s.background = { color: C.bgLight };
    addHeader(s, "07 · PLAYBOOK", "120+ promotion tactics, 31 categories, single playbook");

    // Big stat (left)
    addCard(s, 0.5, 1.7, 3.0, 2.7);
    s.addText("120+", {
        x: 0.5, y: 1.85, w: 3.0, h: 1.2,
        fontSize: 80, fontFace: F.title, color: C.amber,
        bold: true, align: "center", valign: "middle", margin: 0,
    });
    s.addText("tactics catalogued", {
        x: 0.5, y: 3.1, w: 3.0, h: 0.35,
        fontSize: 12, fontFace: F.body, color: C.slate,
        align: "center", margin: 0,
    });
    s.addText("across 31 categories", {
        x: 0.5, y: 3.4, w: 3.0, h: 0.35,
        fontSize: 11, fontFace: F.body, color: C.amber,
        italic: true, align: "center", margin: 0,
    });
    s.addText("each: audience · effort · impact · autonomy · risk", {
        x: 0.5, y: 3.8, w: 3.0, h: 0.5,
        fontSize: 9, fontFace: F.body, color: C.textMuted,
        align: "center", margin: 0,
    });

    // Right side: category cloud
    const categories = [
        "Owned Media", "Academic Identity", "Code Portfolios",
        "Long-form Social", "Developer Publishing", "Short-form Social",
        "Web3-native", "Russian Platforms", "Q&A Sites",
        "Communities", "Video", "Audio",
        "Academic Speaking", "Industry Speaking", "Reviewer Roles",
        "OSS Contributions", "OSS Releases", "Awards",
        "Grants", "Hackathons", "Education",
        "Press Media", "Partnerships", "Direct Outreach",
        "Lead-Gen", "SEO Technical", "Verifications",
        "Live Formats", "Localization", "Paid Promo", "Cross-promotion",
    ];

    // Render as chips (3 columns)
    const chipCols = 3, chipsPerCol = Math.ceil(categories.length / chipCols);
    const chipBoxX = 3.8, chipBoxY = 1.7, chipBoxW = 5.7, chipBoxH = 2.7;
    const chipColW = chipBoxW / chipCols;

    for (let col = 0; col < chipCols; col++) {
        const colCats = categories.slice(col * chipsPerCol, (col + 1) * chipsPerCol);
        const items = colCats.map((c, i) => ({
            text: c,
            options: { bullet: { code: "25CF" }, breakLine: i < colCats.length - 1, color: C.text },
        }));
        s.addText(items, {
            x: chipBoxX + col * chipColW + 0.1, y: chipBoxY + 0.15, w: chipColW - 0.15, h: chipBoxH - 0.3,
            fontSize: 10, fontFace: F.body, color: C.text,
            valign: "top", paraSpaceAfter: 3, margin: 0,
        });
    }

    // Phase plan
    s.addText("Phase 1 priorities (first 60 days)", {
        x: 0.5, y: 4.6, w: 9, h: 0.3,
        fontSize: 11, fontFace: F.body, color: C.amber,
        bold: true, charSpacing: 3, align: "left", margin: 0,
    });
    s.addText("Cross-post blog content · Stack Exchange answers · HARO/Pressfeed monitoring · ETHGlobal scan · EF Academic Grants tracking", {
        x: 0.5, y: 4.9, w: 9, h: 0.5,
        fontSize: 10, fontFace: F.body, color: C.slate,
        italic: true, align: "left", valign: "top", margin: 0,
    });
}

// =============================================================================
// SLIDE 9 — Deployment & cost
// =============================================================================
{
    const s = pres.addSlide();
    s.background = { color: C.bgLight };
    addHeader(s, "08 · DEPLOYMENT", "Production stack, controlled cost");

    // Left: stack
    s.addText("Stack", {
        x: 0.5, y: 1.7, w: 4.7, h: 0.3,
        fontSize: 11, fontFace: F.body, color: C.amber,
        bold: true, charSpacing: 3, align: "left", margin: 0,
    });
    s.addText([
        { text: "Hetzner CX21 VPS (2 vCPU, 4 GB)",        options: { bullet: true, breakLine: true } },
        { text: "Ubuntu 24.04 LTS · hardened",            options: { bullet: true, breakLine: true, indentLevel: 1 } },
        { text: "Docker Compose · sandboxed",             options: { bullet: true, breakLine: true } },
        { text: "Tinyproxy egress whitelist",             options: { bullet: true, breakLine: true, indentLevel: 1 } },
        { text: "Hermes Agent (NousResearch)",            options: { bullet: true, breakLine: true } },
        { text: "Browser-Use + Playwright + Chromium",    options: { bullet: true, breakLine: true, indentLevel: 1 } },
        { text: "1Password Connect for secrets",          options: { bullet: true, breakLine: true } },
        { text: "SQLite event store · JSONL traces",      options: { bullet: true } },
    ], {
        x: 0.5, y: 2.0, w: 4.7, h: 2.9,
        fontSize: 12, fontFace: F.body, color: C.text,
        valign: "top", paraSpaceAfter: 4, margin: 0,
    });

    // Right: cost
    s.addText("Cost", {
        x: 5.5, y: 1.7, w: 4.0, h: 0.3,
        fontSize: 11, fontFace: F.body, color: C.amber,
        bold: true, charSpacing: 3, align: "left", margin: 0,
    });

    const costTable = [
        [
            { text: "Component", options: { bold: true, color: "FFFFFF", fill: { color: C.text }, fontSize: 10, valign: "middle" } },
            { text: "$/mo",      options: { bold: true, color: "FFFFFF", fill: { color: C.text }, fontSize: 10, valign: "middle", align: "right" } },
        ],
        [{ text: "VPS Hetzner CX21" }, { text: "$5",     options: { align: "right" } }],
        [{ text: "Anthropic Claude"  }, { text: "$15-25", options: { align: "right" } }],
        [{ text: "OpenRouter free"   }, { text: "$0-2",   options: { align: "right" } }],
        [{ text: "Browser-Use"        }, { text: "$0",     options: { align: "right" } }],
        [{ text: "1Password Connect"  }, { text: "$5",     options: { align: "right" } }],
        [
            { text: "Phase 1 total", options: { bold: true, fill: { color: C.accentBg } } },
            { text: "$25–40", options: { align: "right", bold: true, color: C.amber, fill: { color: C.accentBg } } },
        ],
    ];
    s.addTable(costTable, {
        x: 5.5, y: 2.0, w: 4.0,
        colW: [2.7, 1.3],
        rowH: [0.32, 0.32, 0.32, 0.32, 0.32, 0.32, 0.45],
        fontSize: 11,
        fontFace: F.body,
        color: C.text,
        border: { pt: 0.5, color: C.stroke },
    });

    // Phase 2 note
    s.addText("Phase 2 adds: RentAHuman ($20-50/mo for ~3-5 tasks) → total $50-100/mo", {
        x: 0.5, y: 5.05, w: 9, h: 0.3,
        fontSize: 10, fontFace: F.body, color: C.textMuted,
        italic: true, align: "center", margin: 0,
    });
}

// =============================================================================
// SLIDE 10 — Roadmap (dark closing)
// =============================================================================
{
    const s = pres.addSlide();
    s.background = { color: C.bgDark };

    // Title
    s.addText("ROADMAP · NEXT 6 MONTHS", {
        x: 0.5, y: 0.6, w: 9, h: 0.3,
        fontSize: 11, fontFace: F.body, color: C.amber,
        bold: true, charSpacing: 6, align: "left", margin: 0,
    });
    s.addText("Where this goes from here", {
        x: 0.5, y: 0.9, w: 9, h: 0.6,
        fontSize: 32, fontFace: F.title, color: C.textInverted,
        align: "left", valign: "top", margin: 0,
    });

    // Three phases as horizontal blocks
    const phases = [
        {
            tag: "PHASE 1 · MONTHS 1",
            title: "Scaffold + Triad live",
            bullets: [
                "VPS provisioned, sandbox up",
                "Triad publishes blog (Tier 2)",
                "LinkedIn drafts via Tier 3",
                "Critic catches canary set 8/8",
            ],
        },
        {
            tag: "PHASE 2 · MONTHS 2–3",
            title: "Discovery + outreach",
            bullets: [
                "RentAHuman wired in",
                "5+ discovery sources scanned",
                "Outreach skills with Critic policing",
                "Eval harness — voice-drift detection",
            ],
        },
        {
            tag: "PHASE 3 · MONTHS 4–6",
            title: "Optional Researcher agent",
            bullets: [
                "4th cognitive agent if needed",
                "Deep grant-proposal pre-fill",
                "Conference paper match-scoring",
                "Computer Use for native dialogs",
            ],
        },
    ];

    const pY = 1.85, pW = 3.0, pH = 2.7, gap = 0.15;
    phases.forEach((p, i) => {
        const x = 0.5 + i * (pW + gap);

        s.addShape("rect", {
            x, y: pY, w: pW, h: pH,
            fill: { color: C.slate },
            line: { color: C.amber, width: 0 },
            shadow: makeShadow(),
        });

        // Tag
        s.addText(p.tag, {
            x: x + 0.2, y: pY + 0.25, w: pW - 0.4, h: 0.3,
            fontSize: 10, fontFace: F.body, color: C.amber,
            bold: true, charSpacing: 3, align: "left", valign: "top", margin: 0,
        });

        // Title
        s.addText(p.title, {
            x: x + 0.2, y: pY + 0.6, w: pW - 0.4, h: 0.5,
            fontSize: 17, fontFace: F.title, color: C.textInverted,
            bold: true, align: "left", valign: "top", margin: 0,
        });

        // Bullets
        s.addText(p.bullets.map((b, j) => ({
            text: b,
            options: { bullet: { code: "25CF" }, breakLine: j < p.bullets.length - 1, color: C.textInverted },
        })), {
            x: x + 0.2, y: pY + 1.25, w: pW - 0.4, h: 1.35,
            fontSize: 10, fontFace: F.body, color: C.textInverted,
            valign: "top", paraSpaceAfter: 3, margin: 0,
        });
    });

    // Closing call to action
    s.addText("Repository ready · awaiting credentials to deploy", {
        x: 0.5, y: 4.85, w: 9, h: 0.4,
        fontSize: 14, fontFace: F.body, color: C.amber,
        italic: true, align: "center", margin: 0,
    });
    s.addText("github.com/SergeySolovyev/sergei-brand-agent", {
        x: 0.5, y: 5.18, w: 9, h: 0.3,
        fontSize: 11, fontFace: F.body, color: C.textMuted,
        align: "center", margin: 0,
    });
}

// -----------------------------------------------------------------------------
// Save
// -----------------------------------------------------------------------------
pres.writeFile({ fileName: "Solovev_Brand_Agent_Presentation.pptx" })
    .then(name => console.log(`[OK] Wrote ${name}`))
    .catch(err => { console.error("[FAIL]", err); process.exit(1); });
