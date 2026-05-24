# s02_config.py — single source of truth for deployments and pricing.
# Update the per-model prices from the values you verified in Step 0.
import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
REGION = "swedencentral"

DEPLOY_PLANNER       = "planner-gpt41"
DEPLOY_ROUTER        = "router-nano"
DEPLOY_MINI_VISION   = "mini-vision"
DEPLOY_POLICY_BASE   = "policy-mini-base"
DEPLOY_POLICY_FT     = "policy-mini-ft"

# Per-1K-token prices (illustrative — verify against your catalog).
PRICE = {
    DEPLOY_PLANNER:     {"in": 0.0050, "out": 0.0150},
    DEPLOY_ROUTER:      {"in": 0.0002, "out": 0.0006},
    DEPLOY_MINI_VISION: {"in": 0.0008, "out": 0.0024},
    DEPLOY_POLICY_BASE: {"in": 0.0008, "out": 0.0024},
    DEPLOY_POLICY_FT:   {"in": 0.0010, "out": 0.0030},
}
