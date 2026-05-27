---
name: run-workshop
description: Guide a learner through a workshop one step at a time, revealing only what they need for the next action. Dispatches to setup, complete-step, check-status, troubleshoot, learn-more subskills.
when_to_use: |
  - "Run the X workshop with me"
  - "Walk me through workshops/<slug>"
  - "Help me do the next step of this workshop"
  - "I'm stuck on a step / what should I do now"
  - "Run workshop as learner" (learner mode with feedback + progress)
  - "Run workshop as instructor" (instructor mode with fast pacing)
do_not_use_for: |
  - Creating a brand-new workshop folder (use `add-workshop`).
  - Editing workshop content as an author (open the files directly).
  - Generic Q&A unrelated to a workshop in `workshops/`.
---

# Skill: `run-workshop` (dispatcher)

Drive a learner through a workshop in `workshops/<slug>/` **one step at a
time**. The learner should only ever see the actions for the current
step — never the full workshop dumped at once.

## Modes

| Mode | Trigger | Behavior |
|---|---|---|
| **Default** | "Run workshop X" | Standard guided flow — reveal one action at a time |
| **Learner** | "Run workshop X as learner" | Feedback capture + granular progress + **learner executes all commands** |
| **Instructor** | "Run workshop X as instructor" | Feedback capture + granular progress + faster pacing (Copilot may run commands) |

> If no mode is specified, treat as **default** (same as learner for
> command execution — Copilot never runs commands on behalf of the user).

---

## Subskills

This skill dispatches to these subskills under `./skills/`:

| Subskill | Use when |
|---|---|
| [`setup`](./skills/setup/SKILL.md) | First time in the workshop, or `00-setup.md` checks are not yet green. |
| [`complete-step`](./skills/complete-step/SKILL.md) | The learner is ready to work on the current step. |
| [`check-status`](./skills/check-status/SKILL.md) | Learner is unsure where they are or what's blocked. |
| [`troubleshoot`](./skills/troubleshoot/SKILL.md) | A step's Verify check failed, or the learner is reporting an error. |
| [`learn-more`](./skills/learn-more/SKILL.md) | Learner asks for an explanation of a concept, term, or command. |
| [`instructor-mode`](./skills/instructor-mode/SKILL.md) | User says "run-workshop as instructor" — enables feedback capture and granular progress tracking with fast pacing. |

---

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

### Granular progress (learner + instructor modes)

When running in **learner** or **instructor** mode, create a timestamped
progress file with sub-step resolution:

```
workshops/<slug>/progress.<YYYYMMDDTHHmmss>.json
```

Schema:

```json
{
  "workshop_slug": "model-router-demystified",
  "mode": "learner",
  "started_at": "2025-05-26T14:00:00Z",
  "current_step": "2.1",
  "completed_steps": [
    {
      "step": "1.1",
      "title": "Verify Azure CLI auth",
      "outcome": "az account show returned correct subscription",
      "completed_at": "2025-05-26T14:02:30Z"
    }
  ],
  "scorecard": {
    "quality": null,
    "cost_per_task": null,
    "latency_p50": null,
    "custom_evals": {}
  },
  "feedback_files": [],
  "ended_at": null
}
```

Sub-step numbering: major = step file number (`01` → `1`), minor =
sequential action within that step (first action = `.1`, second = `.2`).

---

## Playbook

1. **Pick the workshop.** If the learner did not name one, list
   `workshops/*/` (folders only, excluding hidden) and ask which one.

2. **Detect mode.**
   - "as instructor" / "instructor mode" / "demo mode" → dispatch to
     [`instructor-mode`](./skills/instructor-mode/SKILL.md).
   - "as learner" / "learner mode" → activate learner-mode features
     (feedback capture, granular progress, visual scorecards) while
     staying in the main dispatcher.
   - Otherwise → default mode (same command-execution rules as learner,
     but no feedback capture or granular progress file).

3. **Load progress.** If learner/instructor mode, create
   `progress.<ts>.json`. Otherwise load `.progress.json` (create if
   absent with `current_step = "00"`, `completed_steps = []`).

4. **Choose a subskill.**
   - If `00` not in `completed_steps`, dispatch to `setup`.
   - Else if the learner asked "where am I / status", dispatch to
     `check-status`.
   - Else if the learner asked "why / what is X", dispatch to `learn-more`.
   - Else if the learner reports an error or a failed Verify, dispatch
     to `troubleshoot`.
   - Else dispatch to `complete-step` for the `current_step`.

5. **Reveal-only-the-current-step rule.** When you read a step file,
   show the learner *only* the Goal and the first unfinished Step
   action. Hold the rest until they confirm completion. Never paste the
   full workshop README or all step files into the conversation.

6. **Hand off softly.** After the subskill finishes its unit of work,
   summarize the next action in one or two sentences and ask whether
   the learner wants to continue, pause, or use a different subskill.

---

## Command execution rules (CRITICAL)

**Copilot MUST NOT run terminal commands on behalf of the user** in
default or learner modes. The interaction pattern is:

1. **Give the command.** Present exactly what to type, in a fenced code
   block. Do not run it yourself.
2. **Ask them to run it.** End your message with a clear prompt:
   - *"Run that in the terminal and share what you see."*
   - *"Paste that into Copilot Chat (or run in terminal) and tell me the result."*
