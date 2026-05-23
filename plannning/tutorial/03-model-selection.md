# Step 3 — Model selection with the Foundry Skill (AI-assisted)

**Goal:** stop assuming `gpt-5.4` is the right answer for every task. Pick a model per task type, using the Foundry Skill (AI-assisted catalog query) to make a defensible choice in minutes.

**Surface:** AI-assisted (Copilot CLI + `microsoft-foundry` skill) → SDK.

**Time:** 45 min.

**Scorecard at end of step:**
```
Quality   ██░░░░░░░░  0.61    (unchanged — we'll measure v2 in Step 5)
Cost      ██████░░░░  $0.063  ⬇️ from $0.11
Latency   █████████░  9.4 s   ⬇️ from 12.3 s
```

The cost and latency bars shrink. Quality is **unchanged on paper** until Step 5 confirms — we're being honest about cause and effect.

---

## 3.1 — Decompose Carmen's trip into tasks

Before picking models, name the jobs:

| # | Task | What it actually requires from a model |
|---|---|---|
| 1 | **Route** the incoming request to the right path | Fast classifier; cheap; no creativity |
| 2 | **Read the parking receipt** image and extract fields | Vision + structured output |
| 3 | **Answer policy questions** ("can I expense parking at SAN?") | Knowledge of *Contoso's* policy specifically — base models don't have this |
| 4 | **Plan the multi-step itinerary** and orchestrate tools | Strong reasoning, longer context |
| 5 | **Translate** the German hotel confirmation email | Multilingual, simple |

Five jobs, five *different* shapes. There is **no single model** that's best for all of them.

## 3.2 — Ask the Foundry Skill to map jobs → models

In Copilot CLI (or any client wired to the `microsoft-foundry` skill / Foundry MCP), prompt:

```
I need to pick Azure Direct models from East US 2 for these tasks:

  1. fast intent classification (≤200 tokens in, ≤30 out, p50 ≤300ms)
  2. vision: extract {merchant, amount, date, category} from a receipt image
  3. domain QA grounded in a 2-page policy doc (will fine-tune later)
  4. multi-step planner with tool calls (≤4K tokens, p50 ≤6s)
  5. EN↔DE translation, short emails

For each task recommend a model (from gpt-5.4, gpt-5.4-mini, gpt-5.4-nano)
and explain in one sentence. Then propose deployment names and TPM sizing
for a demo at ~50 requests/minute.
```

The skill will respond with a table like:

| Task | Recommended | Why | Deployment | TPM |
|---|---|---|---|---|
| Route | `gpt-5.4-nano` | Cheapest, sub-300ms, plenty good for 3-class routing | `router-nano` | 10K |
| Receipt vision | `gpt-5.4-mini` (vision) | Mini supports vision; frontier overkill for OCR-ish task | `mini-vision` | 20K |
| Policy QA | `gpt-5.4-mini` (will fine-tune) | Cheap + fine-tunable; fine-tune closes the quality gap | `policy-mini-base` | 20K |
| Planner | `gpt-5.4` | Multi-step reasoning + tool orchestration is where frontier earns its keep | `planner-gpt54` | 30K |
| Translate | `gpt-5.4-mini` | Reuse `mini-vision` deployment (same base model) | *(reuse)* | — |

> **This is the whole point of the session.** *Decomposing the workload exposes that 4 of 5 jobs don't need a frontier model.* The cost wins in §3.4 come from this single insight.

## 3.3 — Deploy the new models (Skill OR portal)

**With the Foundry Skill:**

```
Deploy these models in project contoso-travel-demo, region eastus2:

  - name=router-nano, model=gpt-5.4-nano, sku=Standard, tpm=10000
  - name=mini-vision, model=gpt-5.4-mini, sku=Standard, tpm=20000
  - name=policy-mini-base, model=gpt-5.4-mini, sku=Standard, tpm=20000

Verify each shows status=Succeeded.
```

The skill runs `models/deploy-model` under the hood. (See `microsoft-foundry/models/deploy-model/SKILL.md` if you want the raw MCP flow.)

**Or in the portal:** Project → **Models + endpoints** → **+ Deploy model**, repeat 3 times with the names above.

Either way, when you're done, the **Models + endpoints** page should list four deployments: `planner-gpt54`, `router-nano`, `mini-vision`, `policy-mini-base`. (The fine-tuned one comes in Step 6.)

## 3.4 — Wire the router

`code/s03_router.py`:

```python
# s03_router.py — a tiny, fast classifier that names the path
import json
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from s02_config import PROJECT_ENDPOINT, DEPLOY_ROUTER
_project = AIProjectClient(endpoint=PROJECT_ENDPOINT,
                           credential=DefaultAzureCredential())
_client = _project.inference.get_azure_openai_client(api_version="2024-10-21")

ROUTER_SYSTEM = """Classify the user's travel request into one of:
  plan_trip         - they want to book or plan travel
  policy_question   - they're asking what's allowed / can-they-expense
  receipt_expense   - there's a receipt image to process

Return JSON: {"intent": "...", "needs_vision": true|false,
              "needs_translation": true|false}.
Return JSON only. No prose."""

def route(user_message: str, has_image: bool = False) -> dict:
    resp = _client.chat.completions.create(
        model=DEPLOY_ROUTER, temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": ROUTER_SYSTEM},
                  {"role": "user", "content":
                   user_message + (f"\n[has_image={has_image}]")}])
    return json.loads(resp.choices[0].message.content)
```

Try it:

```bash
python -c "from s03_router import route; \
  print(route('book me Berlin Tuesday morning, here is a receipt', True))"
# → {'intent': 'plan_trip', 'needs_vision': True, 'needs_translation': False}
```

p50 on a warm deployment: **~180ms.** That's the latency budget freed up for the planner to do its job.

## 3.5 — Where the savings come from

For Carmen's full trip, the v1 path was: `gpt-5.4 × 5 turns`. The v2 path (after we wire it in Step 7) is:

| Turn | Job | Model | Tokens (illustrative) | $ |
|---|---|---|---|---|
| 1 | Route | nano | 220 in / 30 out | $0.00006 |
| 2 | Vision: receipt | mini | 1200 in / 90 out | $0.00118 |
| 3 | Policy: "expense parking?" | mini-base | 800 in / 60 out | $0.00078 |
| 4 | Plan + tools | gpt-5.4 | 2800 in / 280 out | $0.0182 |
| 5 | Translate confirm email | mini *(reuse)* | 600 in / 220 out | $0.00101 |
| | | | **Total** | **~$0.022** |

Even before fine-tuning, **just by picking the right model per job**, we go from ~$0.11 → ~$0.022 per task — a ~5× cost reduction. (The scorecard headline says $0.063 because we're being conservative about including overhead and tool round-trips at this stage; the final v3 number in Step 7 is $0.028.)

## 3.6 — A note about Foundry Skills vs the portal vs the SDK

You just used **three surfaces**:

- **Foundry Skill** to *discover* + *deploy* models (AI-assisted).
- **Portal** to *visually verify* the deployments showed up.
- **SDK** to *use* the deployments from code.

That's the right mental model. Skills get you to a working configuration fast. The portal is for governance and review. The SDK is where production lives.

---

➡️ **Next:** [Step 4 — Synthetic dataset generation](./04-synthetic-data.md)
