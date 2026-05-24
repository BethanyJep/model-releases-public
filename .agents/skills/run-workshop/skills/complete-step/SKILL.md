---
name: run-workshop/complete-step
description: Drive the learner through the current step of a workshop, revealing only the next action and verifying completion before moving on.
when_to_use: |
  - Setup is complete and the learner is ready to do the current step.
  - Learner says "next step", "let's continue", "what do I do now".
do_not_use_for: |
  - Setup (use `setup`).
  - Diagnosing failures (use `troubleshoot`).
  - Explaining a concept (use `learn-more`).
---

# Subskill: `complete-step`

Drive the learner through the **current** step in `.progress.json` —
the file named `<current_step>-*.md` in `workshops/<slug>/`.

## Playbook

1. Read `.progress.json` to find `current_step`. Locate the matching
   file (e.g. `01-baseline-sdk.md`).

2. Open the file. Parse its sections: Goal, Prereqs, Steps, Verify,
   Troubleshoot, Next.

3. **Reveal-only-the-current-action rule.** State the Goal in one
   sentence. Then surface **one** action from the Steps list at a time.
   For each action follow the terminal-command interaction pattern:
   - **Give the command** — exact command in a code block, do not run it.
   - **Ask the learner to run it** — end with "Run that and share what you see."
   - **Wait for their output** — when they paste or describe results, read carefully.
   - **Analyse** — acknowledge numbers worth recording, then give the next action.
   - For file edits: open the file and make the change directly, then
     ask the learner to confirm it looks right.
   - For decisions they should make: ask explicitly before proceeding.

4. After each action, run the inline check or the step's Verify section.
   Do not advance until it passes.

5. On Verify success:
   - Append `current_step` to `completed_steps`.
   - Set `current_step` to the next numbered file (or `"99"` if recap is
     next; mark `current_step = "done"` after recap).
   - Write `.progress.json` back.
   - Summarize what was accomplished in one or two sentences.
   - Ask whether the learner wants the next step now, a break, or a
     different subskill.

6. If Verify fails, hand off to `troubleshoot` with the captured error.

## Guardrails

- Never paste the full step file or the workshop README into the chat.
- Never preview future steps. The next step is revealed only after the
  current one is marked complete.
- If a Verify check is missing from the file, ask the learner what they
  see and propose a check together before marking the step done.
