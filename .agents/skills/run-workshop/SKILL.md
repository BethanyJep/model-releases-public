---
name: run-workshop
description: Guide a learner through a workshop one step at a time, revealing only what they need for the next action. Dispatches to setup, complete-step, check-status, troubleshoot, learn-more subskills.
when_to_use: |
  - "Run the X workshop with me"
  - "Walk me through workshops/<slug>"
  - "Help me do the next step of this workshop"
  - "I'm stuck on a step / what should I do now"
do_not_use_for: |
  - Creating a brand-new workshop folder (use `add-workshop`).
  - Editing workshop content as an author (open the files directly).
  - Generic Q&A unrelated to a workshop in `workshops/`.
---

# Skill: `run-workshop` (dispatcher)

Drive a learner through a workshop in `workshops/<slug>/` **one step at a
time**. The learner should only ever see the actions for the current
step — never the full workshop dumped at once.

## Subskills

This skill dispatches to these subskills under `./skills/`:

| Subskill | Use when |
|---|---|
| [`setup`](./skills/setup/SKILL.md) | First time in the workshop, or `00-setup.md` checks are not yet green. |
| [`complete-step`](./skills/complete-step/SKILL.md) | The learner is ready to work on the current step. |
| [`check-status`](./skills/check-status/SKILL.md) | Learner is unsure where they are or what's blocked. |
| [`troubleshoot`](./skills/troubleshoot/SKILL.md) | A step's Verify check failed, or the learner is reporting an error. |
| [`learn-more`](./skills/learn-more/SKILL.md) | Learner asks for an explanation of a concept, term, or command. |

## Progress state

Per-workshop progress lives at `workshops/<slug>/.progress.json` (gitignored):

```json
{
  "workshop_slug": "foundry-intro",
  "started_at": "2026-05-24T10:00:00Z",
  "current_step": "01",
  "completed_steps": ["00"],
  "blocked": false,
  "notes": []
}
```

If the file is missing, treat the workshop as not yet started.

## Playbook

1. **Pick the workshop.** If the learner did not name one, list
   `workshops/*/` (folders only, excluding hidden) and ask which one.

2. **Load `.progress.json`** for the chosen workshop. If absent, create
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
   full workshop README or all step files into the conversation.

5. **Hand off softly.** After the subskill finishes its unit of work,
   summarize the next action in one or two sentences and ask whether
   the learner wants to continue, pause, or use a different subskill.

## Recommended learner layout

At the start of every workshop, suggest this VS Code window arrangement
once (skip if the learner already mentions they have it set up):

> **Suggested layout:** editor panel on the left, GitHub Copilot Chat on
> the right, integrated terminal docked at the bottom. This lets you read
> file diffs on the left, follow Copilot guidance on the right, and run
> commands below — all without switching windows.

## Interaction pattern for terminal commands

This is the core loop for every action that involves running code:

1. **Give the command.** Tell the learner exactly what to type, formatted
   in a code block. Do not run it yourself unless the learner asks.
2. **Ask them to run it.** End your message with a prompt such as
   *"Run that in the terminal and share what you see."*
3. **Wait for their output.** When they paste or describe the result,
   read it carefully.
4. **Analyse or troubleshoot.** If it succeeded, acknowledge the result,
   note any numbers worth recording, and move to the next action. If it
   failed, hand off to the `troubleshoot` subskill with the captured error.

This pattern keeps the learner in control of pace and ensures they
understand what each command does before moving on.

## Conventions for revealing steps

- Quote at most one action at a time from a step file.
- Translate the step's actions into a Copilot-driven flow (commands to
  run, files to open) instead of pasting the markdown verbatim.
- After each action, run or describe the Verify check before moving on.
- On Verify success, append the step number to `completed_steps`, bump
  `current_step`, and write back `.progress.json`.

## Notes

- Stay Microsoft Foundry / Azure-direct in examples; do not name
  competitor clouds.
- Use inclusive language ("sentences" / "key points", not "bullets").
