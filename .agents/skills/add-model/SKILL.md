---
name: add-model
description: Scaffold a new entry under `models/<slug>/` with a README, model card, evaluation stub, and numbered exploration steps so learners can use `explore-model` to walk through it.
when_to_use: |
  - "Add a new model to this repo"
  - "Register a model for the catalog"
  - "Author skilling content for a Foundry model"
do_not_use_for: |
  - Walking a learner through an existing model (use `explore-model`).
  - Editing an existing model entry (open the model folder directly).
  - Authoring a workshop (use `add-workshop`).
  - Deploying a model to Foundry (this skill only scaffolds documentation).
---

# Skill: `add-model`

Scaffold a new model entry under `models/<slug>/` from a short interview.
Keeps the catalog consistent and produces step files that pair with the
`explore-model` skill (the learner-facing counterpart, analogous to
`add-workshop` ↔ `run-workshop`).

## What this skill produces

```
models/<slug>/
  README.md         # title, audience, exploration objectives, step index
  model-card.md     # capabilities, limits, intended use, evaluation pointers
  evaluation.md     # baseline scorecard (per-task quality/cost/latency)
  00-setup.md       # prereqs to call the model (project, deployment, auth)
  01-<topic>.md     # first exploration step (e.g. "first call")
  02-<topic>.md     # ...
  99-recap.md       # what was learned, where to go next
  .gitkeep          # placeholder for future assets
```

## Playbook

1. **Collect inputs** using `ask_user`, one question at a time:
   - `slug` — kebab-case, e.g. `gpt-5-mini-azure-direct`. Validate
     `^[a-z0-9][a-z0-9-]*$`.
   - `display_name` — short human title.
   - `family` — `frontier-reasoning`, `small-language-model`,
     `multimodal-vision`, `embedding`, or `other`.
   - `hosting_type` — `azure-direct` or `models-as-a-service`.
   - `primary_task` — what task this model is best at (one sentence).
   - `deployment_name` — the name code will call (e.g. `planner-gpt5mini`).
   - `audience` — one sentence on who the exploration is for.
   - `objectives` — between 1 and 6 learning objectives (numbered list).
   - `step_count` — integer between 1 and 8. For each step, ask for a
     short topic slug (kebab-case) and a one-line goal.

2. **Refuse to overwrite.** If `models/<slug>/` already exists, suggest
   `<slug>-v2`, `<slug>-east-us-2`, etc., and re-prompt.

3. **Render templates** from `./templates/`, substituting `{{slug}}`,
   `{{display_name}}`, `{{family}}`, `{{hosting_type}}`,
   `{{primary_task}}`, `{{deployment_name}}`, `{{audience}}`,
   `{{objectives}}`, `{{step_index}}`, and `{{today}}`. For each
   exploration step, copy `01-step.md` to `<NN>-<topic>.md` with
   `{{step_number}}`, `{{step_title}}`, `{{step_goal}}` substituted.

4. **Wire progress tracking.** Ensure `models/*/.progress.json` is
   covered by `.gitignore`. If not, add it.

5. **Update the model index.** If `models/README.md` exists, add a row
   to its catalog table. If it does not exist, create it with a header
   and a single-row table.

6. **Verify.** Run `ls models/<slug>/` and confirm files exist. Suggest
   next steps:
   - "Open `models/<slug>/model-card.md` and fill in the capabilities."
   - "Refine the exploration steps in `01-…md` through `<NN>-…md`."
   - "Then ask Copilot to use `explore-model` on `models/<slug>`."

## Conventions for exploration steps

- Steps follow the same shape as workshop steps: Goal, Prereqs, Steps,
  Verify, Troubleshoot, Next. The `explore-model` skill depends on these
  sections existing.
- Step 00 is always `00-setup.md` (deployment + auth checks). The last
  step is always `99-recap.md`.

## Notes

- Stay Foundry / Azure-direct in examples. Do not reference competitor
  clouds by name.
- Do not deploy anything. This skill is documentation-only.
- If the learner does not know a field, offer a sensible default and mark
  the placeholder with `TODO:` in the generated file.
- Use inclusive language — "key points" or "sentences" rather than
  "bullets".
