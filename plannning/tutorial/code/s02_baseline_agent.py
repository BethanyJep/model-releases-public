# s02_baseline_agent.py — v1: one frontier model does every task.
import json
import time
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from s02_tools_mock import TOOL_SCHEMAS, DISPATCH
from s02_config import PROJECT_ENDPOINT, DEPLOY_PLANNER

SYSTEM = """You are Contoso Travel. Use tools to plan and book travel.
Always check policy before booking. Return a final JSON itinerary with keys:
flight, hotel, policy_notes, total_estimated_cost_usd, booking_status."""


def run(user_message: str, image_url: str | None = None) -> dict:
    project = AIProjectClient(
        endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())
    client = project.inference.get_azure_openai_client(api_version="2024-10-21")

    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user",   "content": user_message},
    ]
    t0 = time.time()
    total_in = total_out = 0

    msg = None
    for _ in range(8):
        resp = client.chat.completions.create(
            model=DEPLOY_PLANNER,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        total_in  += resp.usage.prompt_tokens
        total_out += resp.usage.completion_tokens
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            break
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            out = DISPATCH[tc.function.name](**args)
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": json.dumps(out)})

    return {
        "answer": msg.content if msg else "",
        "latency_s": time.time() - t0,
        "usage_by_model": {DEPLOY_PLANNER: (total_in, total_out)},
    }


if __name__ == "__main__":
    with open("../sample-data/carmen-trace.json") as f:
        carmen = json.load(f)
    print(json.dumps(run(carmen["user_message"]), indent=2, default=str))
