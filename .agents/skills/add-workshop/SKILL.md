---
name: add-workshop
description: Scaffold a new workshop under `workshops/<slug>/` with a README, numbered step files, and a recap, ready to be driven by the `run-workshop` skill.
when_to_use: |
  - "Create a new workshop"
  - "Start a new tutorial under workshops/"
  - "Author a hands-on learning module"
do_not_use_for: |
  - Running an existing workshop interactively (use `run-workshop`).
  - Adding a model entry (use `add-model`).
  - Editing one specific step of an existing workshop (open the file directly).
---

# Skill: `add-workshop`

Scaffold a new workshop under `workshops/<slug>/` from a short interview.
Files are laid out so the `run-workshop` skill can reveal them one step at
a time.

## What this skill produces

```
workshops/<slug>/
  README.md      # title, audience, objectives, step index
  00-setup.md    # prereqs, accounts, tools, environment
  01-<topic>.md  # first content step
  02-<topic>.md  # ...
  ...
  99-recap.md    # what was learned, where to go next
```

## Playbook

1. **Collect inputs** using `ask_user`, one question at a time:
   - `slug` — kebab-case, e.g. `foundry-intro`. Validate
     `^[a-z0-9][a-z0-9-]*$`.
   - `title` — short human title.
   - `audience` — one sentence on who this is for.
   - `objectives` — between 1 and 6 learning objectives (ask for them as
     a numbered list in one freeform response).
   - `step_count` — integer between 1 and 12 (excluding setup and recap).
   - For each step, ask for a short topic slug (kebab-case) and a one-line
     goal. Number them `01`, `02`, … with zero-padding.

2. **Refuse to overwrite.** If `workshops/<slug>/` already exists, suggest
   alternatives and re-prompt.

3. **Render templates** from `./templates/`:
   - `README.md` — substitute `{{slug}}`, `{{title}}`, `{{audience}}`,
     `{{today}}`, and the rendered objective + step lists.
   - `00-setup.md` — substitute `{{title}}` and seed the prereqs section
     with empty TODOs the learner will fill in.
   - For each content step, copy `01-step.md` to `<NN>-<topic>.md` and
     substitute `{{step_number}}`, `{{step_title}}`, `{{step_goal}}`.
   - `99-recap.md` — substitute `{{title}}` and link back to objectives.

4. **Wire progress tracking.** Ensure `workshops/*/.progress.json` is
   covered by `.gitignore` in the repo root. If it is not, add it.

5. **Verify.** List the new folder and confirm files exist. Show the
   learner the path and suggest:
   - "Open `workshops/<slug>/README.md` and refine the objectives."
   - "When ready, run `run-workshop` on this folder."

## Notes

- Steps follow a consistent shape (Goal, Prereqs, Steps, Verify,
  Troubleshoot, Next). `run-workshop` depends on these sections existing.
- Keep examples Foundry / Azure-direct.
- Use inclusive language — "key points" or "sentences" rather than
  "bullets".
