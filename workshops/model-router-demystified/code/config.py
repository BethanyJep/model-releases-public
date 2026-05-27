# =============================================================================
# config.py — Shared configuration for the Model Router workshop
# =============================================================================
import os
from dotenv import load_dotenv

load_dotenv()

# Model Router endpoint
ROUTER_ENDPOINT = os.environ.get("AZURE_MODEL_ROUTER_ENDPOINT", "")
ROUTER_KEY = os.environ.get("AZURE_MODEL_ROUTER_KEY", "")
ROUTER_DEPLOYMENT = os.environ.get("AZURE_MODEL_ROUTER_DEPLOYMENT", "model-router")

# Baseline model endpoint
BASELINE_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
BASELINE_KEY = os.environ.get("AZURE_OPENAI_KEY", "")
BASELINE_DEPLOYMENT = os.environ.get("AZURE_BASELINE_DEPLOYMENT", "gpt-5-baseline")

# Judge model (for LLM-as-a-judge scoring)
JUDGE_ENDPOINT = os.environ.get("AZURE_JUDGE_ENDPOINT", "")
JUDGE_KEY = os.environ.get("AZURE_JUDGE_KEY", "")
JUDGE_DEPLOYMENT = os.environ.get("AZURE_JUDGE_DEPLOYMENT", "gpt-5-baseline")

# Foundry project (for portal integration)
PROJECT_ENDPOINT = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "")

# API version
API_VERSION = "2025-04-01-preview"

# Pricing (per 1M tokens) — used for cost calculations
PRICING = {
    "model-router-markup": {"input": 0.50},  # router markup on input only
    "gpt-5": {"input": 5.00, "output": 15.00},
    "gpt-5-mini": {"input": 1.50, "output": 6.00},
    "gpt-5-nano": {"input": 0.30, "output": 1.20},
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    "o4-mini": {"input": 1.10, "output": 4.40},
}


def get_router_client():
    """Return an AzureOpenAI client pointed at the Model Router deployment."""
    from openai import AzureOpenAI
    return AzureOpenAI(
        azure_endpoint=ROUTER_ENDPOINT,
        api_key=ROUTER_KEY,
        api_version=API_VERSION,
    )


def get_baseline_client():
    """Return an AzureOpenAI client pointed at the baseline model."""
    from openai import AzureOpenAI
    return AzureOpenAI(
        azure_endpoint=BASELINE_ENDPOINT,
        api_key=BASELINE_KEY,
        api_version=API_VERSION,
    )


def get_judge_client():
    """Return an AzureOpenAI client pointed at the judge model."""
    from openai import AzureOpenAI
    return AzureOpenAI(
        azure_endpoint=JUDGE_ENDPOINT,
        api_key=JUDGE_KEY,
        api_version=API_VERSION,
    )


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost for a single request including router markup if applicable."""
    cost = 0.0
    # Router markup on input tokens
    if "router" in model.lower() or model not in PRICING:
        cost += (input_tokens / 1_000_000) * PRICING["model-router-markup"]["input"]

    # Underlying model cost
    pricing = PRICING.get(model, PRICING.get("gpt-5"))
    cost += (input_tokens / 1_000_000) * pricing["input"]
    cost += (output_tokens / 1_000_000) * pricing["output"]
    return cost
