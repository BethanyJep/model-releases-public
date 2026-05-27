# Lab 7 — Operate: Monitoring, Failover & Continuous Evaluation

> **Surface:** SDK + Portal · **Time:** ~15 min · **Outcome:** Production-ready operations with continuous eval, failover, and Foundry portal visibility

## What you'll do

Set up production-grade operations for your Model Router deployment. Configure continuous evaluation, understand auto-failover behavior, and push results to the Foundry portal for governance.

## Key concepts

| Concept | Detail |
|---|---|
| **Auto-failover** | Built-in — if a model is throttled/unavailable, router redirects to next-best model transparently |
| **Failover + subset** | Your model subset doubles as your fallback pool. Use ≥2 models. |
| **Model distribution drift** | Over time, routing patterns may shift as the router version updates or traffic changes |
| **Continuous evaluation** | Sample N% of production traffic, score with your custom evaluator, alert on regression |
| **Foundry portal** | Cloud-graded visibility, governance, RBAC, version comparison |

## Step-by-step

### 7.1 — Understand automatic failover

Model Router includes built-in failover — no configuration needed for default deployments:

```
Normal flow:
  Prompt → Router → selects gpt-5-mini → response ✓

Failover flow (gpt-5-mini throttled):
  Prompt → Router → selects gpt-5-mini → 429 rate limit
                  → transparently retries → selects gpt-5 → response ✓
```

**For custom model subsets:**
- Your subset IS your fallback pool
- If you only have 1 model in subset → no failover possible
- Recommendation: **always include ≥2 models in your subset**

### 7.2 — Simulate and observe failover

```bash
python code/run_comparison.py --mode failover-test
```

This script:
1. Sends a burst of requests (exceed rate limits intentionally)
2. Observes which models handle the overflow
3. Reports: failover count, latency impact, model distribution during stress

### 7.3 — Monitor model distribution over time

Track which models the router selects across days/weeks. Look for drift:

```python
import json
from datetime import datetime

# After each eval run, record the distribution
distribution = {
    "timestamp": datetime.now().isoformat(),
    "total_requests": 50,
    "model_counts": {
        "gpt-5-nano": 12,
        "gpt-5-mini": 18,
        "gpt-5": 15,
        "o4-mini": 5
    }
}

# Append to a log file
with open("results/distribution-log.jsonl", "a") as f:
    f.write(json.dumps(distribution) + "\n")
```

**When distribution drifts significantly:**
- New models may have been added to the router version
- Your workload mix may have changed
- Re-run your evaluation to confirm quality hasn't regressed

### 7.4 — Set up continuous evaluation

Sample production traffic and score it with the Policy-Adherence evaluator:

```python
# Continuous eval pipeline (simplified)
# In production, this would run on a schedule (e.g., hourly, daily)

import random

def continuous_eval_sample(traffic_log, sample_rate=0.05):
    """Sample 5% of production traffic for evaluation."""
    sampled = [r for r in traffic_log if random.random() < sample_rate]
    return sampled

def check_regression(scores, threshold=3.5):
    """Alert if average policy-adherence drops below threshold."""
    avg = sum(s["result"] for s in scores) / len(scores)
    if avg < threshold:
        alert(f"⚠️ Policy-adherence regression: {avg:.2f} < {threshold}")
    return avg
```

### 7.5 — Push results to Foundry portal

Submit your evaluation results to Foundry for cloud-graded visibility:

```bash
# Authenticate
az login

# Submit results for cloud grading
python code/policy_adherence_evaluator.py --action submit-to-foundry \
    --input-dir results/baseline-vs-balanced/
```

In the Foundry portal, you'll see:
- Evaluation runs with per-item scores
- Quality trends over time
- Model Router vs. baseline comparisons
- RBAC-controlled access for the team

### 7.6 — Production readiness checklist

| Item | Status | Notes |
|---|---|---|
| Model Router deployed (Balanced mode) | ☐ | Sweden Central, Global Standard |
| Model subset configured (≥2 models) | ☐ | Ensures failover capability |
| Custom evaluator registered | ☐ | Policy-Adherence with adaptive rubric |
| Baseline comparison completed | ☐ | Quality within 2% of frontier |
| Continuous eval pipeline configured | ☐ | 5% sample rate, daily scoring |
| Regression alert threshold set | ☐ | Alert if policy-adherence < 3.5 |
| Foundry portal integration active | ☐ | Results visible in portal |
| Distribution monitoring in place | ☐ | Track model selection drift weekly |
| Failover tested | ☐ | Confirmed ≥2 models handle overflow |

### 7.7 — When to re-evaluate

Re-run your full evaluation when:

| Trigger | Why |
|---|---|
| Router version updates | New models may be added, changing distribution |
| You change model subset | Need to confirm quality still meets bar |
| Policy document changes | Ground truth shifts — update eval dataset |
| Weekly/monthly cadence | Catch slow drift before it becomes a problem |
| After rate limit changes | Different tier → different routing behavior |
| New model added to catalog | May want to add it to your subset |

## Checkpoint

- [ ] Understand auto-failover behavior and subset requirements
- [ ] Observed failover under simulated load
- [ ] Distribution monitoring configured (even if basic JSONL logging)
- [ ] Continuous eval concept clear (sample, score, alert)
- [ ] Results pushed to Foundry portal (or understand how to)
- [ ] Production readiness checklist reviewed

---

**Next:** [Lab 99 — Recap & decision framework →](./99-recap.md)
