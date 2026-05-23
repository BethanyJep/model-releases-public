# s05_run_eval.py — runs an agent module over an eval set and prints the scorecard.
import argparse
import importlib
import json
from statistics import mean
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from s02_config import PROJECT_ENDPOINT, DEPLOY_PLANNER
from s02_scorecard import print_scorecard, cost_of


def schema_eval(row: dict, response: dict) -> dict:
    try:
        obj = json.loads(response.get("answer") or "{}")
    except Exception:
        return {"score": 0.0, "reason": "non-json"}
    missing = [k for k in row.get("expected_keys", []) if k not in obj]
    over_budget = False
    constraints = row.get("expected_constraints", {})
    if "max_total" in constraints:
        if obj.get("total_estimated_cost_usd", 1e9) > constraints["max_total"]:
            over_budget = True
    score = 1.0 if (not missing and not over_budget) else 0.0
    return {"score": score, "missing": missing, "over_budget": over_budget}


JUDGE_SYSTEM = """Score the agent's answer 1-5 for whether it correctly
satisfies the user's request and respects the stated constraints.
Return JSON: {"score": int, "reason": "..."}"""


def judge_eval(row: dict, response: dict, client) -> dict:
    msg = (f"User asked: {row.get('input', '')}\n\n"
           f"Agent answered:\n{response.get('answer', '')}")
    r = client.chat.completions.create(
        model=DEPLOY_PLANNER,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user",   "content": msg},
        ],
    )
    try:
        return json.loads(r.choices[0].message.content)
    except Exception:
        return {"score": 3, "reason": "judge parse error"}


def run_eval(agent_module: str, eval_path: str, label: str) -> dict:
    mod = importlib.import_module(agent_module)
    rows = [json.loads(line) for line in open(eval_path)]

    project = AIProjectClient(
        endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())
    judge_client = project.inference.get_azure_openai_client(api_version="2024-10-21")

    schema_scores, judge_scores, latencies = [], [], []
    usage_by_model: dict[str, tuple[int, int]] = {}

    for row in rows:
        try:
            resp = mod.run(row["input"])
        except Exception as e:
            schema_scores.append(0.0); judge_scores.append(0.0)
            latencies.append(30.0)
            print(f"[error] {row['id']}: {e}")
            continue
        schema_scores.append(schema_eval(row, resp)["score"])
        judge_scores.append(judge_eval(row, resp, judge_client)["score"] / 5.0)
        latencies.append(resp.get("latency_s", 0.0))
        for m, (tin, tout) in resp.get("usage_by_model", {}).items():
            cur = usage_by_model.get(m, (0, 0))
            usage_by_model[m] = (cur[0] + tin, cur[1] + tout)

    quality = 0.5 * mean(schema_scores) + 0.5 * mean(judge_scores)
    cost    = cost_of(usage_by_model) / max(1, len(rows))
    latency = sorted(latencies)[len(latencies) // 2] if latencies else 0.0
    print_scorecard(label, quality, cost, latency)
    return {"quality": quality, "cost": cost, "latency": latency,
            "n": len(rows), "label": label}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True,
                    help="python module name: baseline_agent | multi_model_agent")
    ap.add_argument("--eval",  default="../sample-data/eval-full.jsonl")
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    run_eval(args.agent, args.eval, args.label)
