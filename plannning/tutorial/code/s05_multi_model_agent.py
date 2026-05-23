# s05_multi_model_agent.py — v2 (USE_FT_POLICY=False) and v3 (True).
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
_client = _project.inference.get_azure_openai_client(api_version="2024-10-21")


def _bump(usage: dict, model: str, resp) -> None:
    cur = usage.get(model, (0, 0))
    usage[model] = (cur[0] + resp.usage.prompt_tokens,
                    cur[1] + resp.usage.completion_tokens)


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
        r = _client.chat.completions.create(
            model=DEPLOY_MINI_VISION,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system",
                 "content": "Extract receipt fields as JSON: "
                            "merchant, amount, date, category."},
                {"role": "user", "content": [
                    {"type": "text", "text": "Extract."},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ]},
            ],
        )
        _bump(usage, DEPLOY_MINI_VISION, r)
        try:
            vision_facts = json.loads(r.choices[0].message.content)
        except Exception:
            vision_facts = {"_raw": r.choices[0].message.content}

    # 3. Pre-resolve policy answer with the cheap (optionally fine-tuned) model
    policy_model = DEPLOY_POLICY_FT if USE_FT_POLICY else DEPLOY_POLICY_BASE
    pol = _client.chat.completions.create(
        model=policy_model,
        temperature=0,
        messages=[
            {"role": "system",
             "content": "You answer Contoso travel policy questions. Concise."},
            {"role": "user", "content": user_message},
        ],
    )
    _bump(usage, policy_model, pol)
    policy_note = pol.choices[0].message.content

    # 4. Planner with tools
    sys = ("You are Contoso Travel planner. Use tools. Respect policy. "
           f"Pre-resolved policy: {policy_note}. "
           f"Receipt facts: {vision_facts}. "
           "Return final JSON with keys: flight, hotel, policy_notes, "
           "total_estimated_cost_usd, booking_status.")
    msgs = [
        {"role": "system", "content": sys},
        {"role": "user",   "content": user_message},
    ]
    msg = None
    for _ in range(6):
        r = _client.chat.completions.create(
            model=DEPLOY_PLANNER, messages=msgs,
            tools=TOOL_SCHEMAS, tool_choice="auto")
        _bump(usage, DEPLOY_PLANNER, r)
        msg = r.choices[0].message
        msgs.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            break
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            out = DISPATCH[tc.function.name](**args)
            msgs.append({"role": "tool", "tool_call_id": tc.id,
                         "content": json.dumps(out)})

    return {
        "answer": msg.content if msg else "",
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
