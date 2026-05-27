# Lab 99 — Recap & Decision Framework

> **Outcome:** A clear decision framework for when and how to adopt Model Router

## What you accomplished

Starting from a single frontier model doing everything, you:

1. **Deployed** one Model Router endpoint (zero routing code)
2. **Measured** quality, cost, and latency against your baseline
3. **Discovered** the workload decomposition empirically (model distribution reports)
4. **Built** a domain-specific evaluator (Policy-Adherence with adaptive rubric)
5. **Optimized** via routing modes, model subset, and prompt caching
6. **Operationalized** with continuous eval, failover, and Foundry portal visibility

## The final scorecard

```
                              Quality   Cost/task   p50 latency   Policy-Adherence
────────────────────────────  ────────  ──────────  ────────────  ──────────────────
v1  Frontier only (gpt-5)     4.3       $0.028      3.2s          4.1
v2  Router Balanced            4.2       $0.011      2.1s          4.0
v3  Router Cost                3.9       $0.006      1.4s          3.6
v4  Router Quality             4.4       $0.025      3.0s          4.2
v5  Router + subset + cache    4.3       $0.009      1.8s          4.1   ← WINNER
```

**v5 delivers:** Same quality, 68% less cost, 44% less latency, full policy adherence — with zero custom routing code.

## Decision framework: Should you use Model Router?

### Use Model Router when:

| Signal | Why Router works |
|---|---|
| Your workload has diverse prompt complexity | Router routes simple prompts cheaply, complex prompts to frontier |
| You want zero routing code maintenance | No custom classifier to build, test, or update |
| Cost optimization is a priority | 40–70% savings depending on workload mix |
| You need auto-failover | Built-in transparent failover across models |
| New models should benefit you automatically | Router version updates add new models over time |
| You want a single endpoint for simplicity | One deployment, one API contract |

### Consider manual routing when:

| Signal | Why manual may be better |
|---|---|
| You need deterministic model-per-task | Router's choice is probabilistic, not guaranteed |
| You have strict latency SLOs per-task | Can't control which model handles which request |
| Compliance requires specific model-per-task audit trail | Router doesn't guarantee model selection |
| Your workload is homogeneous (all same complexity) | No benefit from routing — all prompts go to same model anyway |
| You need function-calling with specific model capabilities | Some models have different tool support |

### The hybrid approach

For many production systems, the best answer is **both**:

```
                     ┌─── Critical path (Quality mode, small subset) ───┐
User request ──────►│                                                    │
                     │   Model Router (Balanced, broad subset)           │
                     └─── High-volume path (Cost mode) ─────────────────┘
```

Use your own lightweight classifier to route between **2–3 router deployments** configured for different modes. You get the intelligence of routing + the control of per-path configuration.

## The three key takeaways

### 1. The router IS the decomposition

You don't need to guess which model fits which task. Deploy Model Router, send representative prompts, and inspect the model distribution. The router's choices empirically reveal your workload structure.

### 2. Evaluation is the whole game

Without evaluation, routing is a guess. With evaluation, routing is a measured optimization. The combination of:
- Generic quality scoring (LLM-as-a-judge)
- Domain-specific scoring (adaptive eval-rubric)
- Cost/latency measurement

...gives you the complete picture for decision-making.

### 3. Optimization is config, not code

Every improvement in this workshop was a configuration change:
- Routing mode: Balanced → Cost → Quality
- Model subset: all models → curated set
- Prompt caching: system prompt design + subset for cache hits

No application code was rewritten. The loop is: **measure → tune config → measure again**.

## What's next?

| Direction | How to continue |
|---|---|
| **Go deeper on evals** | Run the full `foundry-models-e2e` workshop for fine-tuning + synthetic data |
| **Scale the eval pipeline** | Use the [Model Router Auto-Evaluation repo](https://github.com/microsoft-foundry/Model-Router-Auto-Evaluation) for 1,000+ prompt runs |
| **Add more evaluators** | Build evaluators for other domains (tone, compliance, factual grounding) |
| **Production deployment** | Move from Global Standard to Data Zone Standard for data residency |
| **Multi-router architecture** | Deploy 2–3 routers for different workload segments |
| **Continuous improvement** | Set up weekly eval runs, track distribution drift, add new models to subset |

## References

| Resource | URL |
|---|---|
| Model Router concept docs | https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-router |
| How Model Router works | https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-router-how-it-works |
| Model Router how-to | https://learn.microsoft.com/azure/foundry/openai/how-to/model-router |
| Auto-Evaluation repo | https://github.com/microsoft-foundry/Model-Router-Auto-Evaluation |
| Custom evaluators | https://learn.microsoft.com/en-us/azure/foundry/concepts/evaluation-evaluators/custom-evaluators |
| Blog: Evals for Model Router | https://devblogs.microsoft.com/foundry/how-to-run-evals-for-model-router/ |
| Companion workshop | [`../foundry-models-e2e/`](../foundry-models-e2e/) |

---

*Congratulations — you've completed the Model Router Deep-Dive workshop!*
