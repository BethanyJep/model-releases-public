# Step 8 — Back to the portal: evals, red team, versions

**Goal:** close the loop. Show that everything you did from code is also *visible, governable, and comparable* from the Foundry Portal — which is what your security, compliance, and decision-maker stakeholders care about.

**Surface:** Foundry Portal.

**Time:** 30 min to set up, plus the on-stage walkthrough.

**Final scorecard:**
```
Quality   █████████░  0.94  ✅
Cost      ██░░░░░░░░  2.8¢  ✅
Latency   ███░░░░░░░  7.6s  ✅
```

We're not changing numbers in this step. We're proving the work.

---

## 8.1 — The Evaluation tab

Portal → **Evaluation**.

You should see (at minimum) three runs you created from `s05_run_eval.py`:

- `v1-batch`   (0.61)
- `v2-batch`   (0.78)
- `v3-final`   (0.94)

Click **Compare** → select v1 vs v3. The portal lays out side-by-side: quality scores, latency, cost, and per-row diffs.

**What to point at on stage:**
- Row-level diffs on the *policy* rows: v1 invents an answer, v3 cites Section 4.2 verbatim.
- The aggregate quality trend chart.
- The dataset version pinned at the top — *"these numbers are only meaningful because the dataset is fixed."*

## 8.2 — Red teaming (built-in)

Portal → **Evaluation** → **+ New run** → **Red team**.

Pick your deployment (`planner-gpt54` for the planner role) and select attack categories:
- Jailbreak
- Prompt injection
- Sensitive content
- Direct violence / self-harm / hate (toggle as appropriate)

Run it. The portal will run a panel of synthetic adversarial prompts and report attack success rate per category.

**What to point at on stage:**
- Categories where v3 is **stronger** than v1 (usually prompt injection — the router shape limits attack surface; the policy model has no tools).
- Any *new* failures introduced by giving the planner more autonomy.

> **Yina's line:** *"This is the difference between 'we tested it on Carmen's trip' and 'we tested it against an adversary'. Both matter. Foundry gives you the second one out of the box."*

## 8.3 — Agent versions, side-by-side

Portal → **Agents** → your agent → **Versions**.

If you registered each milestone as an agent version (recommended: do this after Steps 2, 5, 6 — the Foundry Skill's deploy sub-skill will do it automatically), you'll see v1.0, v2.0, v3.0 with:

- The deployment(s) bound to each version
- The eval run pinned to each version
- A "Compare" button

This is where you screenshot the **architecture diff**: v1 = 1 model, v3 = 4 deployments (counting the fine-tune).

## 8.4 — Tracing & datasets

Two more tabs worth pointing at briefly:

- **Tracing** — open the v3 run, drill into Carmen's trace. The portal shows the router → vision → policy(ft) → planner chain with per-call latency. This is the visual proof that the architecture is real.
- **Datasets** — your `eval-v1` should be listed with lineage back to the seed file and the synthetic generation run. *"This is what 'reproducible eval' actually means."*

## 8.5 — Online evaluation (production monitoring)

Briefly: Portal → **Evaluation** → **Continuous monitoring** → bind to your `planner-gpt54` deployment and pick a sample rate (e.g. 5% of traffic).

For the toy demo you won't have real traffic. **Show the setup screen** and explain: *"In production, this is where you catch the regression the day after a model update — not a quarter later in a postmortem."*

## 8.6 — The closing slide

```
The unit of progress is the model decision —
made per task, against a per-task scorecard.

What you saw:
  v1 → v3:  1 model → 4 deployments
  Quality:  0.61 → 0.94    (+54%)
  Cost:     $0.108 → $0.028  (–74%)
  Latency:  12.3s → 7.6s    (–38%)

Nothing here required heroics.
It required naming the jobs, measuring them,
and picking the right tool for each one.

Microsoft Foundry — Portal, SDK, Skills — gave us the surface.
The decisions were ours.
```

QR code → your repo. Drop the mic.

---

## You're done

If you've followed Steps 0–8 you have:

- A working multi-model agent on Foundry East US 2.
- A reproducible eval pipeline with versioned datasets.
- A fine-tuned `gpt-5.4-mini` deployment for policy.
- Portal artifacts (eval runs, red-team report, agent versions) ready for screenshots.
- Three progress bars that go from red to green over 45 minutes of stage time.

Now go rehearse. See `PLAN.md` §9.4 for the OBS recording recipe and §9.6 for the Day 1–Day 7 build calendar.
