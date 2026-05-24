# s03_router.py — a tiny, fast classifier that names the path.
# Uses the OpenAI Responses API with JSON-mode output.
import json
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from s02_config import PROJECT_ENDPOINT, DEPLOY_ROUTER

_project = AIProjectClient(
    endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())
_client = _project.get_openai_client()

ROUTER_INSTRUCTIONS = """Classify the user's travel request into one of:
  plan_trip         - they want to book or plan travel
  policy_question   - they're asking what's allowed
  receipt_expense   - there's a receipt to process

Return JSON: {"intent": "...", "needs_vision": true|false,
              "needs_translation": true|false}.
JSON only. No prose."""


def route(user_message: str, has_image: bool = False) -> dict:
    resp = _client.responses.create(
        model=DEPLOY_ROUTER,
        temperature=0,
        instructions=ROUTER_INSTRUCTIONS,
        input=f"{user_message}\n[has_image={has_image}]\nReturn JSON only.",
        text={"format": {"type": "json_object"}},
    )
    return json.loads(resp.output_text)


if __name__ == "__main__":
    print(route("book me Berlin Tuesday morning, here is a receipt", True))
