---
name: run-workshop/troubleshoot
description: Diagnose a failing step by matching the learner's error against the step's Troubleshoot section, then falling back to interactive diagnosis.
when_to_use: |
  - A Verify check failed.
  - The learner pasted an error or says "it broke / doesn't work / stuck".
  - `.progress.json.blocked` is true.
do_not_use_for: |
  - Routine progress through a step (use `complete-step`).
  - Explaining a concept the learner does not yet know (use `learn-more`).
---

# Subskill: `troubleshoot`

Help the learner unblock the current step. Fast pattern match first,
interactive diagnosis second.

## Playbook

1. Capture the symptom: the failing command, the error message, the
   step file in play. Ask for any missing piece, one question at a time.

2. Open the current step's `Troubleshoot` table. Look for a row whose
   Symptom matches what the learner reported.
   - On match: apply the Fix. Re-run the Verify check. If it passes,
     hand back to `complete-step` to advance.

3. If no row matches, run **interactive diagnosis**:
   - State a one-sentence hypothesis.
   - Propose the smallest probe (a command, a log line, a config value)
     to confirm or refute it.
   - Iterate. Stop after at most three hypotheses without progress and
     ask the learner if they want to escalate (open an issue, ask a
     colleague, switch to `learn-more` to understand the concept).

4. When resolved:
   - Set `.progress.json.blocked = false`.
   - Append a one-line note to `.progress.json.notes` describing the
     symptom and fix so future runs benefit.
   - Hand back to `complete-step`.

5. If unresolved, set `blocked = true`, record the symptom in `notes`,
   and recommend a next move (typically `learn-more` on the relevant
   concept).

## Guardrails

- Do not paste the entire step file. Quote only the Troubleshoot row.
- Do not invent fixes. If the documented fix does not match, say so and
  switch to interactive diagnosis.
- Never recommend running destructive commands without explicit
  confirmation from the learner.
