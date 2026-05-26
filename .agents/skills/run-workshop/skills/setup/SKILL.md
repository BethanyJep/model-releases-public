---
name: run-workshop/setup
description: Verify prerequisites from a workshop's `00-setup.md` one check at a time, then mark setup complete in `.progress.json`.
when_to_use: |
  - First time entering a workshop.
  - `00` is not in `completed_steps`.
  - Learner says "setup", "prereqs", "get ready", "what do I need".
do_not_use_for: |
  - Content steps after setup is complete (use `complete-step`).
  - Diagnosing a runtime error mid-step (use `troubleshoot`).
---

# Subskill: `setup`

Walk the learner through `workshops/<slug>/00-setup.md` one check at a
time. The goal is a green Verify section and `00` recorded in
`.progress.json.completed_steps`.

## Playbook

1. Open `workshops/<slug>/00-setup.md`. Do not paste the whole file.

2. Extract the Prereqs list and the Verify check.

3. For each prereq, in order:
   - Tell the learner what is being checked, in one sentence.
   - Run the smallest possible probe (e.g. `az --version`, `python --version`,
     `gh auth status`, `az account show`).
   - On success: confirm and move on.
   - On failure: offer the documented fix from the file. If none exists,
     dispatch to `troubleshoot` and return here when it resolves.

4. Run the Verify check from the file. If it passes:
   - Append `"00"` to `completed_steps` in `.progress.json`.
   - Set `current_step` to the next step (`"01"`).
   - Write the file back.

5. Tell the learner setup is done and offer to start `complete-step` for
   `01`.

## Guardrails

- Do not install anything without confirming with the learner first.
- Do not deploy cloud resources as part of setup unless the file
  explicitly says so.
- Keep responses short — one check, one result, one next action.
