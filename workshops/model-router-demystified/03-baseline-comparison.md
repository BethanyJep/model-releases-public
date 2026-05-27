# Lab 3 — Baseline vs. Router: The First Comparison

> **Surface:** SDK · **Time:** ~20 min · **Outcome:** Side-by-side quality/cost/latency comparison with model distribution analysis

## What you'll do

Run your full prompt set against both the frontier baseline and Model Router. Generate a dashboard that answers: "Does Model Router save money on *my* workload without hurting quality?"

## Key concepts

| Concept | Detail |
|---|---|
| **Auto-eval pipeline** | Based on [Model Router Auto-Evaluation](https://github.com/microsoft-foundry/Model-Router-Auto-Evaluation) |
| **LLM-as-a-judge** | A judge model scores both baseline and router responses. Dual-ordered pairwise comparison cancels position bias. |
| **Router-aware cost** | `router_markup × input_tokens + underlying_model_input × input_tokens + underlying_model_output × output_tokens` |
| **Model distribution** | Which underlying models the router selected and how often — the most revealing chart |
| **Value composites** | Quality-per-dollar and quality-per-second — makes trade-offs explicit |

## Step-by-step

### 3.1 — Configure the comparison

Edit `code/config.py` to point at your deployments:

```python
# config.py is already set up to read from .env
# Verify your configuration:
python -c "from config import *; print(f'Router: {ROUTER_DEPLOYMENT}'); print(f'Baseline: {BASELINE_DEPLOYMENT}')"
```

### 3.2 — Run the baseline evaluation

Send all 50+ prompts to the frontier model:

```bash
python code/run_comparison.py --mode baseline --dataset sample-data/router-eval-prompts.jsonl
```

This calls the baseline model for every prompt and records:
- Response text
- Latency (wall-clock)
- Token usage (input + output)
- Cost (calculated from token pricing)

### 3.3 — Run the router evaluation

Send the same prompts to Model Router:

```bash
python code/run_comparison.py --mode router --dataset sample-data/router-eval-prompts.jsonl
```

For each prompt, this records everything above *plus*:
- Which underlying model was selected (`response.model`)
- Router markup cost

### 3.4 — Run the judge (quality scoring)

Score both sets of responses using LLM-as-a-judge:

```bash
python code/run_comparison.py --mode judge
```

The judge uses **dual-ordered pairwise comparison**:
1. Shows (baseline_response, router_response) → scores
2. Shows (router_response, baseline_response) → scores
3. If scores disagree → tie (eliminates position bias)

Plus **absolute scoring** (1–5) on:
- Accuracy
- Completeness
- Clarity
- Helpfulness

### 3.5 — Generate the dashboard

```bash
python code/run_comparison.py --mode report --output results/baseline-vs-balanced/
```

Open `results/baseline-vs-balanced/dashboard.html` in your browser.

### 3.6 — Analyze the results

**The eight charts you'll see:**

1. **Quality comparison** — pairwise win/loss/tie bar chart
2. **Cost comparison** — $/prompt for baseline vs. router
3. **Latency comparison** — p50, p90, p95 side-by-side
4. **Model distribution** — pie/bar chart showing which models the router selected
5. **Quality by category** — scores broken down by your prompt categories
6. **Cost by category** — where the savings come from
7. **Value score** — quality-per-dollar composite
8. **Efficiency score** — quality-per-second composite

### 3.7 — The revelation: model distribution by category

This is the most important chart. Look at the model distribution grouped by your `category` tags:

```
Expected pattern:
  simple_faq       → 80% gpt-5-nano, 20% gpt-4.1-nano
  policy_question  → 60% gpt-4.1-mini, 30% gpt-5-mini, 10% gpt-5
  trip_planning    → 40% gpt-5-mini, 40% gpt-5, 20% gpt-4.1
  receipt_expense  → 50% gpt-4.1-mini, 50% gpt-5-mini
  edge_case        → 70% gpt-5, 20% o4-mini, 10% gpt-5-mini
  multi_step       → 60% gpt-5, 30% o4-mini, 10% gpt-5-mini
```

> **The insight:** The router's model choices ARE the workload decomposition. You didn't write a single line of routing code. The router empirically identified which tasks need frontier intelligence and which can be handled by smaller models.

### 3.8 — Compare to manual routing

In the original `foundry-models-e2e` workshop, we wrote a custom router (`s03_router.py`) that classified intents into `plan_trip`, `policy_question`, `receipt_expense`. That required:
- Writing classification logic
- Deploying a nano model as a classifier
- Maintaining routing rules as task types evolve

Model Router does this automatically. The trade-off:
- ✅ Zero routing code
- ✅ Adapts as new models arrive
- ✅ No maintenance when task types change
- ⚠️ Less deterministic (you can't force a specific model per task)
- ⚠️ Need to validate with evals (which is what we're doing)

## Expected results (illustrative)

| Metric | Baseline (gpt-5) | Router (Balanced) | Delta |
|---|---|---|---|
| Quality (avg 1–5) | 4.3 | 4.2 | −2% |
| Cost per prompt | $0.028 | $0.011 | **−61%** |
| p50 latency | 3.2s | 2.1s | **−34%** |
| Quality-per-dollar | 153 | 382 | **+149%** |

## Checkpoint

- [ ] Both baseline and router runs completed successfully
- [ ] Judge scoring finished (all prompts have quality scores)
- [ ] `dashboard.html` generated and reviewed
- [ ] Model distribution chart shows differentiated routing by category
- [ ] Cost savings quantified (expect 40–60% on Balanced mode)
- [ ] Quality delta understood (expect <5% drop on Balanced)

---

**Next:** [Lab 4 — Custom evaluator: Policy-Adherence →](./04-custom-evaluator.md)
