#!/usr/bin/env bash
# =============================================================================
# s99_replay_demo.sh — Reusable demo replay driver (Steps 1-6)
# =============================================================================
#
# PURPOSE
#   Re-run the *code-only* path of the workshop end-to-end so you can record
#   a clean demo without redoing setup, synthetic generation, or fine-tuning.
#   Assumes all 7 deployments (incl. policy-mini-ft) already exist and that
#   sample-data/*.jsonl is intact.
#
# DESIGN
#   - Each stage is an interactive prompt: hit ENTER to run, "s" to skip,
#     "q" to quit. Lets you start recording, pause for a slide, then resume.
#   - Stages write to distinct --label outputs so prior result files are NOT
#     clobbered (you can diff old vs new).
#   - Uses sed to flip USE_FT_POLICY for v2 vs v3 — the marquee one-line
#     architectural diff. The script PRINTS the diff before each flip so it
#     shows up on screen for the audience.
#
# PARALLEL TERMINALS
#   You can also copy individual stages into separate terminals if you want
#   to run them in parallel for a faster demo. Each stage is self-contained;
#   the only ordering constraint is "flip USE_FT_POLICY before running v3".
#
# PREREQS
#   - cwd must be workshops/foundry-models-e2e/code
#   - venv active:  source ../.venv/bin/activate
#   - az login complete, .env loaded (handled by s02_config.py)
#   - All 7 deployments present (verify: az cognitiveservices account
#     deployment list -g $AZURE_RESOURCE_GROUP -n $FOUNDRY_ACCOUNT_NAME -o table)
# =============================================================================
set -euo pipefail

# --- helpers -----------------------------------------------------------------
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
banner() { echo -e "\n${CYAN}════════════════════════════════════════════════════════════════${NC}"; echo -e "${CYAN}▶ $1${NC}"; echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"; }
gate()   { read -rp "$(echo -e ${YELLOW}[$1] ENTER=run, s=skip, q=quit: ${NC})" a; case "$a" in s|S) return 1;; q|Q) exit 0;; *) return 0;; esac; }
flip()   { sed -i "s/^USE_FT_POLICY = .*/USE_FT_POLICY = $1   # set by s99_replay_demo.sh/" s05_multi_model_agent.py; echo -e "${GREEN}--- s05_multi_model_agent.py:39 now reads: ---${NC}"; grep -n "^USE_FT_POLICY" s05_multi_model_agent.py; }

# --- preflight ---------------------------------------------------------------
[[ "$PWD" == *"/foundry-models-e2e/code" ]] || { echo "ERROR: cd into workshops/foundry-models-e2e/code first"; exit 1; }
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  echo "ERROR: workshop venv not active. Run this first, then re-launch the replay:"
  echo "  source ../.venv/bin/activate"
  echo "(System python has no Azure SDKs in this devcontainer, so unvenv'd runs"
  echo " would fail fast rather than silently produce wrong data.)"
  exit 1
fi
echo "venv: $VIRTUAL_ENV"
python -c "import sys; assert sys.prefix != sys.base_prefix, 'not in venv'; print('python:', sys.executable)"
mkdir -p generated
TS=$(date -u +%Y%m%dT%H%M%S)
echo -e "${GREEN}Replay session timestamp: $TS${NC}"
echo "All result files land in generated/  (gitignored). Suffix '${TS}' isolates this run."

# =============================================================================
# STAGE 1 — Carmen single-trace (v1 baseline → multi-model w/ vision)
# =============================================================================
# WHY: The eval harness does NOT pass image_url, so vision OCR (mini-vision)
# is only exercised by this single trace. Show this LIVE so the audience sees
# all 4 models firing in one request (router → vision → policy → planner).
# OUTPUT: stdout JSON; nothing saved to disk.
banner "STAGE 1 · Carmen multi-model trace (vision demo)"
if gate "stage-1"; then
  python s05_multi_model_agent.py | tee "generated/carmen-trace-out.${TS}.json"
fi

