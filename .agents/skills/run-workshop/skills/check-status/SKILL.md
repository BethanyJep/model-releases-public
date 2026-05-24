---
name: run-workshop/check-status
description: Report where the learner is in a workshop — current step, completed steps, blockers — using `.progress.json` and filesystem signals.
when_to_use: |
  - Learner asks "where am I", "what's left", "what have I done".
  - Returning to a workshop after a break.
  - Before dispatching to `complete-step` when state is ambiguous.
do_not_use_for: |
  - Doing the next step (use `complete-step`).
  - Fixing an error (use `troubleshoot`).
---

# Subskill: `check-status`

Give the learner a short, accurate picture of where they are in the
workshop. No prose dump — a status line and a recommended next action.

## Playbook

1. Read `workshops/<slug>/.progress.json`. If absent, report "not
   started" and offer to dispatch to `setup`.

2. List `workshops/<slug>/` step files (`NN-*.md`). Cross-reference
   `completed_steps` and `current_step`.

3. Produce a short status block, e.g.:

   ```
   Workshop: foundry-intro
   Completed: 00 (setup), 01 (baseline-sdk)
   Current:   02 (model-selection)
   Remaining: 03, 04, 05, 99 (recap)
   Blocked:   no
   ```

4. If `blocked` is true, surface the note from `.progress.json.notes`
   and recommend `troubleshoot`.

5. Recommend one next action — almost always `complete-step` for the
   current step, or `setup` if `00` is still incomplete.

## Guardrails

- Do not infer "completed" from filesystem alone. `.progress.json` is the
  source of truth. If the file disagrees with what the learner says, ask
  rather than overwrite.
- Do not summarize the content of upcoming steps — only their numbers
  and topic slugs.
