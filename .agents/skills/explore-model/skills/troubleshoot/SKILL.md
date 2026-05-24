---
name: explore-model/troubleshoot
description: Diagnose a failing model exploration step by matching the error against the step's Troubleshoot section, then falling back to interactive diagnosis.
when_to_use: |
  - A Verify check failed.
  - The learner pasted an error or says "it broke / doesn't work / stuck".
  - `.progress.json.blocked` is true.
do_not_use_for: |
  - Routine progress through a step (use `complete-step`).
  - Explaining a concept the learner does not yet know (use `learn-more`).
---

# Subskill: `troubleshoot` (explore-model)

Help the learner unblock the current step. Fast pattern match first,
interactive diagnosis second.

## Playbook

1. Capture the symptom: the failing command or SDK call, the error
   message, the step file in play. Ask for any missing piece, one
   question at a time.

2. Open the current step's `Troubleshoot` table. Look for a row whose
   Symptom matches what the learner reported.
   - On match: apply the Fix. Re-run the Verify check. If it passes,
     hand back to `complete-step` to advance.

3. If no row matches, run **interactive diagnosis**. Common model-call
   failure modes to consider first:
   - Wrong endpoint or deployment name.
   - Missing or expired credentials / wrong role.
   - Region or quota mismatch.
   - Request shape (model expects chat vs. completion vs. embeddings).
   - Token limit / context overflow.

   For each hypothesis: state it in one sentence, propose the smallest
   probe to confirm or refute it, then iterate. Stop after at most three
   hypotheses without progress and ask the learner if they want to
   escalate (open an issue, switch to `learn-more` on the underlying
   concept).

4. When resolved:
   - Set `.progress.json.blocked = false`.
   - Append a one-line note to `.progress.json.notes` describing the
     symptom and fix so future runs benefit.
   - Hand back to `complete-step`.

5. If unresolved, set `blocked = true`, record the symptom in `notes`,
   and recommend a next move (typically `learn-more` on the relevant
   concept).

## Guardrails

- Do not paste the entire step file. Quote only the matching
  Troubleshoot row.
- Do not invent fixes. If the documented fix does not match, say so and
  switch to interactive diagnosis.
- Never recommend running destructive commands (deleting deployments,
  rotating keys) without explicit confirmation from the learner.
