# =============================================================================
# run_mode_comparison.py — Compare routing modes (Balanced / Cost / Quality)
# =============================================================================
# Runs evaluations across different router configurations and generates
# a side-by-side comparison report.
#
# Usage:
#   python run_mode_comparison.py --mode cost --dataset ../sample-data/router-eval-prompts.jsonl
#   python run_mode_comparison.py --mode quality --dataset ../sample-data/router-eval-prompts.jsonl
#   python run_mode_comparison.py --compare results/run-a results/run-b results/run-c
# =============================================================================
import argparse
import json
from pathlib import Path


def compare_runs(run_dirs: list):
    """Compare multiple evaluation runs side-by-side."""
    runs = {}
    for run_dir in run_dirs:
        run_path = Path(run_dir)
        name = run_path.name

        # Try to load router responses
        router_file = run_path / "router_responses.jsonl"
        if not router_file.exists():
            print(f"⚠️ Skipping {name} — no router_responses.jsonl found")
            continue

        with open(router_file) as f:
            results = [json.loads(line) for line in f if line.strip()]

        avg_cost = sum(r["cost"] for r in results) / len(results)
        avg_latency = sum(r["latency_s"] for r in results) / len(results)

        # Model distribution
        dist = {}
        for r in results:
            model = r["model"]
            dist[model] = dist.get(model, 0) + 1

        runs[name] = {
            "prompts": len(results),
            "avg_cost": avg_cost,
            "avg_latency": avg_latency,
            "model_distribution": dist,
        }

        # Load judge scores if available
        judge_file = run_path / "judge_scores.jsonl"
        if judge_file.exists():
            with open(judge_file) as f:
                judge = [json.loads(line) for line in f if line.strip()]
            if judge:
                # Average quality from absolute scores
                router_scores = [j.get("router", {}) for j in judge]
                if router_scores and "accuracy" in router_scores[0]:
                    avg_quality = sum(
                        (s.get("accuracy", 3) + s.get("completeness", 3) +
                         s.get("clarity", 3) + s.get("helpfulness", 3)) / 4
                        for s in router_scores
                    ) / len(router_scores)
                    runs[name]["avg_quality"] = avg_quality

    # Print comparison table
    print(f"\n{'='*80}")
    print("MODE COMPARISON")
    print(f"{'='*80}")
    print(f"{'Run':<30} {'Prompts':<10} {'Quality':<10} {'Cost/prompt':<14} {'Latency':<10}")
    print(f"{'-'*80}")
    for name, data in sorted(runs.items()):
        quality = f"{data.get('avg_quality', 0):.2f}" if "avg_quality" in data else "N/A"
        print(f"{name:<30} {data['prompts']:<10} {quality:<10} "
              f"${data['avg_cost']:.4f}      {data['avg_latency']:.2f}s")

    # Model distribution comparison
    print(f"\n{'='*80}")
    print("MODEL DISTRIBUTION")
    print(f"{'='*80}")
    all_models = set()
    for data in runs.values():
        all_models.update(data["model_distribution"].keys())

    header = f"{'Model':<25}" + "".join(f"{name:<20}" for name in sorted(runs.keys()))
    print(header)
    print("-" * len(header))

    for model in sorted(all_models):
        row = f"{model:<25}"
        for name in sorted(runs.keys()):
            count = runs[name]["model_distribution"].get(model, 0)
            total = runs[name]["prompts"]
            pct = f"{count}/{total} ({count/total*100:.0f}%)" if count else "—"
            row += f"{pct:<20}"
        print(row)

    print(f"{'='*80}\n")

    # Save comparison
    output_path = Path("results") / "mode-comparison.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(runs, f, indent=2, default=str)
    print(f"Comparison saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mode Comparison Tool")
    parser.add_argument("--compare", nargs="+",
                        help="Directories to compare (e.g., results/run-a results/run-b)")
    parser.add_argument("--mode", choices=["balanced", "cost", "quality"],
                        help="Routing mode to evaluate")
    parser.add_argument("--dataset", default="../sample-data/router-eval-prompts.jsonl")
    parser.add_argument("--subset", default=None,
                        help="Comma-separated model subset (e.g., 'gpt-5,gpt-5-mini')")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if args.compare:
        compare_runs(args.compare)
    elif args.mode:
        # For actual mode runs, delegate to run_comparison.py with the right endpoint
        output = args.output or f"results/router-{args.mode}"
        print(f"To run a {args.mode}-mode evaluation:")
        print(f"  1. Deploy or reconfigure your router to '{args.mode}' mode")
        print(f"  2. Update AZURE_MODEL_ROUTER_DEPLOYMENT in .env")
        print(f"  3. Run: python run_comparison.py --mode router "
              f"--dataset {args.dataset} --output {output}")
        if args.subset:
            print(f"  4. Model subset: {args.subset}")
            print(f"     (Configure via portal or ARM API before running)")
    else:
        parser.print_help()
