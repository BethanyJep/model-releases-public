---
marp: true
theme: default
paginate: true
size: 16:9
header: ''
footer: ''
style: |
  /* ─────────────────────────────────────────────────────────────────
     Right Model, Right Job — Microsoft Foundry training deck
     A modern dark/light theme with violet→cyan accent gradients,
     Inter for prose, JetBrains Mono for code.
     ───────────────────────────────────────────────────────────────── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap');

  :root {
    --ink:        #0f172a;
    --ink-soft:   #334155;
    --muted:      #64748b;
    --paper:      #ffffff;
    --paper-2:    #f8fafc;
    --line:       #e2e8f0;
    --accent:     #6366f1;   /* indigo */
    --accent-2:   #06b6d4;   /* cyan   */
    --violet:     #8b5cf6;
    --green:      #10b981;
    --amber:      #f59e0b;
    --red:        #ef4444;
    --grad:       linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%);
    --grad-dark:  linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #155e75 100%);
  }

  section {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    font-size: 26px;
    color: var(--ink);
    background: var(--paper);
    padding: 60px 80px;
    letter-spacing: -0.01em;
  }

  h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 800; letter-spacing: -0.02em; color: var(--ink); }
  h1 { font-size: 44px; line-height: 1.1; margin: 0 0 24px; }
  h2 { font-size: 36px; line-height: 1.15; margin: 0 0 20px; }
  h3 { font-size: 28px; font-weight: 700; }

  p, li { line-height: 1.55; }
  strong { color: var(--ink); font-weight: 700; }
  em { color: var(--accent); font-style: normal; font-weight: 600; }

  blockquote {
    border: none;
    border-left: 6px solid var(--accent);
    padding: 16px 0 16px 28px;
    margin: 24px 0;
    color: var(--ink-soft);
    font-size: 28px;
    font-style: italic;
    background: linear-gradient(90deg, rgba(99,102,241,0.06), transparent);
  }

  code {
    font-family: 'JetBrains Mono', monospace;
    background: #eef2ff;
    color: #4338ca;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.9em;
  }
  pre {
    background: #0f172a;
    color: #e2e8f0;
    border-radius: 10px;
    padding: 22px 26px;
    font-size: 20px;
    line-height: 1.5;
    box-shadow: 0 8px 32px rgba(15,23,42,0.18);
  }
  pre code { background: transparent; color: inherit; padding: 0; }

  table {
    border-collapse: collapse;
    width: 100%;
    font-size: 22px;
    margin: 12px 0;
  }
  th {
    background: linear-gradient(135deg, #1e1b4b, #312e81);
    color: #fff;
    text-align: left;
    padding: 12px 16px;
    font-weight: 600;
    letter-spacing: 0.02em;
  }
  td { padding: 10px 16px; border-bottom: 1px solid var(--line); }
  tr:last-child td { border-bottom: none; }
  tr:nth-child(even) td { background: var(--paper-2); }

  ul, ol { padding-left: 28px; }
  li { margin: 8px 0; }
  li::marker { color: var(--accent); }

  header { color: var(--muted); font-size: 16px; padding: 24px 80px 0; }
  footer { color: var(--muted); font-size: 16px; padding: 0 80px 24px; }
  section::after {
    color: var(--muted);
    font-size: 14px;
    font-weight: 500;
  }

  /* ─── utility classes used by individual slides ─── */
  .scorecard {
    font-family: 'JetBrains Mono', monospace;
    font-size: 28px;
    line-height: 1.7;
    background: #0f172a;
    color: #e2e8f0;
    padding: 28px 36px;
    border-radius: 12px;
    box-shadow: 0 12px 40px rgba(15,23,42,0.25);
  }
  .scorecard .bar-red    { color: #fca5a5; }
  .scorecard .bar-amber  { color: #fcd34d; }
  .scorecard .bar-green  { color: #86efac; }
  .scorecard .check      { color: #10b981; font-weight: 700; }

  .pill {
    display: inline-block;
    padding: 6px 16px;
    background: var(--grad);
    color: white;
    border-radius: 999px;
    font-size: 18px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }

  .hero-stat {
    font-size: 96px;
    font-weight: 900;
    background: var(--grad);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1;
    letter-spacing: -0.04em;
  }

  .stat-row { display: flex; gap: 32px; margin-top: 28px; }
  .stat {
    flex: 1;
    background: var(--paper-2);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 24px;
    border-top: 4px solid var(--accent);
  }
  .stat .label { color: var(--muted); font-size: 16px; text-transform: uppercase; letter-spacing: 0.08em; }
  .stat .val { font-size: 44px; font-weight: 800; margin-top: 6px; }
  .stat .val.md { font-size: 28px; font-weight: 700; line-height: 1.3; }
  .stat .val.sm { font-size: 22px; font-weight: 700; line-height: 1.3; }
  .stat.good { border-top-color: var(--green); }
  .stat.bad  { border-top-color: var(--red); }

  .note { color: var(--muted); font-size: 22px; font-style: italic; }
  .note.sm { font-size: 18px; }
  .note.xs { font-size: 16px; }

  /* ─── slide variants via _class ─── */

  /* Title / closing slide */
  section.lead {
    background: var(--grad-dark);
    color: white;
    padding: 80px;
  }
  section.lead h1 { color: white; font-size: 72px; font-weight: 900; }
  section.lead h2 { color: #c7d2fe; font-weight: 500; font-size: 32px; }
  section.lead p, section.lead li { color: #e0e7ff; }
  section.lead em { color: #67e8f9; }
  section.lead strong { color: white; }
  section.lead::after { color: #c7d2fe; }

  /* Section dividers */
  section.divider {
    background: var(--grad);
    color: white;
    padding: 80px;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  section.divider .pill {
    background: rgba(255,255,255,0.18);
    color: white;
    border: 1px solid rgba(255,255,255,0.4);
    margin-bottom: 32px;
  }
  section.divider h1 { color: white; font-size: 88px; font-weight: 900; max-width: 14ch; }
  section.divider p { color: #e0e7ff; font-size: 28px; max-width: 30ch; }
  section.divider::after { color: rgba(255,255,255,0.7); }

  /* Quote / "the email" cold open */
  section.quote {
    background: var(--paper-2);
    padding: 80px 120px;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  section.quote blockquote {
    font-size: 36px;
    line-height: 1.4;
    color: var(--ink);
    border-left: 8px solid var(--accent);
    padding-left: 36px;
  }

  /* Hero stat slide */
  section.hero {
    background: var(--paper);
    text-align: center;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }

  /* Dark “stage” slide for scorecards */
  section.stage {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    color: #e2e8f0;
  }
  section.stage h1, section.stage h2 { color: white; }
  section.stage .note { color: #94a3b8; }
  section.stage::after { color: #64748b; }

  /* Two-column layout */
  section.split { display: grid; grid-template-columns: 1fr 1fr; gap: 48px; align-items: start; }
  section.split h1, section.split h2 { grid-column: 1 / -1; }

  /* Portrait layout — used with `![bg right:N%]`. Marp auto-reserves the
     right N% for the image, so we only need to tune typography here. */
  section.portrait p, section.portrait li { font-size: 24px; }
  section.portrait blockquote { font-size: 22px; padding: 12px 0 12px 20px; margin: 16px 0; }

  /* 2×2 tile grid — for slides with 4 short equal-weight ideas */
  .grid-2x2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px 32px; margin-top: 20px; }
  /* 1×N stacked tile list — for short, uniform enumerations (e.g. 5 challenges) */
  .list-5 { display: grid; grid-template-columns: 1fr; gap: 10px; margin-top: 14px; }
  .list-5 .tile { padding: 10px 18px; }
  .list-5 .tile p { font-size: 20px; margin: 2px 0; line-height: 1.35; }
  .tile {
    background: var(--paper-2);
    border: 1px solid var(--line);
    border-left: 4px solid var(--accent);
    border-radius: 10px;
    padding: 16px 20px;
  }
  .tile p { margin: 6px 0; font-size: 22px; line-height: 1.45; }
  .tile p:first-child { margin-top: 0; }
  .tile p:last-child { margin-bottom: 0; }
---

<!--
═══════════════════════════════════════════════════════════════════════
  {{title}} — speaker deck scaffold
  Generated by the `create-slides` skill from
  .agents/skills/create-slides/templates/index.md

  BUILD:
    bash .agents/skills/create-slides/templates/build.sh <target>
  or:
    marp slides/index.md -o slides/index.html
    marp slides/index.md --pdf  -o slides/index.pdf
    marp slides/index.md --pptx -o slides/index.pptx
    marp -s slides/                          # live server :8080

  Speaker notes live inside HTML comment blocks like this one.
  Custom slide styles via the `_class: name` directive on a slide.
═══════════════════════════════════════════════════════════════════════
-->

<!-- _class: lead -->
<!-- _paginate: false -->

<span class="pill">{{tagline}}</span>

# {{title}}

## {{subtitle}}

<br>

{{presenter_line}}

<!--
Speaker notes for the opener live here.
Replace {{tagline}}, {{title}}, {{subtitle}}, and {{presenter_line}}
with content from the workshop's README.md / 99-recap.md or the model
card.
-->

---

# Why we're here

{{problem_statement}}

<!--
One sentence on the problem this content addresses. For workshops,
pull from "Where we start" or the opening of `01-…md`. For models,
pull the "Primary task" / "Intended use" from `model-card.md`.
-->

---

# What you'll be able to do

{{objectives_block}}

<!--
A numbered list (1–6 items) drawn from `README.md` → Learning
objectives (workshop) or Exploration objectives (model). Aim for
short, action-verb statements.
-->

---

<!-- _class: stage -->

# {{section_title}}

{{section_note}}

<!--
Use stage class to introduce a new section. Keep these to one line.
Repeat the section/content slides pattern for each chunk of the
narrative.
-->

---

# {{step_title}}

{{step_body}}

<!--
One slide per step (or two: a "what we'll do" slide and a "what we
saw" slide). Pull content from `NN-<topic>.md` Goal + the key
artifact produced. Use ``` fenced code for commands.
-->

---

# {{scorecard_title}}

```
Quality   {{quality_bar}}  {{quality_value}}
Cost      {{cost_bar}}     {{cost_value}}
Latency   {{latency_bar}}  {{latency_value}}
```

<!--
For workshops with a scorecard narrative, place one of these slides
after each step that moves a bar. For models, replace with the
per-task scorecard from `evaluation.md`.
-->

---

# Recap

{{recap_block}}

<!--
Pull from `99-recap.md` "What you built" + "Objectives revisited".
Keep this to one slide if possible.
-->

---

<!-- _class: lead -->

# {{closing_title}}

{{closing_body}}

<!--
The "Now you" / call-to-action slide. Reference the repo, the
workshop folder, and any QR code. Keep to a single visual focus.
-->
