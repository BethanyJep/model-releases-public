# s05_multi_model_agent.py — v2 (USE_FT_POLICY=False) and v3 (True).
# Uses the OpenAI Responses API via azure-ai-projects v2.
# Same code; the only difference is which policy deployment is in use.
import json
import time
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from s02_tools_mock import TOOL_SCHEMAS, DISPATCH
from s03_router import route
from s02_config import (
    PROJECT_ENDPOINT, DEPLOY_PLANNER, DEPLOY_ROUTER,
    DEPLOY_MINI_VISION, DEPLOY_POLICY_BASE, DEPLOY_POLICY_FT,
)

USE_FT_POLICY = False   # flip to True after Step 6 deploys the fine-tune.

_project = AIProjectClient(
    endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())
_client = _project.get_openai_client()


def _bump(usage: dict, model: str, resp) -> None:
    cur = usage.get(model, (0, 0))
    usage[model] = (cur[0] + resp.usage.input_tokens,
                    cur[1] + resp.usage.output_tokens)


def run(user_message: str, image_url: str | None = None) -> dict:
    t0 = time.time()
    usage: dict[str, tuple[int, int]] = {}

    # 1. Route
    intent = route(user_message, has_image=bool(image_url))
    # router usage isn't returned from route(); bill it conservatively
    usage[DEPLOY_ROUTER] = (250, 35)

    # 2. Optional vision pre-step
    vision_facts = None
    if image_url:
        r = _client.responses.create(
            model=DEPLOY_MINI_VISION,
            temperature=0,
            instructions=("Extract receipt fields as JSON: "
                          "merchant, amount, date, category."),
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text",  "text": "Extract. Return JSON only."},
                    {"type": "input_image", "image_url": image_url},
                ],
            }],
            text={"format": {"type": "json_object"}},
        )
        _bump(usage, DEPLOY_MINI_VISION, r)
        try:
            vision_facts = json.loads(r.output_text)
        except Exception:
            vision_facts = {"_raw": r.output_text}

    # 3. Pre-resolve policy answer with the cheap (optionally fine-tuned) model
    policy_model = DEPLOY_POLICY_FT if USE_FT_POLICY else DEPLOY_POLICY_BASE
    pol = _client.responses.create(
        model=policy_model,
        temperature=0,
        instructions="You answer Contoso travel policy questions. Concise.",
        input=user_message,
    )
    _bump(usage, policy_model, pol)
    policy_note = pol.output_text

    # 4. Planner with tools
    planner_instructions = (
        "You are Contoso Travel planner. Use tools. Respect policy. "
        f"Pre-resolved policy: {policy_note}. "
        f"Receipt facts: {vision_facts}. "
        "Return final JSON with keys: flight, hotel, policy_notes, "
        "total_estimated_cost_usd, booking_status."
    )
    input_items: list[dict] = [{"role": "user", "content": user_message}]

    final_response = None
    for _ in range(6):
        r = _client.responses.create(
            model=DEPLOY_PLANNER,
            instructions=planner_instructions,
            input=input_items,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        _bump(usage, DEPLOY_PLANNER, r)
        final_response = r
        input_items += [item.model_dump(exclude_none=True) for item in r.output]

        function_calls = [item for item in r.output if item.type == "function_call"]
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
        "usage_by_model": usage,
        "intent": intent,
        "vision": vision_facts,
        "policy_model_used": policy_model,
    }


if __name__ == "__main__":
    with open("../sample-data/carmen-trace.json") as f:
        carmen = json.load(f)
    out = run(carmen["user_message"], image_url=carmen.get("image_url"))
    print(json.dumps(out, indent=2, default=str))
