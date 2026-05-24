# s06_finetune_policy.py — upload data, create fine-tune job, poll until done.
# Uses the Azure OpenAI resource endpoint directly (project endpoint /v1 does
# not expose fine-tuning).  The resource endpoint is derived from the project
# endpoint: https://<account>.services.ai.azure.com → https://<account>.openai.azure.com
import os, re, time
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

from s02_config import PROJECT_ENDPOINT

# Derive the Azure OpenAI resource endpoint from the Foundry project endpoint.
# Pattern: https://<account>.services.ai.azure.com/api/projects/<project>
#       →  https://<account>.openai.azure.com/
_m = re.match(r"https://([^.]+)\.services\.ai\.azure\.com", PROJECT_ENDPOINT)
if not _m:
    raise RuntimeError(f"Cannot derive AOAI endpoint from: {PROJECT_ENDPOINT}")
AOAI_ENDPOINT = f"https://{_m.group(1)}.openai.azure.com/"
AOAI_API_VERSION = "2025-01-01-preview"

BASE_MODEL = "gpt-4.1"        # gpt-4.1 supports supervised fine-tuning in Sweden Central
TRAIN_FILE = "../sample-data/policy-ft-train.jsonl"
VAL_FILE   = "../sample-data/policy-ft-val.jsonl"


def main():
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    client = AzureOpenAI(
        azure_endpoint=AOAI_ENDPOINT,
        azure_ad_token_provider=token_provider,
        api_version=AOAI_API_VERSION,
    )
    print("Using endpoint:", AOAI_ENDPOINT)

    train = client.files.create(file=open(TRAIN_FILE, "rb"), purpose="fine-tune")
    val   = client.files.create(file=open(VAL_FILE,   "rb"), purpose="fine-tune")
    print("uploaded:", train.id, val.id)

    job = client.fine_tuning.jobs.create(
        training_file=train.id,
        validation_file=val.id,
        model=BASE_MODEL,
        hyperparameters={"n_epochs": 3},
        suffix="contoso-policy-v1",
    )
    print("job:", job.id, "status:", job.status)

    while True:
        job = client.fine_tuning.jobs.retrieve(job.id)
        print(f"  {job.status}  trained_tokens={job.trained_tokens}")
        if job.status in ("succeeded", "failed", "cancelled"):
            break
        time.sleep(60)

    print("fine-tuned model id:", job.fine_tuned_model)
    print("Now deploy this id as 'policy-mini-ft' via the Foundry Skill or portal.")


if __name__ == "__main__":
    main()
