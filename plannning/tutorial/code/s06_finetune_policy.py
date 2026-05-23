# s06_finetune_policy.py — upload data, create fine-tune job, poll until done.
import time
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

from s02_config import PROJECT_ENDPOINT
BASE_MODEL = "gpt-5.4-mini"   # use the exact version string from Step 0.
TRAIN_FILE = "../sample-data/policy-ft-train.jsonl"
VAL_FILE   = "../sample-data/policy-ft-val.jsonl"


def main():
    project = AIProjectClient(
        endpoint=PROJECT_ENDPOINT, credential=DefaultAzureCredential())
    client = project.inference.get_azure_openai_client(api_version="2024-10-21")

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