# =============================================================================
# STAGE 2 — v1 batch eval (single-model baseline, 173 rows)
# =============================================================================
# WHY: Establishes the "frontier-model-does-everything" baseline. Slow,
# expensive, quality dragged by JSON formatting failures. This is the BEFORE.
# RUNTIME: ~5 min on 100K TPM. Watch progress with [N/173] per-row prints.
# OUTPUT: eval_results_v1-batch-${TS}.json + scorecard to stdout.
banner "STAGE 2 · v1 batch eval — single model baseline"
if gate "stage-2"; then
  python s05_run_eval.py --agent s02_baseline_agent \
                         --eval ../sample-data/eval-full.jsonl \
                         --label "v1-batch-${TS}"
fi

# =============================================================================
# STAGE 3 — v2 batch eval (multi-model, NO fine-tune)
# =============================================================================
# WHY: Same 173 rows, but routed through 4 specialist models. Expect cost to
# drop ~10× vs v1; quality may regress because policy-mini-base is ungrounded.
# This regression motivates the fine-tune in stage 4.
# PRE-STEP: Ensure USE_FT_POLICY = False (printed on screen for audience).
# OUTPUT: eval_results_v2-batch-${TS}.json + scorecard.
banner "STAGE 3 · v2 batch eval — multi-model, NO fine-tune"
if gate "stage-3"; then
  flip False
  python s05_run_eval.py --agent s05_multi_model_agent \
                         --eval ../sample-data/eval-full.jsonl \
                         --label "v2-batch-${TS}"
fi

# =============================================================================
# STAGE 4 — v3 batch eval (multi-model + FT policy)
# =============================================================================
# WHY: The marquee moment. Single-line code change (USE_FT_POLICY=True)
# swaps the policy submodel for the distilled FT model. Architecture, cost,
# latency, and 99 % of the code remain identical.
# PRE-STEP: Flip USE_FT_POLICY = True (printed on screen).
# OUTPUT: eval_results_v3-final-${TS}.json + scorecard.
banner "STAGE 4 · v3 batch eval — multi-model WITH fine-tuned policy"
if gate "stage-4"; then
  flip True
  python s05_run_eval.py --agent s05_multi_model_agent \
                         --eval ../sample-data/eval-full.jsonl \
                         --label "v3-final-${TS}"
fi

# =============================================================================
# STAGE 5 — Isolated policy-only side-by-side (THE FT lift slide)
# =============================================================================
# WHY: End-to-end evals dilute FT lift (policy is 1 of 4 stages). This script
# bypasses the planner and hits policy-mini-base + policy-mini-ft directly
# with the 35-row policy slice. Deterministic constraint check (no LLM judge).
# This produces the clean BEFORE/AFTER number for the headline FT slide.
# OUTPUT: eval_results_policy-isolated.json (overwritten each run).
banner "STAGE 5 · Isolated policy QA — base vs FT, side-by-side"
if gate "stage-5"; then
  python s06_policy_only_eval.py
fi

# =============================================================================
# STAGE 6 — Reset boolean for clean git state
# =============================================================================
# WHY: Workshop default is USE_FT_POLICY = False so first-time learners see
# the regression before discovering FT. Leave the file as committed.
banner "STAGE 6 · Reset USE_FT_POLICY = False (clean git state)"
if gate "stage-6"; then
  flip False
  git -C .. diff --stat code/s05_multi_model_agent.py || true
fi

# =============================================================================
# RECAP
# =============================================================================
banner "DONE · Generated this session"
ls -1t generated/*-${TS}.json 2>/dev/null || true
ls -1t generated/eval_results_policy-isolated.json generated/carmen-trace-out.${TS}.json 2>/dev/null || true
echo -e "\n${GREEN}Slide-ready numbers (all in generated/):${NC}"
echo "  v1: generated/eval_results_v1-batch-${TS}.json  (quality, cost, latency)"
echo "  v2: generated/eval_results_v2-batch-${TS}.json"
echo "  v3: generated/eval_results_v3-final-${TS}.json"
echo "  FT lift slide: generated/eval_results_policy-isolated.json (base vs ft)"
