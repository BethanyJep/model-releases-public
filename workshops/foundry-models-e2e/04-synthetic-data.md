# Step 4 — Synthetic dataset generation (SDK)

> **Foundry lifecycle:** **02 · Evaluate** (data) — grow a domain-grounded eval set so we can test on *our* data.

## Goal

Grow our 20-row curated eval into a ~200-row dataset we can run meaningful batch evals against — *without* hand-writing 200 rows.

**Surface:** Foundry SDK + `gpt-4.1` as a *data generator* (one of the legitimate uses of a frontier model in this stack).

**Time:** 45 min.

**Scorecard at end of step:**
```
Quality   ██░░░░░░░░  0.61   (same — generation doesn't change quality)
Cost      ██████░░░░  $0.063
Latency   █████████░  9.4 s
```

## Prereqs

- Step 3 complete: per-task model mapping decided, router wired.
- `sample-data/eval-seed.jsonl` and `sample-data/synthetic-prompts.jsonl` accessible from your repo.

## Steps

The numbered subsections below (4.1 – 4.5) are the actions to perform in order.

Bars unchanged. What changes is that **Step 5 can now produce a number we actually trust**, because the eval is no longer 20 hand-picked easy rows.

---

## 4.1 — Why synthesize?

20 rows is enough to know your prompt is broken. It is **not** enough to:
- Catch class-imbalance failures (e.g. only 1/20 rows tests German translation).
- Detect regressions when you change a model.
- Stress test policy edge cases.

You want **~200 rows** with deliberate coverage across:
- Intent (plan / policy / receipt) — balanced
- Budget edge cases (just under, just over)
- Geography (US ↔ EU, US ↔ APAC)
- Receipt categories (parking, taxi, meals, hotel-incidentals)
- Language (EN, DE, ES)
- Policy traps ("can I fly business on a 4-hour leg?")

## 4.2 — The seed rows (20 curated)

`sample-data/eval-seed.jsonl` — already authored by hand. Each row looks like:

```json
{"id":"seed-001","intent":"plan_trip","input":"Book SAN→BER Tuesday morning under $2500","expected_keys":["flight","hotel","total_estimated_cost_usd"],"expected_constraints":{"max_total":2500,"must_arrive_before":"Tue 12:00 BER"}}
```

We commit these. They are our **ground truth** — humans wrote and reviewed them. Synthetic rows expand coverage; they don't replace the seed.

## 4.3 — The generator

`code/s04_generate_synthetic.py`:

```python
# s04_generate_synthetic.py — grow the eval from 20 seed rows to ~200
import json, hashlib
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from s02_config import PROJECT_ENDPOINT, DEPLOY_PLANNER
GEN_INSTRUCTIONS = """You are an evaluation dataset author for an internal
travel agent. Given seed rows, produce NEW rows that:
  - keep the same JSON schema as the seed
  - vary along ONE axis at a time (intent, geography, budget, language,
    receipt category, policy trap)
  - include 2-3 'adversarial' rows that try to bypass policy
  - never duplicate a seed verbatim

Return a JSON array of rows. Each row must include:
  id, intent, input, expected_keys, expected_constraints, axis_varied."""

def generate(seed_path: str, n_per_axis: int = 25, out_path: str = None):
    project = AIProjectClient(endpoint=PROJECT_ENDPOINT,
                              credential=DefaultAzureCredential())
    client = project.get_openai_client()

    seeds = [json.loads(l) for l in open(seed_path)]
    seen_ids = {s["id"] for s in seeds}
    all_rows = list(seeds)

    AXES = ["intent_balance", "geography", "budget_edge",
            "language", "receipt_category", "policy_trap"]

    for axis in AXES:
        prompt = (f"Seed rows:\n{json.dumps(seeds, indent=2)}\n\n"
                  f"Generate {n_per_axis} new rows varying axis='{axis}'.")
        resp = client.responses.create(
            model=DEPLOY_PLANNER, temperature=0.8,
            instructions=GEN_INSTRUCTIONS,
            input=prompt,
            text={"format": {"type": "json_object"}},
        )
        wrapped = json.loads(resp.output_text)
        new_rows = wrapped.get("rows", wrapped if isinstance(wrapped, list) else [])
        for r in new_rows:
            # dedupe + namespace synthetic ids
            r["id"] = "syn-" + hashlib.sha1(r["input"].encode()).hexdigest()[:8]
            if r["id"] in seen_ids:  continue
            seen_ids.add(r["id"]);   all_rows.append(r)

    if out_path:
        with open(out_path, "w") as f:
            for r in all_rows: f.write(json.dumps(r) + "\n")
    print(f"Wrote {len(all_rows)} rows ({len(all_rows)-20} synthetic).")
    return all_rows

if __name__ == "__main__":
    generate("../sample-data/eval-seed.jsonl",
             out_path="../sample-data/eval-full.jsonl")
```

Run:

```bash
python s04_generate_synthetic.py
# → Wrote 198 rows (178 synthetic).
```

The script makes 6 sequential API calls (one per axis) with no progress output — it will appear to hang for 2–3 minutes. **While you wait**, do this:

1. Open the [Foundry portal](https://ai.azure.com) → your project → **Models + endpoints** → click `planner-gpt41`.
2. Select the **Monitor** tab.
3. Watch **Requests** and **Token usage** tick up — one call per axis, 25 rows each.

This is the portal's real-time view of what the script is costing you. By the time you've explored the Monitor tab, the script will likely be done.

## 4.4 — Hand-review the first 30 synthetic rows

**Do not skip this.** Open `eval-full.jsonl`, find the rows whose `id` starts with `syn-`, read the first 30:

- Mark any that are duplicates of seed rows in spirit (cull them).
- Mark any that have impossible constraints (e.g. "arrive before depart"). Cull or fix.
- Mark any that test something *already* well-tested. Replace with a missing axis.

Keep ~150-200 rows. **A 150-row clean eval beats a 500-row noisy one.**

> **The honest aside for the session** (Naomi has this line in the transcript): *"Synthetic data is a tool, not a magic wand. Every synthetic row I add, I scan. Every adversarial row, I read twice."*

## 4.5 — Versioning

```bash
mkdir -p ../.foundry/datasets
cp ../sample-data/eval-full.jsonl ../.foundry/datasets/eval-v1.jsonl
```

When you change generation logic later (Step 8 shows how Foundry tracks dataset *versions* in the portal), bump to `eval-v2.jsonl`. Eval results without a dataset version are uninterpretable.

> **Foundry Skill tip:** ask the `microsoft-foundry` skill's **eval-datasets** sub-skill (`microsoft-foundry/foundry-agent/eval-datasets/`) to register the dataset against your project so it shows up in the portal's **Datasets** tab.

## Verify

- `python s04_generate_synthetic.py` produces ~200 rows in `sample-data/eval-full.jsonl`.
- A hand-review of the first 30 synthetic rows shows fewer than 10% obvious quality issues.
- The dataset is versioned as `eval-v1.jsonl` under `.foundry/datasets/`.

## Troubleshoot

| Symptom | Likely cause | Fix |
|---|---|---|
| Generator output is repetitive | Temperature too low, or seed prompts too narrow. | Raise temperature to 0.8; diversify seed prompts. |
| Many rows fail JSON parsing | Frontier model added prose around JSON. | Add a strict "respond with JSON only" system instruction and a JSON-mode flag if available. |
| Dataset doesn't show in portal | Skill didn't register or wrong project endpoint. | Verify project endpoint in env; re-run the registration command. |

## Next

➡️ [Step 5 — Evaluations: curated, batch, online](./05-evaluations.md)
