---
name: run-workshop/instructor-mode
description: Run a workshop in instructor mode — enables live feedback capture and granular progress tracking for demo/talk delivery.
when_to_use: |
  - "Run workshop as instructor"
  - "Run <slug> in instructor mode"
  - "Start workshop in demo mode"
do_not_use_for: |
  - Normal learner-driven workshop runs (use default run-workshop).
  - Authoring or editing workshop content (open files directly).
---

# Subskill: `instructor-mode`

Activate when the learner says **"run-workshop as instructor"** (or any
variant mentioning instructor/demo mode). This mode wraps the normal
`complete-step` flow with two additions:

1. **Live feedback capture** (take-feedback)
2. **Granular progress tracking** (progress.json with sub-step resolution)

---

## Activation

When instructor mode is active, announce:

> 🎓 **Instructor mode ON.** Feedback capture is active. Say `Feedback:`
> followed by your note at any time — it will be logged without
> interrupting the current step.

## 1. Take-Feedback Capability

### How it works

At any point during an instructor-mode run, the instructor can type a
message starting with `Feedback:` (case-insensitive). The skill:

1. **Ensures `.do-not-commit/` exists** at the repository root. Create it
   if missing — it is gitignored.
2. **Creates a feedback file** at:
   ```
   .do-not-commit/FEEDBACK.<short-lab>.<timestamp>.md
   ```
   Where:
   - `<short-lab>` = slug derived from the current step file name
     (e.g. `01-baseline` from `01-baseline-sdk.md`)
   - `<timestamp>` = ISO-compact format `YYYYMMDDTHHmmss`
   
   Example: `.do-not-commit/FEEDBACK.03-evaluate.20250526T143012.md`

3. **Appends the feedback entry** to that file using this format:
   ```markdown
   ## Feedback — Step <current_step>
   
   **Context:** <brief description of what was being demonstrated>
   **Request:** <the instructor's feedback text after "Feedback:">
   **Logged at:** <ISO timestamp>
   ```

4. **Acknowledges** with a one-line confirmation:
   > ✅ Feedback logged → `.do-not-commit/FEEDBACK.<short-lab>.<ts>.md`

5. **Does NOT interrupt** the current step. Return to where the
   instructor left off.

### Post-Run Fix Application

When the instructor stops the workshop run (says "stop", "done", "end
session", etc.), the skill:

1. Reads all `FEEDBACK.*.md` files from `.do-not-commit/` created in
   this session (filter by timestamp range from session start).
2. Summarizes the collected feedback as a numbered list.
3. Asks: "Would you like me to apply these fixes now?"
4. If yes — applies each fix to the workshop files, committing each
   logical change separately. If no — leaves the feedback files for
   later review.

---

## 2. Granular Progress Tracking

In instructor mode, progress is tracked at **sub-step granularity**
(e.g., `1.1`, `1.2`, `2.1`, `2.3`) instead of only whole steps.

### File Location

```
workshops/<slug>/progress.<timestamp>.json
```

Where `<timestamp>` is ISO-compact (`YYYYMMDDTHHmmss`) set at session
start. This allows multiple instructor runs without overwriting.

### Schema

```json
{
  "workshop_slug": "model-router-demystified",
  "mode": "instructor",
  "started_at": "2025-05-26T14:00:00Z",
  "current_step": "2.1",
  "completed_steps": [
    {
      "step": "1.1",
      "title": "Verify Azure CLI auth",
      "outcome": "az account show returned correct subscription",
      "completed_at": "2025-05-26T14:02:30Z"
    },
    {
      "step": "1.2",
      "title": "Deploy Model Router",
      "outcome": "Deployment succeeded in Sweden Central, endpoint active",
      "completed_at": "2025-05-26T14:05:10Z"
    }
  ],
  "feedback_files": [],
  "ended_at": null
}
```

### Sub-Step Numbering

- The major number is the workshop step file number (e.g. `01` → `1`,
  `02` → `2`).
- The minor number is the sequential action within that step file
  (first action = `.1`, second = `.2`, etc.).
- Parse actions from the step file's **Steps** section — each numbered
  or headed action increments the minor counter.

### Tracking Rules

- **On action start:** Set `current_step` to the new sub-step ID.
- **On action verified:** Append to `completed_steps` with title,
  outcome summary (one sentence), and timestamp.
- **On feedback logged:** Append filename to `feedback_files`.
- **On session end:** Set `ended_at` timestamp.

Write the progress file after every state change.

---

## Playbook (Instructor-Mode Flow)

1. **Activate.** Detect "as instructor" / "instructor mode" in the
   user's request. Announce activation message.

2. **Initialize progress file.** Create
   `workshops/<slug>/progress.<ts>.json` with schema above, empty
   `completed_steps`.

3. **Dispatch to subskills.** Use the same dispatch logic as the main
   `run-workshop` skill (setup → complete-step → etc.), but:
   - Track at sub-step granularity.
   - Watch for `Feedback:` prefixed messages — handle via take-feedback.
   - Do NOT ask "ready?" between sub-steps — in instructor mode, pace
     is faster. Just present the next action immediately.
   - In instructor mode, Copilot MAY run commands directly (unlike
     learner mode where the user must run them). This enables faster
     demo pacing.
   - Show **visual scorecards** at major step boundaries (same format
     as defined in the parent `run-workshop` SKILL.md).

4. **On session end.** Finalize progress file, summarize feedback, offer
   to apply fixes.

---

## Guardrails

- Feedback files go ONLY in `.do-not-commit/`. Never commit them.
- Progress files inside the workshop folder should be gitignored (add
  pattern `progress.*.json` to the workshop's `.gitignore` or repo
  `.gitignore` if not already present).
- Do not modify workshop source files during the run. Fixes happen only
  after the session ends and the instructor approves.
- Keep feedback acknowledgments to one line — do not break flow.
