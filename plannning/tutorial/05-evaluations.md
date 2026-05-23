# Step 5 — Evaluations: curated, batch, online (SDK)

**Goal:** turn "the answer sounds good" into a number, and run the same number across v1, v2, and v3 so we can *prove* the journey.

**Surface:** Foundry SDK (`azure-ai-evaluation`) + Foundry Portal review.

**Time:** 60 min.

**Scorecard at end of step:**
```
Quality   ██████░░░░  0.61 → 0.78  ⬆️  (v2 measured)
Cost      ██████░░░░  $0.063
Latency   █████████░  9.4 s
```

Quality moves for the first time — because we *measured* the v2 agent (model-per-task from Step 3) against our 198-row eval, not because we changed code.

---

## 5.1 — Three eval flavors, three jobs

| Flavor | When | What it answers |
|---|---|---|
| **Curated (20 rows)** | Every commit | "Did I break a known case?" Fast smoke test. |
| **Batch (~200 rows)** | Before deploy | "How does this version score overall?" |
| **Online (continuous)** | Production traffic | "Is real-world quality drifting?" |

This step builds curated + batch. Online is shown in the portal in Step 8.

## 5.2 — Evaluators

We use three:

1. **Schema/constraint evaluator** (deterministic): does the JSON parse, do `expected_keys` appear, is `total_estimated_cost_usd ≤ max_total`?
2. **LLM-as-judge** (uses `gpt-5.4`): semantic correctness of policy answers and translation accuracy. Scored 1–5, normalized to 0–1.
3. **Safety/groundedness** (built-in `azure-ai-evaluation`): no hallucinated bookings, no PII leakage.

## 5.3 — The driver

`code/s05_run_eval.py`:

```python
# s05_run_eval.py — runs an agent factory over an eval set and scores it
import json, time, argparse
from statistics import mean
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.evaluation import evaluate, GroundednessEvaluator
from s02_config import PROJECT_ENDPOINT, DEPLOY_PLANNER
from s02_scorecard import print_scorecard, cost_of
# --- evaluators ---------------------------------------------------------

def schema_eval(row, response):
    try:
        obj = json.loads(response["answer"])
    except Exception:
        return {"score": 0.0, "reason": "non-json"}
    missing = [k for k in row["expected_keys"] if k not in obj]
    over = 0
    if "max_total" in row.get("expected_constraints", {}):
        if obj.get("total_estimated_cost_usd", 1e9) > row["expected_constraints"]["max_total"]:
            over = 1
    score = 1.0 if (not missing and not over) else 0.0
    return {"score": score, "missing": missing, "over_budget": bool(over)}

JUDGE_SYSTEM = """Score the agent's answer 1-5 for whether it correctly
satisfies the user's request and respects the stated constraints.
Return JSON: {"score": int, "reason": "..."}"""

def judge_eval(row, response, client):
    msg = (f"User asked: {row['input']}\n\nAgent answered:\n{response['answer']}")
    r = client.chat.completions.create(
        model=DEPLOY_PLANNER, temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": JUDGE_SYSTEM},
                  {"role": "user", "content": msg}])
    return json.loads(r.choices[0].message.content)

# --- driver -------------------------------------------------------------

def run_eval(agent_module: str, eval_path: str, label: str):
    mod = __import__(agent_module)
    rows = [json.loads(l) for l in open(eval_path)]

    project = AIProjectClient(endpoint=PROJECT_ENDPOINT,
                              credential=DefaultAzureCredential())
    judge_client = project.inference.get_azure_openai_client(api_version="2024-10-21")

    schema_scores, judge_scores, latencies = [], [], []
    usage_by_model = {}

    for row in rows:
        resp = mod.run(row["input"])
        schema_scores.append(schema_eval(row, resp)["score"])
        judge_scores.append(judge_eval(row, resp, judge_client)["score"] / 5.0)
        latencies.append(resp["latency_s"])
        for m, (tin, tout) in resp.get("usage_by_model", {}).items():
            cur = usage_by_model.get(m, (0, 0))
            usage_by_model[m] = (cur[0] + tin, cur[1] + tout)

    quality = 0.5 * mean(schema_scores) + 0.5 * mean(judge_scores)
    cost    = cost_of(usage_by_model) / len(rows)
    latency = sorted(latencies)[len(latencies)//2]    # p50
    print_scorecard(label, quality, cost, latency)
    return {"quality": quality, "cost": cost, "latency": latency,
            "n": len(rows), "label": label}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True,
                    help="python module: baseline_agent | multi_model_agent")
    ap.add_argument("--eval",  default="../sample-data/eval-full.jsonl")
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    run_eval(a.agent, a.eval, a.label)
```

Run the curated quick check first:

```bash
python s05_run_eval.py --agent s02_baseline_agent \
                   --eval ../sample-data/eval-seed.jsonl \
                   --label "v1-curated"
```

Then the full batch on v1:

