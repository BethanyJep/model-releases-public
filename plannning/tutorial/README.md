# Right Model, Right Job - Contoso Travel Concierge

This is the **hands-on companion** to `PLAN.md`. Follow it end-to-end and you'll have every demo in the 45-minute session built, recorded-ready, and explainable.

> **Audience:** professionals who know AI but are new to Microsoft Foundry.
> **Region:** East US 2. **Model family:** Azure Direct `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.4-nano`.
> **Build budget:** ~7 days of evenings, toy-scale data.

---

## The narrative device: three progress bars

Everything in this tutorial moves three bars. We update them at the end of every step so the story is visible:

```
Quality   ░░░░░░░░░░  0%   (target ≥ 0.92 on the curated eval)
Cost      ██████████  11¢  (target ≤ 3¢ / task)
Latency   ██████████ 12.3s (target ≤ 8s p50)
```

- **Quality** = pass rate on a 20-row curated eval (plus the policy sub-eval after Step 6).
- **Cost** = $ per completed task on the demo trace.
- **Latency** = wall-clock p50 across the demo trace.

By the end of Step 8 all three bars are in the green:

```
Quality   █████████░  94%  ✅
Cost      ██░░░░░░░░  2.8¢ ✅
Latency   ███░░░░░░░  7.6s ✅
```

The whole arc is: **one frontier model doing every task → the right model for each task, evaluated against a per-task scorecard.**

---

## What you'll touch in Foundry

| Surface | What we use it for | When in the tutorial |
|---|---|---|
| **Foundry Portal** (low-code) | Provision project, browse the model catalog, try a prompt in the playground, review evals/red-team results, compare agent versions side-by-side | Steps 0, 1, and 8 |
| **Foundry SDK** (code-first, Python) | Build the agent, route between models, run evals, kick off fine-tuning, deploy versions | Steps 2–7 |
| **Foundry Skills** (AI-assisted code, e.g. Copilot CLI's `microsoft-foundry` skill) | Discover available models, deploy a model with one prompt, set up RBAC, scaffold evaluator code | Step 3 (model selection) and Step 6 (fine-tune) — but useful everywhere |

> **Two MCP tools you should know:** the Foundry MCP exposes `models_list`, `model_get`, `agent_get`, `evaluation_run`, and more. The `microsoft-foundry` skill in Copilot CLI wraps these. Anywhere this tutorial says *"ask the Foundry skill to…"* you can also call those MCP tools directly.

---

## Steps

| # | Step | Surface | What moves on the scorecard |
|---|---|---|---|
| 0 | [Prereqs & project](./00-setup.md) | Portal + CLI | (nothing yet) |
| 1 | [Baseline in the playground](./01-baseline-portal.md) | Portal (low-code) | Establish v1 = 11¢ / 12.3s / quality unknown |
| 2 | [Baseline agent in VS Code](./02-baseline-sdk.md) | SDK | Measure v1 quality = 0.61 |
| 3 | [Model selection with the Foundry Skill](./03-model-selection.md) | AI-assisted | Pick the right model **per task** |
| 4 | [Synthetic dataset generation](./04-synthetic-data.md) | SDK | Grow eval set 20 → ~200 rows |
| 5 | [Evaluations: curated, batch, online](./05-evaluations.md) | SDK | Quality bar goes from "blind" → measured |
| 6 | [Fine-tune `gpt-5.4-mini` for policy](./06-finetune.md) | SDK + Skill | Policy 0.81 → 0.94, cost ÷50 vs. frontier |
| 7 | [Assemble the multi-model agent (v3)](./07-multi-model-agent.md) | SDK | v3 = 2.8¢ / 7.6s / 0.94 ✅ |
| 8 | [Back to the portal — evals, red team, versions](./08-portal-review.md) | Portal | Compare v1 vs. v2 vs. v3 side-by-side |

---

## Files in this folder

```
tutorial/
├── README.md                      ← you are here
├── 00-setup.md
├── 01-baseline-portal.md
├── 02-baseline-sdk.md
├── 03-model-selection.md
├── 04-synthetic-data.md
├── 05-evaluations.md
├── 06-finetune.md
├── 07-multi-model-agent.md
├── 08-portal-review.md
├── sample-data/
│   ├── travel-policy.md           ← the 2-page sample policy
│   ├── eval-seed.jsonl            ← 20 curated rows
│   ├── synthetic-prompts.jsonl    ← seed prompts for §4 generation
│   └── carmen-trace.json          ← the on-stage demo input
└── code/
    ├── requirements.txt
    ├── s02_config.py             ← shared deployments + pricing
    ├── s02_tools_mock.py         ← mocked flight/hotel/booking tools
    ├── s02_scorecard.py          ← prints the progress bars
    ├── s02_baseline_agent.py     ← v1: gpt-5.4 does everything
    ├── s03_router.py             ← gpt-5.4-nano router
    ├── s04_generate_synthetic.py ← grow the eval set
    ├── s05_multi_model_agent.py  ← v2/v3: planner + router + mini + ft
    ├── s05_run_eval.py           ← curated + batch eval driver
    └── s06_finetune_policy.py    ← fine-tune gpt-5.4-mini on policy QA
```

Start with **[Step 0 — Prereqs & project](./00-setup.md)**.

