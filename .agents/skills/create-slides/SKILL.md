---
name: create-slides
description: Author and build a MARP-based slide deck under `<target>/slides/`, producing `index.md` source plus `index.html`, `index.pptx`, and `index.pdf`. Works for any workshop or model folder.
when_to_use: |
  - "Create slides for this workshop / model"
  - "Build the deck for `workshops/<slug>`"
  - "Generate HTML / PPTX / PDF from a Markdown deck"
  - "Refresh the slide outputs after editing `slides/index.md`"
do_not_use_for: |
  - Authoring non-slide markdown (use `add-workshop` or `add-model`).
  - Driving a learner through slides (use `run-workshop` / `explore-model`).
  - Slide content unrelated to a `workshops/<slug>` or `models/<slug>` folder.
---

# Skill: `create-slides`

Author and build a MARP slide deck for a workshop or model. The skill
produces a `slides/` subfolder under the target with one Markdown source
(`index.md`) and three rendered outputs (`index.html`, `index.pptx`,
`index.pdf`). The shared theme keeps decks visually consistent across
the repo.

## What this skill produces

```
<target>/slides/
  index.md      # MARP source (Markdown + YAML frontmatter + theme CSS)
  index.html    # HTML deck (open in a browser; serve with `marp -s slides/`)
  index.pptx    # PowerPoint export
  index.pdf     # PDF export
```

`<target>` is either `workshops/<slug>/` or `models/<slug>/`.

## Toolchain

- [`@marp-team/marp-cli`](https://github.com/marp-team/marp-cli) — the
  `marp` CLI (already installed globally in this devcontainer).
- A headless Chromium for PDF / PPTX export. If `CHROME_PATH` is not
  set, Marp falls back to a system Chromium at `/usr/bin/chromium`.

Verify both with:

```bash
marp --version
which chromium || which chromium-browser || which google-chrome
```

If `marp` is missing, install once:

```bash
npm install -g @marp-team/marp-cli
```

## Playbook

1. **Pick the target.** If the learner did not name it, list
   `workshops/*/` and `models/*/` and ask which folder the deck belongs
   to. Reject anything outside those two roots.

2. **Decide author vs. rebuild.**
   - If `<target>/slides/index.md` exists, ask whether to **rebuild
     outputs** (most common) or **edit the source** first.
   - If it does not exist, **author** a new `slides/index.md` from
     `templates/index.md` and the target's content.

3. **Authoring `slides/index.md`** (when none exists yet):
   - Start from `.agents/skills/create-slides/templates/index.md` —
     copy verbatim, then replace the `{{...}}` tokens.
   - Pull content from these sources in priority order:
     - Workshop: `README.md` (objectives, audience), each `NN-*.md`
       (one or two slides per step), and `99-recap.md` (final scorecard
       + closing slide). The plan in `.plans/<slug>-plan.md`
       (if present) is the canonical narrative source — quote it for
       speaker beats.
     - Model: `README.md`, `model-card.md`, `evaluation.md`, and each
       exploration step.
   - Use the existing slide classes from the theme:
     - `<!-- _class: lead -->` for title and section bookends.
     - `<!-- _class: stage -->` for dark "what we'll do on stage" slides.
     - `<!-- _class: split -->` for two-column slides.
   - Put speaker notes inside `<!-- ... -->` comment blocks.
   - Keep to roughly **1 minute per slide** as a budgeting heuristic.

4. **Build outputs.** Run from the repo root, passing the target so
   relative paths resolve correctly:

   ```bash
   cd <target>
   export CHROME_PATH=${CHROME_PATH:-/usr/bin/chromium}
   marp slides/index.md -o slides/index.html
   marp slides/index.md --pdf  -o slides/index.pdf
   marp slides/index.md --pptx -o slides/index.pptx
   ```

   The `templates/build.sh` script wraps these commands. Run it with
   the target folder as the argument:

   ```bash
   bash .agents/skills/create-slides/templates/build.sh <target>
   ```

5. **Verify.** Confirm all three files exist and are non-empty:

   ```bash
   ls -la <target>/slides/index.{html,pdf,pptx}
   file <target>/slides/index.html <target>/slides/index.pdf <target>/slides/index.pptx
   ```

   Spot-check:
   - HTML: open in a browser; arrows navigate slides.
   - PDF: page count ≈ slide count.
   - PPTX: opens cleanly in PowerPoint / Keynote / LibreOffice.

6. **Live preview (optional).** While iterating on the source:

   ```bash
   marp -s <target>/slides/      # http://localhost:8080
   ```

   This watches `index.md` and reloads in the browser.

## Live-server mode

For long authoring sessions, prefer the live server over rebuilding:

```bash
marp -s <target>/slides/
```

When the source is settled, run the three-output build to refresh
artifacts before committing.

## Conventions

- One deck per workshop or model, named `index.md`. Use additional
  `<topic>.md` files in `slides/` only for genuinely separate decks
  (e.g. a 10-minute intro vs. the full 45-minute version) — and build
  each one explicitly.
- The MARP source is the **single source of truth**. Treat the
  rendered outputs as build artifacts: they may be committed (they are
  useful for review) but they should never be edited directly.
- The theme styles in the frontmatter are intentionally inlined so a
  deck can be opened on any machine without external CSS. When
  authoring a new deck, **start from `templates/index.md`** so the
  styling stays consistent across the repo.
- Stay Microsoft Foundry / Azure-direct in slide content. Do not name
  competitor clouds.
- Use inclusive language ("sentences" / "key points", not "bullets").

## Notes

- PDF/PPTX export requires Chromium. In CI or fresh devcontainers, set
  `CHROME_PATH=/usr/bin/chromium` (or wherever Chromium lives) before
  invoking `marp`.
- Large image embeds inflate the PPTX. Keep raw image sizes
  proportional to the slide; downscale to ~1920×1080 unless you need
  print resolution.
- The `--allow-local-files` flag is only required when a slide
  references absolute local paths; relative paths inside `slides/`
  work without it.
