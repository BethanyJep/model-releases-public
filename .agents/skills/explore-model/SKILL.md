---
name: explore-model
description: Guide a learner through a model in `models/<slug>/` one step at a time, revealing only what they need next. Dispatches to setup, complete-step, check-status, troubleshoot, learn-more subskills.
when_to_use: |
  - "Explore the X model with me"
  - "Walk me through models/<slug>"
  - "Help me try the next step for this model"
  - "I'm stuck calling this model / what should I do now"
do_not_use_for: |
  - Creating a brand-new model entry (use `add-model`).
  - Editing model content as an author (open the files directly).
  - Running a workshop (use `run-workshop`).
  - Generic Q&A unrelated to a model in `models/`.
---

# Skill: `explore-model` (dispatcher)

Drive a learner through a model entry in `models/<slug>/` **one step at a
time**. This is the learner-facing counterpart to `add-model`, in the
same way `run-workshop` is the counterpart to `add-workshop`.

The learner should only ever see the actions for the current step —
never the full model folder dumped at once.

## Subskills

This skill dispatches to these subskills under `./skills/`:

| Subskill | Use when |
|---|---|
| [`setup`](./skills/setup/SKILL.md) | First time exploring this model, or `00-setup.md` checks are not yet green. |
| [`complete-step`](./skills/complete-step/SKILL.md) | The learner is ready to work on the current step. |
| [`check-status`](./skills/check-status/SKILL.md) | Learner is unsure where they are or what's blocked. |
| [`troubleshoot`](./skills/troubleshoot/SKILL.md) | A step's Verify check failed, or the learner is reporting an error. |
| [`learn-more`](./skills/learn-more/SKILL.md) | Learner asks for an explanation of a concept, term, or command. |

## Progress state

Per-model progress lives at `models/<slug>/.progress.json` (gitignored):

```json
{
  "model_slug": "gpt-5-mini-azure-direct",
  "started_at": "2026-05-24T10:00:00Z",
  "current_step": "01",
  "completed_steps": ["00"],
  "blocked": false,
  "notes": []
}
```

If the file is missing, treat the exploration as not yet started.

## Playbook

1. **Pick the model.** If the learner did not name one, list
   `models/*/` (folders only, excluding hidden) and ask which one.

2. **Load `.progress.json`** for the chosen model. If absent, create
   it with `current_step = "00"` and `completed_steps = []`.

3. **Choose a subskill.**
   - If `00` not in `completed_steps`, dispatch to `setup`.
   - Else if the learner asked "where am I / status", dispatch to
     `check-status`.
   - Else if the learner asked "why / what is X", dispatch to `learn-more`.
   - Else if the learner reports an error or a failed Verify, dispatch
     to `troubleshoot`.
   - Else dispatch to `complete-step` for the `current_step`.

4. **Reveal-only-the-current-step rule.** When you read a step file,
   show the learner *only* the Goal and the first unfinished Step
   action. Hold the rest until they confirm completion. Never paste the
   full model README or all step files into the conversation.

5. **Hand off softly.** After the subskill finishes its unit of work,
   summarize the next action in one or two sentences and ask whether
   the learner wants to continue, pause, or use a different subskill.

## Conventions for revealing steps

- Quote at most one action at a time from a step file.
- Translate the step's actions into a Copilot-driven flow (commands to
  run, files to open) instead of pasting the markdown verbatim.
- After each action, run or describe the Verify check before moving on.
- On Verify success, append the step number to `completed_steps`, bump
  `current_step`, and write back `.progress.json`.

## Pairing with workshops

If the learner finishes a model exploration and asks "what next?",
suggest a workshop in `workshops/` that uses this model, or another
model in `models/` to compare against. The exploration recap
(`99-recap.md`) is the right place to find those pointers.

## Notes

- Stay Microsoft Foundry / Azure-direct in examples; do not name
  competitor clouds.
- Use inclusive language ("sentences" / "key points", not "bullets").
