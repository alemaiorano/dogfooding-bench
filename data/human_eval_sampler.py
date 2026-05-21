"""
human_eval_sampler.py
─────────────────────
Extracts a stratified sample of 60 individual test cases from the 38 evaluation
traces for the human calibration study (EMSE submission, R2).

Stratification:
  Stratum A — failed tests (success=False):  20 cases
  Stratum B — passed tests, by raw category: 40 cases

Outputs (written to the same directory as this script):
  human_eval_sample.csv        — BLIND (no system judgment) — hand to evaluators
  human_eval_ground_truth.csv  — with system judgment + metadata — for analysis

Usage:
  cd data && python3 human_eval_sampler.py
"""

import json
import glob
import os
import csv
import random
from collections import defaultdict

SEED = 42
TOTAL_SAMPLE = 60
N_FAIL_TARGET = 20   # ~1/3 failures (mirrors real gate ratio)
N_PASS_TARGET = TOTAL_SAMPLE - N_FAIL_TARGET

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRACES_DIR = os.path.join(SCRIPT_DIR, "evaluation-traces")

random.seed(SEED)

# ──────────────────────────────────────────────
# 1. Pool all individual test results
# ──────────────────────────────────────────────
failed: list[dict] = []
passed: list[dict] = []

for path in sorted(glob.glob(os.path.join(TRACES_DIR, "*.json"))):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("metadata", {})
    run_id = meta.get("runId", os.path.basename(path))

    for result in data.get("results", []):
        question = result.get("message", "").strip()
        response = result.get("responseText", "").strip()
        if not question or not response:
            continue  # skip empty

        record = {
            "run_id": run_id,
            "test_id": result.get("testId", ""),
            "question": question,
            "response": response[:2000],           # truncate very long responses
            "category": result.get("rawCategory") or result.get("category", "general"),
            "intent": result.get("rawIntent") or result.get("intent", ""),
            "system_success": int(bool(result.get("success", False))),
            "issues": "; ".join(result.get("issues", [])),
        }

        if record["system_success"]:
            passed.append(record)
        else:
            failed.append(record)

print(f"Pooled — failed: {len(failed)}, passed: {len(passed)}")

# ──────────────────────────────────────────────
# 2. Stratified sampling
# ──────────────────────────────────────────────

# Stratum A: failed (up to N_FAIL_TARGET)
n_fail = min(N_FAIL_TARGET, len(failed))
sampled_fail = random.sample(failed, n_fail)

# Stratum B: passed — stratified by category
n_pass = TOTAL_SAMPLE - n_fail
by_category: dict[str, list] = defaultdict(list)
for rec in passed:
    by_category[rec["category"]].append(rec)

cats = sorted(by_category.keys())
per_cat = n_pass // len(cats) if cats else n_pass
remainder = n_pass - per_cat * len(cats)

sampled_pass: list[dict] = []
for i, cat in enumerate(cats):
    n = per_cat + (1 if i < remainder else 0)
    pool = by_category[cat]
    sampled_pass.extend(random.sample(pool, min(n, len(pool))))

# If short (some categories had fewer items), top up from passed pool
shortage = n_pass - len(sampled_pass)
if shortage > 0:
    already = {id(r) for r in sampled_pass}
    extra = [r for r in passed if id(r) not in already]
    sampled_pass.extend(random.sample(extra, min(shortage, len(extra))))

# Merge and shuffle
sample = sampled_fail + sampled_pass
random.shuffle(sample)

# Assign sequential eval IDs
for i, rec in enumerate(sample):
    rec["eval_id"] = f"E{i + 1:03d}"

print(f"Sample — failed: {len(sampled_fail)}, passed: {len(sampled_pass)}, total: {len(sample)}")

# Print category distribution
cat_counts: dict[str, dict] = defaultdict(lambda: {"pass": 0, "fail": 0})
for rec in sample:
    key = "fail" if rec["system_success"] == 0 else "pass"
    cat_counts[rec["category"]][key] += 1
print("\nCategory distribution:")
for cat, cnts in sorted(cat_counts.items()):
    print(f"  {cat:30s}  pass={cnts['pass']:2d}  fail={cnts['fail']:2d}")

# ──────────────────────────────────────────────
# 3. Write outputs
# ──────────────────────────────────────────────

BLIND_FIELDS = ["eval_id", "question", "response", "category"]
GT_FIELDS = [
    "eval_id", "run_id", "test_id", "question", "response",
    "category", "intent", "system_success", "issues",
]

blind_path = os.path.join(SCRIPT_DIR, "human_eval_sample.csv")
gt_path = os.path.join(SCRIPT_DIR, "human_eval_ground_truth.csv")

# Blind sample: columns for each human evaluator (to be filled in)
with open(blind_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=BLIND_FIELDS + ["evaluator_1", "evaluator_2"])
    writer.writeheader()
    for rec in sample:
        row = {k: rec[k] for k in BLIND_FIELDS}
        row["evaluator_1"] = ""
        row["evaluator_2"] = ""
        writer.writerow(row)

# Ground truth (researcher-only)
with open(gt_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=GT_FIELDS)
    writer.writeheader()
    for rec in sample:
        writer.writerow({k: rec[k] for k in GT_FIELDS})

print(f"\n✓ Blind sample   → {blind_path}")
print(f"✓ Ground truth   → {gt_path}")
print("\nNext steps:")
print("  1. Send human_eval_sample.csv + HUMAN_EVAL_PROTOCOL.md to 2 evaluators")
print("  2. Evaluators fill 'evaluator_1' / 'evaluator_2' columns (0 = REJECT, 1 = ACCEPT)")
print("  3. Run: python3 llm_judge_eval.py")
print("  4. Run: python3 human_eval_analysis.py")
