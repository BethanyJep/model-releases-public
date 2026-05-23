# Step 2 — Baseline agent in VS Code (Foundry SDK)

**Goal:** move the v1 baseline out of the playground and into Python code, with mocked tools so the trip *actually completes*. Measure v1 properly.

**Surface:** VS Code + `azure-ai-projects` / `azure-ai-inference` SDK.

**Time:** 60 min.

**Scorecard at end of step:**
```
Quality   ██░░░░░░░░  0.61   (measured on 20 curated rows)
Cost      ██████████  $0.108
Latency   ██████████  12.3 s
```

Quality finally gets a number. It's not a good number. That's the win — we can now improve it on purpose.

---

## 2.1 — The mocked tools

We're never calling real airline APIs on stage. Drop in `code/s02_tools_mock.py`:

```python
# s02_tools_mock.py — canned tool responses for the demo
from datetime import datetime, timedelta
import random, json

def search_flights(origin: str, dest: str, depart_date: str) -> dict:
    return {
        "results": [
            {"carrier": "LH", "number": "LH457", "depart": f"{depart_date}T20:30",
             "arrive_local": "next-day 15:25", "price_usd": 1180, "stops": 1},
            {"carrier": "UA", "number": "UA962", "depart": f"{depart_date}T17:50",
             "arrive_local": "next-day 14:10", "price_usd": 1340, "stops": 1},
        ]
    }

def search_hotels(city: str, area: str, checkin: str, checkout: str) -> dict:
    return {
        "results": [
            {"name": "Park Inn Alexanderplatz", "area": area, "nightly_usd": 165,
             "total_usd": 495, "rating": 4.1},
            {"name": "H4 Hotel Berlin Alexanderplatz", "area": area,
             "nightly_usd": 198, "total_usd": 594, "rating": 4.4},
        ]
    }

def check_policy(question: str) -> dict:
    # In step 6 we'll replace this with the fine-tuned policy model.
    # For now it returns a placeholder that the planner has to interpret.
    return {"answer": "See travel policy section 4.2 and 7.1.",
            "policy_doc": "sample-data/travel-policy.md"}

def submit_booking(payload: dict) -> dict:
    return {"booking_id": f"CT-{random.randint(10000,99999)}",
            "status": "confirmed-mock"}

TOOL_SCHEMAS = [
  {"type": "function", "function": {
    "name": "search_flights",
    "description": "Search business-policy-compliant flights.",
    "parameters": {"type": "object", "properties": {
        "origin": {"type": "string"}, "dest": {"type": "string"},
        "depart_date": {"type": "string", "description": "YYYY-MM-DD"}},
      "required": ["origin", "dest", "depart_date"]}}},
  {"type": "function", "function": {
    "name": "search_hotels", "description": "Search hotels.",
    "parameters": {"type": "object", "properties": {
        "city": {"type": "string"}, "area": {"type": "string"},
        "checkin": {"type": "string"}, "checkout": {"type": "string"}},
      "required": ["city", "checkin", "checkout"]}}},
  {"type": "function", "function": {
    "name": "check_policy",
    "description": "Ask a question against Contoso travel policy.",
    "parameters": {"type": "object", "properties": {
        "question": {"type": "string"}}, "required": ["question"]}}},
  {"type": "function", "function": {
    "name": "submit_booking",
    "description": "Submit a booking. Returns a confirmation id.",
    "parameters": {"type": "object",
                   "properties": {"payload": {"type": "object"}},
                   "required": ["payload"]}}},
]

DISPATCH = {"search_flights": search_flights, "search_hotels": search_hotels,
            "check_policy": check_policy, "submit_booking": submit_booking}
```

## 2.2 — Config

`code/s02_config.py`:

```python
# s02_config.py — single source of truth for deployments and pricing
import os
from dotenv import load_dotenv
load_dotenv()

PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
REGION = "eastus2"

# Deployment names (what we created in the portal / via Skill).
DEPLOY_PLANNER       = "planner-gpt54"          # gpt-5.4
DEPLOY_ROUTER        = "router-nano"            # gpt-5.4-nano  (Step 3)
DEPLOY_MINI_VISION   = "mini-vision"            # gpt-5.4-mini  (Step 3)
DEPLOY_POLICY_BASE   = "policy-mini-base"       # gpt-5.4-mini  (Step 5)
DEPLOY_POLICY_FT     = "policy-mini-ft"         # fine-tuned    (Step 6)

# Per-1K token prices — fill from the catalog you verified in Step 0.
# These illustrative numbers match the PLAN.md scorecard story.
PRICE = {
    DEPLOY_PLANNER:     {"in": 0.0050, "out": 0.0150},
    DEPLOY_ROUTER:      {"in": 0.0002, "out": 0.0006},
    DEPLOY_MINI_VISION: {"in": 0.0008, "out": 0.0024},
    DEPLOY_POLICY_BASE: {"in": 0.0008, "out": 0.0024},
    DEPLOY_POLICY_FT:   {"in": 0.0010, "out": 0.0030},
}
```

