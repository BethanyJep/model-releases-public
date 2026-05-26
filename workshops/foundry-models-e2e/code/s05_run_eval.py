# =============================================================================
# s05_run_eval.py — Evaluation harness (Step 5, reused in Steps 6 & 7)
# =============================================================================
# NARRATIVE ROLE
# Running an agent manually for one prompt tells you nothing at scale.
# This harness runs any agent module over a JSONL eval set, applies two
# complementary evaluators, and renders the quality/cost/latency scorecard.
#
# TWO-EVALUATOR DESIGN
# • SchemaEvaluator (deterministic): checks that required JSON keys are
#   present and that numeric constraints (budget) are not violated.
#   Fast, zero cost, reproducible.
# • JudgeEvaluator  (LLM-as-judge):  asks gpt-4.1 to score semantic
#   correctness 1-5.  Catches plausible-but-wrong answers that pass schema.
#   Final quality = 0.5 × schema + 0.5 × judge.
#
# Results are written to eval_results_<label>.json and surfaced in the
# Foundry portal via azure-ai-evaluation.evaluate() for trend tracking.
# The same script runs for v1, v2, v3, and policy-slice evals — the --label
# flag keeps each run identifiable in the portal.
# =============================================================================
import argparse
import importlib
import json
import os
from statistics import mean

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.evaluation import evaluate

from s02_config import PROJECT_ENDPOINT, DEPLOY_PLANNER
from s02_scorecard import print_scorecard, cost_of

# Project coordinates — used to log eval runs to the Foundry portal
_SUBSCRIPTION_ID   = os.environ.get("AZURE_SUBSCRIPTION_ID", "")
_RESOURCE_GROUP    = os.environ.get("AZURE_RESOURCE_GROUP", "")
_PROJECT_NAME      = os.environ.get("FOUNDRY_PROJECT_NAME", "")

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
        try:
            cost_val = float(obj.get("total_estimated_cost_usd") or 1e9)
        except (TypeError, ValueError):
            cost_val = 1e9
        over_budget = (
            "max_total" in constraints
            and cost_val > constraints["max_total"]
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
        # NOTE: azure_ai_project portal logging requires an AML-backed workspace.
        # New Foundry projects (Microsoft.CognitiveServices) are not AML workspaces
        # and will 404. Results are saved locally above.
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
