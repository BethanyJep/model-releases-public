# Step 1 — Baseline in the playground (Portal, low-code)

**Goal:** see one frontier model try to do *everything* Carmen's trip needs. Establish the v1 cost and latency, and feel the pain that motivates the rest of the tutorial.

**Surface:** Foundry Portal — Playground.

**Time:** 20 min.

**Scorecard at end of step:**
```
Quality   ░░░░░░░░░░  ?     (we don't even have an eval yet!)
Cost      ██████████  ~11¢
Latency   ██████████  ~12.3s
```

The bars are red. They *should* be red — that's the point.

---

## 1.1 — Deploy `gpt-5.4`

Portal → **Models + endpoints** → **+ Deploy model**.

- **Model:** `gpt-5.4` (Azure Direct, East US 2).
- **Deployment name:** `planner-gpt54`.
- **SKU:** Standard. **TPM:** start with 30K (you can raise later).
- Click **Deploy** and wait until status = `Succeeded`.

> **Why this name?** We're going to deploy several models, each with a *job-shaped* name. `planner-gpt54` says "this is the planner role, served by gpt-5.4." Naming things by job, not by model, makes Step 7 (swapping models without touching app code) trivial.

## 1.2 — Open the playground and paste Carmen's request

Portal → **Playground** → choose deployment `planner-gpt54`.

System prompt (paste verbatim):

```
You are Contoso Travel, an internal agent that helps employees plan
business travel. You can call tools: search_flights, search_hotels,
check_policy, submit_booking. You must respect company policy and
return a final itinerary as JSON with keys: flight, hotel, policy_notes,
total_estimated_cost_usd, booking_status.
```

User prompt (this is **Carmen's trip** from the demo):

```
Hi, I'm Carmen from the San Diego office. I need to be in Berlin
Tuesday morning for an offsite that runs through Thursday evening.
Please book my flights and a hotel near Alexanderplatz. Keep it
under $2,500. Also — here's a parking receipt photo from three days
ago at SAN, can you expense it? [pretend a photo is attached]
```

Click **Send**.

## 1.3 — Observe what happens

You'll see something like:

- A long, thoughtful, well-written response.
- ~12 seconds wall-clock.
- Token usage in the bottom panel — typically 3K–5K total tokens.
- The model **invents** flight numbers and hotel availability because we haven't wired tools yet.
- It **politely refuses** the receipt because it can't actually see the image (the playground is text-only by default).

Click **View code** → copy the request JSON. Note the cost estimate; for `gpt-5.4` at toy traffic this lands around **~$0.11 per turn**.

## 1.4 — Write down v1

Open `tutorial/code/s02_scorecard.py` (we'll create it in Step 2; for now just jot in a note):

```
v1 (gpt-5.4 only, no tools, no eval):
  Quality:  unknown   ← we have no measurement
  Cost:     $0.11 / task
  Latency:  12.3 s
```

## 1.5 — The lesson

This is what *most* AI demos look like on day one:

- One big model doing every job.
- No tools — so answers are confident fiction.
- No eval — so "it sounds good" is the only quality signal.
- A cost that's fine for a demo and **terrifying at 10,000 tasks/day**.

> **Yina's line in the deck (Step 8):** *"At $0.11 per task and Contoso's 8,000 trips a month, that's ~$10,560/year just on travel planning. And we can't tell our CFO whether the answers are right."*

That's the gap the next seven steps close.

---

➡️ **Next:** [Step 2 — Baseline agent in VS Code](./02-baseline-sdk.md)
