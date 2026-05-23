# Step 6 — Fine-tune `gpt-5.4-mini` for policy (SDK + Foundry Skill)

**Goal:** close the policy-QA quality gap (0.81 → ~0.94) at ~1/50th the cost of asking `gpt-5.4`. This is the step that makes the whole architecture earn its keep.

**Surface:** Foundry SDK to prepare/upload data and kick off the job; Foundry Skill (`microsoft-foundry`) to monitor + deploy.

**Time:** 90 min of your time, plus ~2–4 hours of fine-tune training (do this **Day 4 morning** in your 7-day plan).

**Scorecard at end of step:**
```
Quality   █████████░  0.94   ⬆️  (policy bumps overall pass rate over 0.92)
Cost      ███░░░░░░░  $0.029 ⬇️  (frontier no longer answers policy)
Latency   ████░░░░░░  8.1 s  ⬇️  (skip frontier turn for policy)
```

All three bars are within striking distance of the targets. Step 7 ties the bow.

---

## 6.1 — When to fine-tune (and when not to)

Fine-tune **only** when:
- A cheap base model is *close* but not great on a narrow domain task.
- You have ≥30 high-quality labeled examples (more is better; 100–500 is the realistic sweet spot for narrow QA).
- The task is **stable** — you'd be embarrassed to re-train every week.

Don't fine-tune when:
- You haven't tried a good system prompt + retrieval yet.
- Your eval doesn't isolate the task you're trying to fix.
- The base model already hits your target.

For Contoso policy QA: ✅ on all three.

## 6.2 — Prepare the training data

We have 30 hand-labeled policy Q&A pairs in `sample-data/policy-qa.jsonl`. For fine-tuning we need them in chat-format JSONL:

`sample-data/policy-ft-train.jsonl`:

```json
{"messages":[{"role":"system","content":"You answer Contoso travel policy questions. Concise."},{"role":"user","content":"Can I expense airport parking at SAN for a business trip?"},{"role":"assistant","content":"Yes — airport parking is reimbursable up to $25/day under Section 4.2. Submit the receipt within 30 days."}]}
{"messages":[{"role":"system","content":"You answer Contoso travel policy questions. Concise."},{"role":"user","content":"Am I allowed to fly business class on a 4-hour flight?"},{"role":"assistant","content":"No. Business class is only approved for flights over 6 hours (Section 7.1)."}]}
```

Split 24 / 6 train/val. Keep them in `.foundry/datasets/` so the portal can show lineage.

## 6.3 — Sanity check the base model first

```bash
python s05_run_eval.py --agent s05_multi_model_agent \
                   --eval ../sample-data/eval-policy-only.jsonl \
                   --label "policy-base"
# → quality ≈ 0.81
```

Make a note. We need this *before* number for the on-stage chart.

## 6.4 — Kick off the fine-tune via SDK

`code/s06_finetune_policy.py`:

```python
# s06_finetune_policy.py — upload data, create fine-tune job, poll
import time
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from s02_config import PROJECT_ENDPOINT
BASE_MODEL = "gpt-5.4-mini"   # exact version string from Step 0!
TRAIN_FILE = "../sample-data/policy-ft-train.jsonl"
VAL_FILE   = "../sample-data/policy-ft-val.jsonl"

project = AIProjectClient(endpoint=PROJECT_ENDPOINT,
                          credential=DefaultAzureCredential())
client = project.inference.get_azure_openai_client(api_version="2024-10-21")

train = client.files.create(file=open(TRAIN_FILE, "rb"), purpose="fine-tune")
val   = client.files.create(file=open(VAL_FILE,   "rb"), purpose="fine-tune")
print("uploaded:", train.id, val.id)

job = client.fine_tuning.jobs.create(
    training_file=train.id, validation_file=val.id,
    model=BASE_MODEL,
    hyperparameters={"n_epochs": 3},
    suffix="contoso-policy-v1")
print("job:", job.id, "status:", job.status)

while True:
    job = client.fine_tuning.jobs.retrieve(job.id)
    print(f"  {job.status}  trained_tokens={job.trained_tokens}")
    if job.status in ("succeeded", "failed", "cancelled"): break
    time.sleep(60)

print("fine-tuned model id:", job.fine_tuned_model)
```

Run it:

```bash
python s06_finetune_policy.py
```

Training takes anywhere from 30 min to a few hours for 24 rows × 3 epochs. **Start this Day 4 morning so you have Day 5 as a buffer.**

> **If `gpt-5.4-mini` fine-tune is not yet GA in East US 2**, the job will fail at create time. Use the Foundry Skill to find a region where it is GA, retarget, and disclose the cross-region detail on stage. The plan (PLAN.md §9.7) accounts for this.

## 6.5 — Deploy the fine-tuned model (Foundry Skill)

Once the job reports `succeeded` with a `fine_tuned_model` id, deploy it. The Foundry Skill is the cleanest path:

```
Deploy fine-tuned model <fine_tuned_model id from job> to project
contoso-travel-demo in region eastus2 (or <fallback-region>),
deployment name = policy-mini-ft, sku=Standard, tpm=10000.
Verify status=Succeeded and return the endpoint.
```

Or in the portal: **Fine-tuning** → click your job → **Deploy** → name it `policy-mini-ft`.

## 6.6 — Flip the agent to use the fine-tune

In `code/s05_multi_model_agent.py`:

```python
USE_FT_POLICY = True   # was False
```

That's the entire app change. **One boolean.** Because we named deployments by job in Step 3, the agent doesn't care which underlying model is serving the policy job.

> **This is the slide that lands hardest.** Naomi says: *"This is the whole point of decomposing your agent by task and naming deployments by job. The fine-tune is a one-line swap — and we can A/B it in Step 8."*

## 6.7 — Re-run policy eval

```bash
python s05_run_eval.py --agent s05_multi_model_agent \
                   --eval ../sample-data/eval-policy-only.jsonl \
                   --label "policy-ft"
# → quality ≈ 0.94
```

Cost per policy answer:
- Base `gpt-5.4-mini`:  ~$0.0008
- Fine-tuned:            ~$0.0010 *(slight surcharge per token, far cheaper than `gpt-5.4` at $0.015/1K out)*
- Frontier `gpt-5.4`:   ~$0.045 for the same answer

**~50× cheaper than asking the frontier, with higher quality.** That's the headline.

## 6.8 — Version everything

In your repo:

```bash
git tag agent-v2.1-ftpolicy
```

In the portal, the fine-tuned deployment carries a version + lineage to the training file. Open it in **Models + endpoints** and screenshot — this becomes a slide in Step 8.

---

➡️ **Next:** [Step 7 — Assemble the multi-model agent (v3)](./07-multi-model-agent.md)
