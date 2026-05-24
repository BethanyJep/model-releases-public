---
name: explore-model/learn-more
description: Explain a model-related concept, term, command, or parameter on demand in layered depth — one-liner, analogy, then deep dive only on request.
when_to_use: |
  - Learner asks "what is X", "why does this matter", "explain Y".
  - The current step references a term the learner does not yet know.
  - Troubleshooting points at a concept gap rather than a fix.
do_not_use_for: |
  - Doing the next step (use `complete-step`).
  - Diagnosing an active error (use `troubleshoot`).
---

# Subskill: `learn-more` (explore-model)

Give a layered, on-demand explanation of a concept relevant to the
current model — without derailing the exploration.

## Playbook

1. Identify the concept. If the learner was vague, ask them to name the
   term or paste the line that confused them.

2. Reply in **three layers**, surfaced one at a time:
   - **Layer 1 — one sentence.** A plain-language definition.
   - **Layer 2 — a short analogy or example** grounded in this model's
     primary task or the current step. Stop here unless asked for more.
   - **Layer 3 — deep dive** with mechanism, tradeoffs, and links to the
     model card, evaluation scorecard, or the related workshop's plan
     (`.plans/<workshop>-plan.md`) where applicable. Only on
     explicit request.

3. Cross-reference, when relevant:
   - `model-card.md` for capability/limit context.
   - `evaluation.md` for how the concept shows up in the scorecard.
   - Other models in `models/` for comparison.
   - Workshops in `workshops/` that exercise the concept end-to-end.

4. After explaining, ask whether to resume `complete-step` or stay in
   `learn-more` for another concept.

## Guardrails

- Stay Microsoft Foundry / Azure-direct. Do not compare against
  competitor clouds by name.
- Do not write to `.progress.json` from this subskill — it is read-only
  for state.
- Keep Layer 1 to one sentence. The whole point is to not flood the
  learner.
