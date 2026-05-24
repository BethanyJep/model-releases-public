# s02_baseline_agent.py — v1: one frontier model does every task.
# Uses the OpenAI Responses API via azure-ai-projects v2.
import json
import time
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from s02_tools_mock import TOOL_SCHEMAS, DISPATCH
from s02_config import PROJECT_ENDPOINT, DEPLOY_PLANNER

INSTRUCTIONS = """You are Contoso Travel. Use tools to plan and book travel.
Always check policy before booking. Return a final JSON itinerary with keys:
flight, hotel, policy_notes, total_estimated_cost_usd, booking_status."""


def run(user_message: str, image_url: str | None = None) -> dict:
    project = AIProjectClient(
        endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())
    client = project.get_openai_client()

    input_items: list[dict] = [{"role": "user", "content": user_message}]
    t0 = time.time()
    total_in = total_out = 0

    final_response = None
    for _ in range(8):
        resp = client.responses.create(
            model=DEPLOY_PLANNER,
            instructions=INSTRUCTIONS,
            input=input_items,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        total_in  += resp.usage.input_tokens
        total_out += resp.usage.output_tokens
        final_response = resp

        # Carry every output item back into the next turn.
        input_items += [item.model_dump(exclude_none=True) for item in resp.output]

        function_calls = [item for item in resp.output if item.type == "function_call"]
        if not function_calls:
            break
        for fc in function_calls:
            args = json.loads(fc.arguments)
            out = DISPATCH[fc.name](**args)
            input_items.append({
                "type": "function_call_output",
                "call_id": fc.call_id,
                "output": json.dumps(out),
            })

    return {
        "answer": final_response.output_text if final_response else "",
        "latency_s": time.time() - t0,
        "usage_by_model": {DEPLOY_PLANNER: (total_in, total_out)},
    }


if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import print as rprint
    from s02_scorecard import cost_of

    console = Console()

    with open("../sample-data/carmen-trace.json") as f:
        carmen = json.load(f)

    with console.status("[bold cyan]Running v1 agent (planner-gpt41)…[/]"):
        result = run(carmen["user_message"])

    itinerary = json.loads(result["answer"])
    tin, tout = result["usage_by_model"][DEPLOY_PLANNER]
    cost = cost_of(result["usage_by_model"])

    # ── Itinerary panel ──────────────────────────────────────────────────
    # Handle both nested {"selected": {...}} and flat {"carrier": ...} structures
    raw_flight = itinerary.get("flight", {})
    raw_hotel  = itinerary.get("hotel",  {})
    flight  = raw_flight.get("selected", raw_flight) if isinstance(raw_flight, dict) else {}
    hotel   = raw_hotel.get("selected",  raw_hotel)  if isinstance(raw_hotel,  dict) else {}
    booking = itinerary.get("booking_status", {})

    itinerary_lines = (
        f"[bold]Flight[/]   {flight.get('carrier','')} {flight.get('number','')}  "
        f"{flight.get('depart','')} → {flight.get('arrive_local','')}  "
        f"${flight.get('price_usd','?')}\n"
        f"[bold]Hotel[/]    {hotel.get('name','')}  "
        f"${hotel.get('nightly_usd','?')}/night × {hotel.get('checkout','?')} → {hotel.get('checkin','?')}  "
        f"(${hotel.get('total_usd','?')})\n"
        f"[bold]Total[/]    ${itinerary.get('total_estimated_cost_usd', '?')} USD\n"
        f"[bold]Booking[/]  {booking.get('booking_id','?')}  [{booking.get('status','?')}]"
    )
    console.print(Panel(itinerary_lines, title="[bold green]Carmen's Itinerary — v1[/]", expand=False))

    # ── Policy notes ─────────────────────────────────────────────────────
    for note in itinerary.get("policy_notes", []):
        console.print(f"  [dim]·[/] {note}")

    # ── Scorecard table ───────────────────────────────────────────────────
    table = Table(title="\nv1 Scorecard", show_header=True, header_style="bold magenta")
    table.add_column("Metric",  style="bold")
    table.add_column("Value",   justify="right")
    table.add_column("Target",  justify="right", style="dim")
    table.add_column("Pass?",   justify="center")

    table.add_row("Latency",    f"{result['latency_s']:.1f}s",  "≤ 8.0s",  "❌")
    table.add_row("Tokens in",  f"{tin:,}",                     "—",       "")
    table.add_row("Tokens out", f"{tout:,}",                    "—",       "")
    table.add_row("Cost/task",  f"${cost:.4f}",                 "≤ $0.030","❌")
    table.add_row("Quality",    "? (no eval yet)",              "≥ 0.92",  "❓")

    console.print(table)
