# s03_router.py — a tiny, fast classifier that names the path.
import json
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from s02_config import PROJECT_ENDPOINT, DEPLOY_ROUTER

_project = AIProjectClient(
    endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())
_client = _project.inference.get_azure_openai_client(api_version="2024-10-21")

ROUTER_SYSTEM = """Classify the user's travel request into one of:
  plan_trip         - they want to book or plan travel
  policy_question   - they're asking what's allowed
  receipt_expense   - there's a receipt to process

Return JSON: {"intent": "...", "needs_vision": true|false,
              "needs_translation": true|false}.
JSON only. No prose."""


def route(user_message: str, has_image: bool = False) -> dict:
    resp = _client.chat.completions.create(
        model=DEPLOY_ROUTER,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": ROUTER_SYSTEM},
            {"role": "user",   "content": f"{user_message}\n[has_image={has_image}]"},
        ],
    )
    return json.loads(resp.choices[0].message.content)


if __name__ == "__main__":
    print(route("book me Berlin Tuesday morning, here is a receipt", True))
