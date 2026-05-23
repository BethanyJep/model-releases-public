# Step 0 — Prereqs & project

**Goal:** an empty Foundry project in East US 2 + a local repo that can talk to it.

**Time:** 30–45 min.

**Scorecard at end of step:**
```
Quality   ░░░░░░░░░░  —     (no agent yet)
Cost      ░░░░░░░░░░  —
Latency   ░░░░░░░░░░  —
```

---

## 0.1 — Accounts and tools

You need:

- An Azure subscription with permission to create Microsoft Foundry resources in **East US 2**.
- Azure CLI (`az --version` ≥ 2.60).
- Python 3.11+ and `pip`.
- VS Code with the Python extension.
- *(Recommended)* GitHub Copilot CLI with the `microsoft-foundry` skill enabled — this is what we'll call "the Foundry Skill" later.
- *(Optional)* The Foundry MCP server wired into your editor for raw `models_list`/`model_get` calls.

```bash
az login
az account set --subscription "<your-sub-id>"
```

## 0.2 — Create the Foundry project (Portal, low-code path)

> **Why portal first?** Foundry's portal is the fastest way to see what a *project* actually is — a hub for models, deployments, agents, evaluations, datasets, and traces. Once you've seen it visually, the SDK calls in later steps will feel obvious instead of magical.

1. Open <https://ai.azure.com> and click **+ Create project**.
2. **Name:** `contoso-travel-demo`. **Region:** `East US 2`. **Resource group:** new — `rg-foundry-travel-demo`.
3. Accept defaults for storage and AI Services. Click **Create** and wait ~3 min.
4. Once provisioned, click into the project. In the left nav you should see: **Playground**, **Models + endpoints**, **Agents**, **Evaluation**, **Fine-tuning**, **Datasets**, **Tracing**.
5. **Copy two things into a sticky note:**
   - **Project endpoint** (Overview → "Project details" → Endpoint URL).
   - **Resource group + project name** (for CLI calls later).

## 0.3 — Verify the model catalog (Foundry Skill OR portal)

We're committing to Azure Direct models in East US 2: `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.4-nano`. The catalog moves fast, so verify **today** that those exact versions are deployable in your region.

**Option A — Foundry Skill (AI-assisted, recommended):**

In Copilot CLI (or any tool with the Foundry MCP):

```
List Azure Direct models available in East US 2 that match gpt-5.4*.
For each, show: exact version string, max tokens, supports fine-tuning,
and the per-1K input/output prices.
```

The skill calls `models_list` under the hood and returns a tidy table. Save the exact version strings into `tutorial/code/config.py` (we'll create that file in Step 2).

**Option B — Portal:**

Project → **Models + endpoints** → **Model catalog** → filter:
- **Collection:** *Sold directly by Azure*
- **Region:** *East US 2*
- **Deployable:** ✅

Find each model, click it, and note the version on the **Overview** tab.

> 🚨 **If `gpt-5.4-mini` fine-tuning is not yet GA in East US 2**, note an alternate region (e.g. Sweden Central or East US). Step 6 will need it. The agent inference itself still runs from East US 2.

## 0.4 — Clone or create the local repo

```bash
mkdir contoso-travel-demo && cd contoso-travel-demo
git init
mkdir -p code sample-data .foundry
```

Copy the `tutorial/sample-data/` and `tutorial/code/` files from this folder into your new repo (or symlink for now). We'll build them up step by step.

Create `code/requirements.txt`:

```
azure-ai-projects>=1.0.0
azure-ai-inference>=1.0.0
azure-ai-evaluation>=1.0.0
azure-identity>=1.17.0
openai>=1.50.0
python-dotenv>=1.0.1
rich>=13.7.1
```

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r code/requirements.txt
```

Create a `.env` in the repo root (and add to `.gitignore`):

```
FOUNDRY_PROJECT_ENDPOINT=https://<your-project-endpoint>
FOUNDRY_PROJECT_NAME=contoso-travel-demo
AZURE_RESOURCE_GROUP=rg-foundry-travel-demo
```

## 0.5 — Sanity check

```bash
az ai project show --name contoso-travel-demo \
    --resource-group rg-foundry-travel-demo --output table
```

You should see your project. If you do, **you're done with Step 0**.

---

➡️ **Next:** [Step 1 — Baseline in the playground](./01-baseline-portal.md)
