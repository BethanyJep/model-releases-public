# Workshop Feedback

## General

- **Progress granularity:** `.progress.json` should track completed sub-steps (e.g., `"00.1"`, `"00.2"`) alongside top-level steps, and each note entry should record the sub-step number plus a one-line outcome for fast review.

## Step 0 — Setup

- **Verify command uses hardcoded defaults instead of `.env` values.** The `az cognitiveservices account deployment list` verify command in `00-setup.md` (§0.5) hardcodes `contoso-travel-demo-foundry` and `rg-contoso-travel-demo`. It should read `FOUNDRY_ACCOUNT_NAME` and `AZURE_RESOURCE_GROUP` from `.env` (or use shell variable substitution sourced from `.env`) so learners with custom project names get a correct command without manual editing.

## Step 6 — Fine-tune

- **Policy-base quality is 0.47, not 0.28 as the workshop expects.** The `policy-mini-base` deployment (gpt-4.1-mini) already scores 0.47 on the 35-row policy slice — the base model has improved since the workshop was authored. The step still makes sense (there is a gap to close toward 0.94), but the "before" number in the chart, the narrative ("close the 0.28 gap"), and the troubleshoot table should be updated to use ~0.47 as the realistic baseline.
- **Baseline model family mismatch.** The workshop was likely authored against an older model (e.g. gpt-4o or earlier). All four deployments now use the gpt-4.1 series (gpt-4.1, gpt-4.1-mini, gpt-4.1-nano), which is stronger across the board. All expected baseline numbers throughout the workshop (quality, latency, cost, token counts) should be re-benchmarked against gpt-4.1 series and the scorecards updated accordingly.
- **Missing wait-time warning and portal exploration sub-step.** After `python s06_finetune_policy.py` is launched, add a clearly-boxed callout (e.g. `> ⏱ This job typically takes 30–90 minutes`) so learners know not to wait at the terminal. Then add a guided portal exploration sub-step to fill the time: (1) go to **Build → Data** tab — see the uploaded train/val files listed with file IDs and sizes; (2) go to **Build → Fine-tuning** tab — find the running job, click into it to see epoch-by-epoch training loss, hyperparameters, and estimated completion time. This turns the wait into a learning moment instead of dead time.
- **Codespaces sleep resilience.** The fine-tune job runs entirely in Azure — a Codespace going to sleep won't cancel it. Add an explicit note: *"Codespaces may go to sleep during this wait — that's fine. The job keeps running in the cloud. Copy the job ID from the console output before leaving. If your terminal session is lost, you can resume by pasting the job ID into Copilot and asking it to poll the job and continue from where you left off."* The script should also print the job ID prominently (e.g. `SAVE THIS JOB ID: <id>`) so learners know to copy it.

## Step 5 — Evaluations

- **Rate limit hit during curated eval.** `s05_run_eval.py` uses `planner-gpt41` as both the agent and the LLM judge, firing 20+20 calls in rapid succession. The setup script provisions `planner-gpt41` at only 10K TPM GlobalStandard, which is insufficient. Recommend: bump `planner-gpt41` to at least 50K TPM before running evals, or add retry-with-backoff logic in `s05_run_eval.py`. The setup script (`s00_setup.sh`) should note this and offer an eval-mode capacity option.
- **`s00_setup.sh` default capacity (10K TPM) is too low.** Learners hit rate limits as soon as they run any eval (Step 5) or synthetic generation (Step 4). The script should default to at least **50K TPM** for all deployments so learners never have to manually bump quota mid-workshop. The current 10K is only safe for single-call demos.

## Step 2 — Baseline agent in VS Code

- **s02_baseline_agent.py: model returns prose instead of JSON.** The system prompt asks for a JSON itinerary but gpt-4.1 responds in natural language prose after completing tool calls. Fix applied: after the tool-call loop ends, append a user message containing "json" then make one additional `responses.create` call with `text={"format": {"type": "json_object"}}` to force a clean JSON final answer. Note: the `json_object` format requires the word "json" to appear in the input messages — the extra user message satisfies this constraint.
- **s02_baseline_agent.py: `booking_status` and `policy_notes` type mismatch.** The model may return `booking_status` as a plain string (not a dict) and `policy_notes` as a string (not a list). The display code assumed dicts/lists and crashed. Fix applied: type-check both fields before rendering.
- **Missing 2.4: check the Monitor tab in the portal.** After running `s02_baseline_agent.py`, add a sub-step directing learners to the portal **Monitor** tab (Build → Deployments → `planner-gpt41` → Monitor, or the project-level Monitor view) to verify the calls landed: total requests, token consumption, cost, and any failures. This reinforces the observability loop — code runs locally, but the portal gives the aggregate view without any extra SDK work.

- **1.1 portal navigation is outdated.** The step says "left nav → Models + endpoints" but the new Foundry portal uses a top-nav structure: **Build** (top nav) → **Models** (left sidebar under Build) → **Deployments** tab. The step should reference `assets/01-home.png` and `assets/02-models.png` to orient learners visually.
- **Asset screenshots show different model names.** `02-models.png` shows `gpt-5.4-nano`, `gpt-5.4-mini`, `gpt-5.4` — different from the workshop's `gpt-4.1` family. Screenshots should either be retaken with the correct deployments or noted as illustrative-only.
- **1.2 uses a placeholder receipt instead of the real asset.** `assets/00-receipt.png` is a real parking receipt image. The step should instruct learners to download it locally and upload it via the playground's attachment (paperclip) button, rather than using `[pretend a photo is attached]` in the prompt text.
- **1.3 expected numbers are stale.** Workshop expects ~12.3s latency and ~1,429 tokens; actual run (2026-05-24) got 3.2s and 717 tokens (~5–6¢ cost). The scorecard and narrative in §1.3 and §1.4 should be updated to reflect current model performance, or framed as "approximate" with a note that gpt-4.1 has improved since authoring.
- **Missing 1.5: save as agent + agent playground + tracing.** After observing the baseline, add a multi-part closing sub-step to Step 1:
  1. **Save as agent** — use the playground toolbar to save system prompt + model config as `v1-planner`.
  2. **Open Agent Playground** — navigate to the agent and open it in the Agent Playground (Build → Agents → `v1-planner` → Open in playground).
  3. **Connect Application Insights** — in the **Traces** tab of the agent playground, create or connect an Application Insights resource so traces are stored for later viewing.
  4. **Rerun Carmen's prompt** — send the same system prompt + user message (+ `00-receipt.png`) in the agent playground. The agent is still just calling the model with no extra tools — behavior is identical — but now traces and eval metrics are captured in the portal automatically.
  5. **View traces** — after the run, click into the trace to show learners the span-level view: they can see token counts, latency, and the model's response all in one place, establishing the observability baseline before moving to SDK in Step 2.
  - **Note for §1.5d:** The agent playground may have a web search tool wired by default, which means some parts of the response (e.g. flight prices, hotel options) may be grounded in real results. However, booking confirmation will still be hallucinated since no booking tool exists. Call this out explicitly — it's a useful illustration of *partial* grounding and also enables multi-turn conversation traces in App Insights.