## 2.3 — The v1 agent: `gpt-5.4` doing every job

`code/s02_baseline_agent.py`:

```python
# s02_baseline_agent.py — v1: one frontier model, all tasks
import json, time
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from s02_tools_mock import TOOL_SCHEMAS, DISPATCH
from s02_config import PROJECT_ENDPOINT, DEPLOY_PLANNER
SYSTEM = """You are Contoso Travel. Use tools to plan and book travel.
Always check policy before booking. Return a final JSON itinerary with keys:
flight, hotel, policy_notes, total_estimated_cost_usd, booking_status."""

def run(user_message: str) -> dict:
    project = AIProjectClient(endpoint=PROJECT_ENDPOINT,
                              credential=DefaultAzureCredential())
    client = project.inference.get_azure_openai_client(api_version="2024-10-21")

    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user",   "content": user_message}]
    t0 = time.time()
    total_in = total_out = 0

    for _ in range(8):  # tool-call loop, capped
        resp = client.chat.completions.create(
            model=DEPLOY_PLANNER, messages=messages,
            tools=TOOL_SCHEMAS, tool_choice="auto")
        total_in  += resp.usage.prompt_tokens
        total_out += resp.usage.completion_tokens
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            break
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            out = DISPATCH[tc.function.name](**args)
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": json.dumps(out)})

    return {"answer": msg.content, "latency_s": time.time() - t0,
            "tokens_in": total_in, "tokens_out": total_out,
            "model_calls": {"planner": "all"}}

if __name__ == "__main__":
    with open("../sample-data/carmen-trace.json") as f:
        carmen = json.load(f)["user_message"]
    out = run(carmen)
    print(json.dumps(out, indent=2))
```

Run it:

```bash
cd code
python s02_baseline_agent.py
```

You should see a complete itinerary, with `latency_s` ≈ 11–13s and ~3K–5K total tokens.

## 2.4 — The scorecard module

`code/s02_scorecard.py`:

```python
# s02_scorecard.py — pretty-prints the three progress bars
from s02_config import PRICE
QUALITY_TARGET = 0.92
COST_TARGET    = 0.03
LATENCY_TARGET = 8.0

def bar(value, max_value, width=10, invert=False):
    # invert=True for cost/latency: lower is better, so fill from the right.
    frac = min(1.0, value / max_value)
    filled = int(round(frac * width))
    if invert:
        return "█" * filled + "░" * (width - filled)
    return "█" * filled + "░" * (width - filled)

def cost_of(usage_by_model):
    total = 0.0
    for model, (tin, tout) in usage_by_model.items():
        p = PRICE[model]
        total += tin/1000 * p["in"] + tout/1000 * p["out"]
    return total

def print_scorecard(version, quality, cost, latency):
    q_pass = "✅" if quality >= QUALITY_TARGET else "  "
    c_pass = "✅" if cost    <= COST_TARGET    else "  "
    l_pass = "✅" if latency <= LATENCY_TARGET else "  "
    print(f"\n=== {version} scorecard ===")
    print(f"Quality   {bar(quality, 1.0)}  {quality:.2f}   {q_pass}")
    print(f"Cost      {bar(cost,    0.15, invert=True)}  ${cost:.3f}  {c_pass}")
    print(f"Latency   {bar(latency, 15.0, invert=True)}  {latency:.1f}s  {l_pass}")
```

## 2.5 — Measure v1 quality (20-row curated eval)

We can't move quality if we can't measure it. The seed eval is `sample-data/eval-seed.jsonl` (20 hand-written rows). The driver is in Step 5, but we can preview the result:

```
v1 (gpt-5.4-only):
Quality   ██░░░░░░░░  0.61
Cost      ██████████  $0.108
Latency   ██████████  12.3 s
```

Why 0.61?
- The planner happily books flights *over budget* on 3 rows.
- It gives wrong policy answers on 4 rows (no grounding in the policy doc).
- It fails on the receipt row because the playground baseline has no vision route.

Every one of those failures has a *model-shaped* fix coming. That's Steps 3–7.

## 2.6 — What we did, what's next

- ✅ Moved from a portal playground prompt to a runnable agent in code.
- ✅ Mocked the tool layer so the demo is reproducible.
- ✅ Got our first quality number — 0.61.
- ⏭️ Step 3 picks the right model **per task** instead of using `gpt-5.4` for everything.

---

➡️ **Next:** [Step 3 — Model selection with the Foundry Skill](./03-model-selection.md)
