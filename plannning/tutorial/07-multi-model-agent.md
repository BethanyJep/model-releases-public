# Step 7 — Assemble the multi-model agent (v3)

**Goal:** run the full multi-model agent end-to-end on Carmen's trip, capture v3 numbers, and verify all three scorecard targets are met.

**Surface:** Foundry SDK.

**Time:** 30 min.

**Scorecard at end of step:**
```
Quality   █████████░  0.94  ✅
Cost      ██░░░░░░░░  2.8¢  ✅
Latency   ███░░░░░░░  7.6s  ✅
```

All green. This is the end-of-talk slide.

---

## 7.1 — What's already wired

By now you have:

- `router-nano` — fast classifier (Step 3).
- `mini-vision` — receipt OCR and translation (Step 3).
- `policy-mini-ft` — fine-tuned policy QA (Step 6).
- `planner-gpt54` — multi-step planner with tools (Step 1).
- `s05_multi_model_agent.py` with `USE_FT_POLICY = True` (Step 6).

You haven't touched the *agent topology* since Step 5. That's intentional — the wins in Steps 3, 5, and 6 came from **model and data choices**, not from re-architecting code.

## 7.2 — Run Carmen's full trip end-to-end

```bash
cd code
python -c "
import json, multi_model_agent as agent
with open('../sample-data/carmen-trace.json') as f:
    carmen = json.load(f)
out = agent.run(carmen['user_message'], image_url=carmen.get('image_url'))
print(json.dumps(out, indent=2, default=str))
"
```

Verify the output JSON includes: flight under $1500, hotel near Alexanderplatz under $600 total, policy_notes mentioning Section 4.2 (parking) and 7.1 (flight class), booking_status = `confirmed-mock`.

Wall clock should land **~7–8 seconds**.

## 7.3 — Run the full eval one more time

```bash
python s05_run_eval.py --agent s05_multi_model_agent \
                   --eval ../sample-data/eval-full.jsonl \
                   --label "v3-final"
```

Expected:
```
=== v3-final scorecard ===
Quality   █████████░  0.94  ✅
Cost      ██░░░░░░░░  $0.028  ✅
Latency   ███░░░░░░░  7.6s  ✅
```

If any bar isn't green:
- **Quality < 0.92:** check the policy-only sub-eval; if that's < 0.92 you may need another fine-tune epoch or more train data. If it's the planner rows, look at *which* rows fail — usually budget-edge cases. Adjust planner system prompt to require explicit budget arithmetic.
- **Cost > $0.03:** dump `usage_by_model` for a failing row; you'll usually find the planner doing too many tool round-trips. Trim tool descriptions or add a `max_iterations` guard.
- **Latency > 8s p50:** parallelize router + policy pre-resolution (they don't depend on each other). The current code runs them sequentially for readability; in production you'd `asyncio.gather`.

## 7.4 — Side-by-side comparison

| Version | Architecture | Quality | Cost/task | p50 latency |
|---|---|---|---|---|
| **v1** | `gpt-5.4` only, no tools, no eval | 0.61 (measured later) | $0.108 | 12.3s |
| **v2** | Router + per-task models, no fine-tune | 0.78 | $0.063 | 9.4s |
| **v3** | + fine-tuned policy | **0.94** ✅ | **$0.028** ✅ | **7.6s** ✅ |

The graph of these three rows is the slide. The story is: **each row reflects exactly one decision** (decompose, fine-tune). Each decision was justified by the scorecard *before* it was made.

## 7.5 — Save artifacts

```bash
git add code/ sample-data/ .foundry/datasets/eval-v1.jsonl
git commit -m "v3 multi-model agent: 0.94 / $0.028 / 7.6s"
git tag agent-v3.0-final
```

Push the repo somewhere accessible — the QR code on your last slide points here.

---

➡️ **Next:** [Step 8 — Back to the portal: evals, red team, versions](./08-portal-review.md)
