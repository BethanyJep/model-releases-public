# =============================================================================
# s02_config.py — Workshop shared configuration (Step 2 onwards)
# =============================================================================
# NARRATIVE ROLE
# This file is the single source of truth for every deployment name and
# per-token price used across the entire workshop.  It is imported by every
# subsequent script so that renaming a deployment or updating a price only
# ever requires one edit.
#
# DESIGN DECISION — "name deployments by job, not by model"
# Each constant below describes the *task* the deployment handles
# (planner, router, vision, policy) rather than the underlying model.
# This means Step 6 (fine-tune swap) and Step 7 (v3 architecture) can
# change which model is behind a name without touching any agent code.
# =============================================================================
import os
import sys
from dotenv import load_dotenv

# Venv guard \u2014 imported by every workshop script, so this fail-fast check
# fires on any entrypoint invoked outside the workshop venv. Mixing system
# Python with pinned SDK versions (azure-ai-evaluation, openai) silently
# produces unreliable eval numbers because evaluate() result shape varies
# across releases. Detection works whether the venv is "activated" (sets
# VIRTUAL_ENV) or its interpreter is invoked directly (sys.prefix differs
# from sys.base_prefix). To activate from code/:
#     source ../.venv/bin/activate
_in_venv = (sys.prefix != sys.base_prefix) or bool(os.environ.get("VIRTUAL_ENV"))
if not _in_venv:
    sys.exit(
        "\nERROR: workshop venv not active.\n"
        "Run:  source ../.venv/bin/activate   (from code/)\n"
        "  or  source workshops/foundry-models-e2e/.venv/bin/activate  (from repo root)\n"
        "See RERUN.md \u00a71 \u2014 pre-flight checklist.\n"
    )

load_dotenv()  # reads .env written by s00_setup.sh

PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]  # Foundry project URL
REGION = "swedencentral"  # Azure region — must match where FT is available

# Deployment names — each maps to a specific Azure OpenAI deployment.
DEPLOY_PLANNER       = "planner-gpt41"       # gpt-4.1: orchestrator + tool caller
DEPLOY_ROUTER        = "router-nano"          # gpt-4.1-nano: intent classifier (~50ms)
DEPLOY_MINI_VISION   = "mini-vision"          # gpt-4.1-mini: receipt OCR
DEPLOY_POLICY_BASE   = "policy-mini-base"     # gpt-4.1-mini: policy QA (no FT)
DEPLOY_POLICY_FT     = os.environ.get(         # gpt-4.1-mini: policy QA (fine-tuned, Step 6)
    "FOUNDRY_DEPLOY_POLICY_FT", "policy-mini-ft"
)
DEPLOY_AUTO_ROUTER   = "auto-router"           # model-router: managed multi-model router

# Per-1K-token prices (illustrative — verify against your catalog).
PRICE = {
    DEPLOY_PLANNER:     {"in": 0.0050, "out": 0.0150},
    DEPLOY_ROUTER:      {"in": 0.0002, "out": 0.0006},
    DEPLOY_MINI_VISION: {"in": 0.0008, "out": 0.0024},
    DEPLOY_POLICY_BASE: {"in": 0.0008, "out": 0.0024},
    DEPLOY_POLICY_FT:   {"in": 0.0010, "out": 0.0030},
    # model-router bills at the chosen sub-model's rate. As a workshop
    # approximation we credit the *deployment* at a blended mini-tier
    # rate; for per-sub-model accuracy use the `model` field returned
    # in each response (logged by s09_router_agent.py).
    DEPLOY_AUTO_ROUTER: {"in": 0.0010, "out": 0.0030},
}
