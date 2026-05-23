# s02_scorecard.py — pretty-prints the three progress bars.
from s02_config import PRICE
QUALITY_TARGET = 0.92
COST_TARGET    = 0.03
LATENCY_TARGET = 8.0


def _bar(value: float, max_value: float, width: int = 10) -> str:
    frac = max(0.0, min(1.0, value / max_value))
    filled = int(round(frac * width))
    return "█" * filled + "░" * (width - filled)


def cost_of(usage_by_model: dict[str, tuple[int, int]]) -> float:
    total = 0.0
    for model, (tin, tout) in usage_by_model.items():
        p = PRICE[model]
        total += tin / 1000 * p["in"] + tout / 1000 * p["out"]
    return total


def print_scorecard(version: str, quality: float, cost: float, latency: float):
    q_pass = "✅" if quality >= QUALITY_TARGET else "  "
    c_pass = "✅" if cost    <= COST_TARGET    else "  "
    l_pass = "✅" if latency <= LATENCY_TARGET else "  "
    print(f"\n=== {version} scorecard ===")
    print(f"Quality   {_bar(quality, 1.0)}  {quality:.2f}     {q_pass}")
    print(f"Cost      {_bar(cost,    0.15)}  ${cost:.3f}  {c_pass}")
    print(f"Latency   {_bar(latency, 15.0)}  {latency:.1f}s    {l_pass}")
