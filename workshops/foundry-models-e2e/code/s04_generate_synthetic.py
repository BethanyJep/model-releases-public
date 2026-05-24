# s04_generate_synthetic.py — grow eval-seed.jsonl into eval-full.jsonl (~200 rows).
# Uses the OpenAI Responses API with JSON-mode output.
import json
import hashlib
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from s02_config import PROJECT_ENDPOINT, DEPLOY_PLANNER

GEN_INSTRUCTIONS = """You are an evaluation dataset author for an internal
travel agent. Given seed rows, produce NEW rows that:
  - keep the same JSON schema as the seed
  - vary along ONE axis at a time
  - include 2-3 adversarial rows that try to bypass policy
  - never duplicate a seed verbatim

Return JSON: {"rows": [ ... ]}. Each row must include:
  id, intent, input, expected_keys, expected_constraints, axis_varied."""

AXES = [
    "intent_balance", "geography", "budget_edge",
    "language", "receipt_category", "policy_trap",
]


def generate(seed_path: str, out_path: str, n_per_axis: int = 25) -> list[dict]:
    project = AIProjectClient(
        endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())
    client = project.get_openai_client()

    seeds = [json.loads(line) for line in open(seed_path)]
    seen_ids = {s["id"] for s in seeds}
    all_rows = list(seeds)

    for axis in AXES:
        prompt = (
            f"Seed rows:\n{json.dumps(seeds, indent=2)}\n\n"
            f"Generate {n_per_axis} new rows varying axis='{axis}'."
            f"\nReturn JSON only."
        )
        resp = client.responses.create(
            model=DEPLOY_PLANNER,
            temperature=0.8,
            instructions=GEN_INSTRUCTIONS,
            input=prompt,
            text={"format": {"type": "json_object"}},
        )
        wrapped = json.loads(resp.output_text)
        new_rows = wrapped.get("rows", [])
        for r in new_rows:
            key = r.get("input", "")
            r["id"] = "syn-" + hashlib.sha1(key.encode()).hexdigest()[:8]
            if r["id"] in seen_ids:
                continue
            r.setdefault("axis_varied", axis)
            seen_ids.add(r["id"])
            all_rows.append(r)

    with open(out_path, "w") as f:
        for r in all_rows:
            f.write(json.dumps(r) + "\n")
    print(f"Wrote {len(all_rows)} rows "
          f"({len(all_rows) - len(seeds)} synthetic) to {out_path}.")
    return all_rows


if __name__ == "__main__":
    generate("../sample-data/eval-seed.jsonl",
             "../sample-data/eval-full.jsonl")
