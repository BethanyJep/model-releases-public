# =============================================================================
# s09_run_router_eval.py — Run the model-router agent over eval-full.jsonl
# =============================================================================
# Thin wrapper around s05_run_eval.run_eval — keeps the comparison apples-to-
# apples with v1/v2/v3 (same harness, same evaluators, same dataset).
# =============================================================================
from s05_run_eval import run_eval

if __name__ == "__main__":
    run_eval(
        agent_module="s09_router_agent",
        eval_path="../sample-data/eval-full.jsonl",
        label="model-router",
    )