```bash
python s05_run_eval.py --agent s02_baseline_agent \
                   --eval ../sample-data/eval-full.jsonl \
                   --label "v1-batch"
```

Expected (illustrative): **v1-batch quality ≈ 0.61.**

## 5.4 — Now build the v2 agent (router + per-task models, no fine-tune yet)

Drop in `code/s05_multi_model_agent.py` (we'll fill in fine-tune in Step 6; for v2 the policy step uses `DEPLOY_POLICY_BASE`):

```python
# s05_multi_model_agent.py — v2/v3 router-led agent
import json, time
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from s02_tools_mock import TOOL_SCHEMAS, DISPATCH
from s03_router import route
from s02_config import PROJECT_ENDPOINT, DEPLOY_PLANNER, DEPLOY_MINI_VISION, DEPLOY_POLICY_BASE, DEPLOY_POLICY_FT
USE_FT_POLICY = False   # flip to True after Step 6 deploys the fine-tune

_project = AIProjectClient(endpoint=PROJECT_ENDPOINT,
                           credential=DefaultAzureCredential())
_client  = _project.inference.get_azure_openai_client(api_version="2024-10-21")

def _chat(model, messages, **kw):
    return _client.chat.completions.create(model=model, messages=messages, **kw)

def run(user_message: str, image_url: str | None = None) -> dict:
    t0 = time.time()
    usage = {}
    def _bump(model, r):
        cur = usage.get(model, (0, 0))
        usage[model] = (cur[0] + r.usage.prompt_tokens,
                        cur[1] + r.usage.completion_tokens)

    # 1. Route
    r = _chat(DEPLOY_ROUTER, [
        {"role":"system","content":"Classify intent. JSON only."},
        {"role":"user","content":user_message}],
        temperature=0, response_format={"type":"json_object"})
    _bump(DEPLOY_ROUTER, r)
    intent = json.loads(r.choices[0].message.content)

    # 2. Optional vision pre-step
    vision_facts = None
    if image_url:
        r = _chat(DEPLOY_MINI_VISION, [
            {"role":"system","content":"Extract receipt fields as JSON: merchant, amount, date, category."},
            {"role":"user","content":[
                {"type":"text","text":"Extract."},
                {"type":"image_url","image_url":{"url":image_url}}]}],
            temperature=0, response_format={"type":"json_object"})
        _bump(DEPLOY_MINI_VISION, r)
        vision_facts = json.loads(r.choices[0].message.content)

    # 3. Pre-resolve policy answer (cheap model, optionally fine-tuned)
    policy_model = DEPLOY_POLICY_FT if USE_FT_POLICY else DEPLOY_POLICY_BASE
    pol = _chat(policy_model, [
        {"role":"system","content":"You answer Contoso travel policy questions. Concise."},
        {"role":"user","content":user_message}], temperature=0)
    _bump(policy_model, pol)
    policy_note = pol.choices[0].message.content

    # 4. Planner with tool calls — gets pre-resolved policy + vision facts
    sys = ("You are Contoso Travel planner. Use tools. Respect policy. "
           f"Pre-resolved policy: {policy_note}. "
           f"Receipt facts: {vision_facts}. "
           "Return final JSON: flight, hotel, policy_notes, "
           "total_estimated_cost_usd, booking_status.")
    msgs = [{"role":"system","content":sys},
            {"role":"user","content":user_message}]
    for _ in range(6):
        r = _chat(DEPLOY_PLANNER, msgs, tools=TOOL_SCHEMAS, tool_choice="auto")
        _bump(DEPLOY_PLANNER, r)
        m = r.choices[0].message
        msgs.append(m.model_dump(exclude_none=True))
        if not m.tool_calls: break
        for tc in m.tool_calls:
            args = json.loads(tc.function.arguments)
            out = DISPATCH[tc.function.name](**args)
            msgs.append({"role":"tool","tool_call_id":tc.id,
                         "content": json.dumps(out)})

    return {"answer": m.content, "latency_s": time.time()-t0,
            "usage_by_model": usage,
            "intent": intent, "vision": vision_facts}
```

Run v2:

```bash
python s05_run_eval.py --agent s05_multi_model_agent \
                   --eval ../sample-data/eval-full.jsonl \
                   --label "v2-batch"
```

Expected:
```
=== v2-batch scorecard ===
Quality   ████████░░  0.78
Cost      █████░░░░░  $0.063
Latency   ██████░░░░  9.4 s
```

Two rows of the on-stage scorecard turn green. Policy QA is still the blocker — that's Step 6.

## 5.5 — Check it in the portal

Portal → **Evaluation** → you'll see the run listed under your project. Click into a row to see input, output, evaluator scores, and the full trace.

> **What to point at on stage:** the *failure rows*. Open one of the policy-fail rows and read the model's answer aloud. "Sounds confident. It's wrong. The eval caught it." This is where Yina nods.

---

➡️ **Next:** [Step 6 — Fine-tune `gpt-5.4-mini` for policy](./06-finetune.md)
