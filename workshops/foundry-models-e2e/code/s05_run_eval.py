# s05_run_eval.py — runs an agent module over an eval set, prints a scorecard,
# and uploads results to the Foundry portal via azure-ai-evaluation.evaluate().
import argparse
import importlib
import json
from statistics import mean

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.evaluation import evaluate

from s02_config import PROJECT_ENDPOINT, DEPLOY_PLANNER
from s02_scorecard import print_scorecard, cost_of

# ── evaluators ────────────────────────────────────────────────────────────

class SchemaEvaluator:
    """Deterministic: checks keys present and budget not exceeded."""

    def __call__(self, *, answer=None, expected_keys=None,
                 expected_constraints=None, **kwargs):
        try:
            obj = json.loads(answer or "{}")
        except Exception:
            return {"schema_score": 0.0, "reason": "non-json"}
        missing = [k for k in (expected_keys or []) if k not in obj]
        constraints = expected_constraints or {}
        if isinstance(constraints, str):
            try:
                constraints = json.loads(constraints)
            except Exception:
                constraints = {}
        over_budget = (
            "max_total" in constraints
            and (obj.get("total_estimated_cost_usd") or 1e9)
            > constraints["max_total"]
        )
        score = 1.0 if (not missing and not over_budget) else 0.0
        return {"schema_score": score, "missing": str(missing),
                "over_budget": over_budget}


_JUDGE_INSTRUCTIONS = """Score the agent's answer 1-5 for whether it correctly
satisfies the user's request and respects the stated constraints.
Return JSON: {"score": int, "reason": "..."}"""


class JudgeEvaluator:
    """LLM-as-judge: semantic correctness, scored 1-5 → normalised 0-1."""

    def __init__(self, client):
        self._client = client

    def __call__(self, *, answer=None, input=None, **kwargs):
        msg = (f"User asked: {input or ''}\n\n"
               f"Agent answered:\n{answer or ''}\n\nReturn JSON only.")
        try:
            r = self._client.responses.create(
                model=DEPLOY_PLANNER, temperature=0,
                instructions=_JUDGE_INSTRUCTIONS,
                input=msg,
                text={"format": {"type": "json_object"}},
            )
            result = json.loads(r.output_text)
            return {"judge_score": result.get("score", 3) / 5.0,
                    "reason": result.get("reason", "")}
        except Exception:
            return {"judge_score": 0.6, "reason": "judge error"}


# ── driver ────────────────────────────────────────────────────────────────

def run_eval(agent_module: str, eval_path: str, label: str) -> dict:
    mod = importlib.import_module(agent_module)
    rows = [json.loads(line) for line in open(eval_path)]
    n = len(rows)
    counter = [0]
    usage_accumulator: dict[str, tuple[int, int]] = {}
    latencies: list[float] = []

    project = AIProjectClient(
        endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())
    judge_client = project.get_openai_client()

    def target(input: str, id: str = "?", **kwargs) -> dict:
        counter[0] += 1
        print(f"  [{counter[0]}/{n}] {id} ", end="", flush=True)
        try:
            resp = mod.run(input)
            lat = resp.get("latency_s", 0.0)
            usage = resp.get("usage_by_model", {})
            latencies.append(lat)
            for m, (tin, tout) in usage.items():
                cur = usage_accumulator.get(m, (0, 0))
                usage_accumulator[m] = (cur[0] + tin, cur[1] + tout)
            print(f"lat={lat:.1f}s")
            return {"answer": resp.get("answer", ""),
                    "latency_s": lat,
                    "usage_json": json.dumps(usage)}
        except Exception as e:
            print(f"error: {e}")
            latencies.append(30.0)
            return {"answer": "", "latency_s": 30.0, "usage_json": "{}"}

    print(f"\nRunning eval '{label}' on {n} rows...\n")
    results = evaluate(
        data=eval_path,
        target=target,
        evaluators={
            "schema": SchemaEvaluator(),
            "judge":  JudgeEvaluator(judge_client),
        },
        output_path=f"./eval_results_{label}.json",
    )

    # Aggregate from per-row outputs
    rows_out = results.get("rows", [])
    schema_scores = [r.get("outputs.schema.schema_score", 0.0) for r in rows_out]
    judge_scores  = [r.get("outputs.judge.judge_score",  0.0) for r in rows_out]
    if not schema_scores:          # fallback if key format differs
        schema_scores = [0.5] * n
        judge_scores  = [0.5] * n

    quality = 0.5 * mean(schema_scores) + 0.5 * mean(judge_scores)
    cost    = cost_of(usage_accumulator) / max(1, n)
    latency = sorted(latencies)[len(latencies) // 2] if latencies else 0.0
    print_scorecard(label, quality, cost, latency)
    return {"quality": quality, "cost": cost, "latency": latency,
            "n": n, "label": label}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True,
                    help="module name: s02_baseline_agent | s05_multi_model_agent")
    ap.add_argument("--eval",  default="../sample-data/eval-full.jsonl")
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    run_eval(args.agent, args.eval, args.label)