3. **Wait for their output.** Do not proceed until they report the outcome.
4. **Analyze or troubleshoot.** If success → acknowledge, record any
   numbers for the scorecard, show the updated visual scorecard, and
   move to the next action. If failure → dispatch to `troubleshoot`.

> ⚠️ **Never** use bash/shell tools to execute workshop commands for the
> user. The learner must build muscle memory by running each command
> themselves. The only exception is when the learner explicitly says
> "run it for me" or in instructor mode where pacing takes priority.

---

## Visual Scorecards

At key milestones, display a **visual scorecard** to show progress and
reinforce the narrative arc. Use this format:

### After each major step completion

```
┌─────────────────────────────────────────────────────────────────┐
│  📊  SCORECARD — after Lab <N>: <Lab Title>                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Quality        ███████████████████░░░  4.2 / 5.0              │
│  Cost/task      ████████░░░░░░░░░░░░░  $0.011 (−61%)          │
│  Latency p50    ██████████████░░░░░░░  2.1s (−34%)            │
│  Policy-Adhere  ████████████████████░  4.0 / 5.0              │
│                                                                 │
│  ✅ Steps done: 1.1 → 1.2 → 2.1 → 2.2 → 3.1 → 3.2 → 3.3    │
│  ▶️  Next: 4.1 — Build the eval rubric                         │
│                                                                 │
│  Models used by router: gpt-4.1 (23%) · gpt-4.1-mini (52%)    │
│                          gpt-4.1-nano (25%)                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Scorecard rules

1. **Show after every major step** (when a step file is fully
   completed — all sub-steps done and Verify passes).
2. **Show a mini-scorecard** after milestone sub-steps that produce
   measurable results (e.g., first API call, first eval run).
3. **Populate from actual results.** Use numbers the learner reported
   from their terminal output. If not yet measured, show `—` or `TBD`.
4. **Track deltas.** Always show change vs. previous measurement
   (e.g., `−61%` for cost reduction).
5. **Persist in progress file.** Update the `scorecard` field in
   `progress.<ts>.json` whenever you display one.
6. **Workshop-specific metrics.** Read the workshop's README for which
   metrics to track. Common ones:
   - `foundry-models-e2e`: Quality (pass rate), Cost/task, Latency p50
   - `model-router-demystified`: Quality, Cost/task, Latency p50,
     Policy-Adherence, Model Distribution

### Mini-scorecard (inline, after key sub-steps)

```
📈 Quick check: Quality 4.2 | Cost $0.011/task (−61%) | Latency 2.1s
```

### Step completion badge

After each sub-step is verified, show:

```
✅ Step 3.2 complete — Router deployed in Balanced mode, Sweden Central
```

### Workshop completion banner

At the end of the workshop (after recap):

```
┌─────────────────────────────────────────────────────────────────┐
│  🎓  WORKSHOP COMPLETE — <Workshop Title>                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Final Scorecard:                                               │
│  Quality        ████████████████████░  4.3 / 5.0               │
│  Cost/task      ████░░░░░░░░░░░░░░░░  $0.009 (−68% vs v1)     │
│  Latency p50    ███████████░░░░░░░░░  1.8s (−44% vs v1)       │
│  Policy-Adhere  ████████████████████░  4.1 / 5.0              │
│                                                                 │
│  Total steps completed: 24                                      │
│  Duration: 47 minutes                                           │
│                                                                 │
│  Key wins:                                                      │
│  • Deployed Model Router — zero routing code                    │
│  • Built custom Policy-Adherence evaluator                      │
│  • Proved 68% cost reduction at same quality bar                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feedback capture (learner mode)

When running in **learner mode**, feedback capture is active:

1. If the learner types a message starting with `Feedback:` (case-insensitive):
   - Ensure `.do-not-commit/` exists at repo root.
   - Create/append to `.do-not-commit/FEEDBACK.<short-lab>.<timestamp>.md`
     where `<short-lab>` = slug from current step file name (e.g. `03-baseline`)
     and `<timestamp>` = `YYYYMMDDTHHmmss`.
   - Log: step context, the feedback text, and a timestamp.
   - Acknowledge with one line: `✅ Feedback logged → <path>`
   - Return to the current step without interruption.

2. **Post-run:** When the session ends, summarize all logged feedback
   and offer to apply fixes.

---

## Recommended learner layout

At the start of every workshop, suggest this VS Code window arrangement
once (skip if the learner already mentions they have it set up):

> **Suggested layout:** editor panel on the left, GitHub Copilot Chat on
> the right, integrated terminal docked at the bottom. This lets you read
> file diffs on the left, follow Copilot guidance on the right, and run
> commands below — all without switching windows.

---

## Conventions for revealing steps

- Quote at most one action at a time from a step file.
- Translate the step's actions into a Copilot-driven flow (commands to
  run, files to open) instead of pasting the markdown verbatim.
- After each action, ask the learner to run the Verify check and report
  the result. Do not advance until it passes.
- On Verify success:
  - Show the ✅ step completion badge.
  - If it's the last sub-step of a major step, show the full visual
    scorecard.
  - Append the step to `completed_steps`, bump `current_step`.
  - Write back the progress file.

---

## Notes

- Stay Microsoft Foundry / Azure-direct in examples; do not name
  competitor clouds.
- Use inclusive language ("sentences" / "key points", not violence-adjacent terms).
- In learner/instructor modes, the visual scorecard is the primary
  narrative device — it replaces long explanatory paragraphs about
  progress.

