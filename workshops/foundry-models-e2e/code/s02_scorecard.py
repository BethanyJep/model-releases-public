# =============================================================================
# s02_scorecard.py — Scorecard renderer (Steps 2, 5, 6, 7)
# =============================================================================
# NARRATIVE ROLE
# Every step of this workshop measures the same three dimensions: quality,
# cost, and latency.  This module renders those numbers as a visual bar chart
# (via Rich) so learners can see exactly which needle moved — and which
# didn't — after each architectural change.
#
# The three target thresholds (QUALITY_TARGET, COST_TARGET, LATENCY_TARGET)
# define "good enough for production".  A green ✅ only lights up when that
# bar is met.  The goal of Steps 3-7 is to turn all three green.
# =============================================================================
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box as rich_box

from s02_config import PRICE

QUALITY_TARGET = 0.92
COST_TARGET    = 0.03
LATENCY_TARGET = 8.0

_console = Console()


def _bar(value: float, max_value: float, width: int = 10) -> str:
    frac = max(0.0, min(1.0, value / max_value))
    filled = int(round(frac * width))
    return "█" * filled + "░" * (width - filled)


def cost_of(usage_by_model: dict[str, tuple[int, int]]) -> float:
    total = 0.0
    for model, (tin, tout) in usage_by_model.items():
        p = PRICE.get(model)
        if p is None:
            continue
        total += tin / 1000 * p["in"] + tout / 1000 * p["out"]
    return total


def print_scorecard(version: str, quality: float, cost: float, latency: float):
    q_ok = quality >= QUALITY_TARGET
    c_ok = cost    <= COST_TARGET
    l_ok = latency <= LATENCY_TARGET

    tbl = Table(box=rich_box.SIMPLE, show_header=False, padding=(0, 1))
    tbl.add_column("Metric",  style="bold")
    tbl.add_column("Bar",     no_wrap=True)
    tbl.add_column("Value",   justify="right")
    tbl.add_column("Status")

    tbl.add_row("Quality",
                _bar(quality, 1.0),
                f"{quality:.2f}",
                "[green]✅[/green]" if q_ok else "[dim]  [/dim]")
    tbl.add_row("Cost",
                _bar(cost, 0.15),
                f"${cost:.3f}",
                "[green]✅[/green]" if c_ok else "[dim]  [/dim]")
    tbl.add_row("Latency",
                _bar(latency, 15.0),
                f"{latency:.1f}s",
                "[green]✅[/green]" if l_ok else "[dim]  [/dim]")

    _console.print(Panel(tbl, title=f"[bold cyan]{version}[/bold cyan]",
                         border_style="cyan", expand=False))
