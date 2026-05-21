"""
human_eval_analysis.py
──────────────────────
Computes inter-rater reliability and evaluator-alignment metrics for the
human calibration study (EMSE submission, R2).

Inputs:
  human_eval_sample.csv       — human judgments (evaluator_1, evaluator_2 columns filled)
  human_eval_ground_truth.csv — system_success column (automated gate judgment)
  llm_judge_results.csv       — llm_verdict column (LLM-as-judge)

Metrics computed:
  1. Cohen's κ — Human1 vs Human2 (inter-rater reliability)
  2. % Agreement — Human1 vs Human2
  3. Cohen's κ — Human1 vs System gate
  4. Cohen's κ — Human2 vs System gate
  5. Cohen's κ — LLM Judge vs System gate
  6. Cohen's κ — LLM Judge vs Human1
  7. Cohen's κ — LLM Judge vs Human2

Output:
  latex/tables/human_alignment.tex  — LaTeX table for paper
  human_eval_report.txt             — plain-text summary

Usage:
  cd data && python3 human_eval_analysis.py
"""

import csv
import os
import sys
from collections import Counter

import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_PATH = os.path.join(SCRIPT_DIR, "human_eval_sample.csv")
GT_PATH = os.path.join(SCRIPT_DIR, "human_eval_ground_truth.csv")
JUDGE_PATH = os.path.join(SCRIPT_DIR, "llm_judge_results.csv")
TABLES_DIR = os.path.join(SCRIPT_DIR, "..", "latex", "tables")
os.makedirs(TABLES_DIR, exist_ok=True)


# ──────────────────────────────────────────────
# Cohen's κ implementation (binary classification)
# ──────────────────────────────────────────────

def cohen_kappa(a: list[int], b: list[int]) -> float:
    """Compute Cohen's κ for two binary rater vectors."""
    assert len(a) == len(b), "Vectors must have the same length"
    n = len(a)
    if n == 0:
        return float("nan")

    # Observed agreement
    p_o = sum(ai == bi for ai, bi in zip(a, b)) / n

    # Expected agreement
    p_a1 = sum(a) / n  # proportion rater A says 1
    p_b1 = sum(b) / n  # proportion rater B says 1
    p_e = p_a1 * p_b1 + (1 - p_a1) * (1 - p_b1)

    if p_e == 1.0:
        return float("nan")  # degenerate (all same class)

    return (p_o - p_e) / (1 - p_e)


def pct_agreement(a: list[int], b: list[int]) -> float:
    assert len(a) == len(b)
    return sum(ai == bi for ai, bi in zip(a, b)) / len(a) * 100


def kappa_interpretation(k: float) -> str:
    if k < 0:
        return "poor"
    if k < 0.20:
        return "slight"
    if k < 0.40:
        return "fair"
    if k < 0.60:
        return "moderate"
    if k < 0.80:
        return "substantial"
    return "almost perfect"


# ──────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────

for path in [SAMPLE_PATH, GT_PATH, JUDGE_PATH]:
    if not os.path.exists(path):
        print(f"ERROR: {path} not found.")
        if path == SAMPLE_PATH:
            print("  → Run human_eval_sampler.py first")
        elif path == GT_PATH:
            print("  → Run human_eval_sampler.py first")
        elif path == JUDGE_PATH:
            print("  → Run llm_judge_eval.py first")
        sys.exit(1)

# Load sample (human judgments)
sample: dict[str, dict] = {}
with open(SAMPLE_PATH, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        sample[row["eval_id"]] = row

# Load ground truth (system judgment)
gt: dict[str, int] = {}
with open(GT_PATH, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        gt[row["eval_id"]] = int(row["system_success"])

# Load LLM judge results
judge: dict[str, int] = {}
with open(JUDGE_PATH, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        v = int(row["llm_verdict"])
        if v >= 0:  # exclude error cases
            judge[row["eval_id"]] = v

# Determine common eval IDs (all sources present)
common_ids = sorted(
    set(sample.keys()) & set(gt.keys()) & set(judge.keys())
)

# Validate human columns are filled
h1_filled = [eid for eid in common_ids if sample[eid].get("evaluator_1", "").strip() != ""]
h2_filled = [eid for eid in common_ids if sample[eid].get("evaluator_2", "").strip() != ""]
human_complete = sorted(set(h1_filled) & set(h2_filled))

print(f"Cases with LLM judge: {len(common_ids)}")
print(f"Cases with human evaluator 1 filled: {len(h1_filled)}")
print(f"Cases with human evaluator 2 filled: {len(h2_filled)}")
print(f"Cases with both human evaluators: {len(human_complete)}")

# Build vectors
ids_for_llm = common_ids  # LLM vs system (no need for human)
ids_for_human = human_complete  # human comparisons only where both exist

sys_vec_llm = [gt[eid] for eid in ids_for_llm]
llm_vec = [judge[eid] for eid in ids_for_llm]

results: list[dict] = []

# ──────────────────────────────────────────────
# 1. LLM Judge vs System Gate (always available)
# ──────────────────────────────────────────────
k_llm_sys = cohen_kappa(llm_vec, sys_vec_llm)
pa_llm_sys = pct_agreement(llm_vec, sys_vec_llm)
results.append({
    "Comparison": "LLM Judge vs System Gate",
    "N": len(ids_for_llm),
    "Agreement": f"{pa_llm_sys:.1f}\\%",
    "kappa": k_llm_sys,
    "Interpretation": kappa_interpretation(k_llm_sys),
})

# ──────────────────────────────────────────────
# 2. Human comparisons (only if both columns filled)
# ──────────────────────────────────────────────
if ids_for_human:
    h1_vec = [int(sample[eid]["evaluator_1"]) for eid in ids_for_human]
    h2_vec = [int(sample[eid]["evaluator_2"]) for eid in ids_for_human]
    sys_vec_h = [gt[eid] for eid in ids_for_human]
    llm_vec_h = [judge[eid] for eid in ids_for_human]

    # Inter-rater H1 vs H2
    k_h1h2 = cohen_kappa(h1_vec, h2_vec)
    pa_h1h2 = pct_agreement(h1_vec, h2_vec)
    results.insert(0, {
        "Comparison": "Human Evaluator 1 vs 2",
        "N": len(ids_for_human),
        "Agreement": f"{pa_h1h2:.1f}\\%",
        "kappa": k_h1h2,
        "Interpretation": kappa_interpretation(k_h1h2),
    })

    # H1 vs System
    k_h1_sys = cohen_kappa(h1_vec, sys_vec_h)
    pa_h1_sys = pct_agreement(h1_vec, sys_vec_h)
    results.append({
        "Comparison": "Human 1 vs System Gate",
        "N": len(ids_for_human),
        "Agreement": f"{pa_h1_sys:.1f}\\%",
        "kappa": k_h1_sys,
        "Interpretation": kappa_interpretation(k_h1_sys),
    })

    # H2 vs System
    k_h2_sys = cohen_kappa(h2_vec, sys_vec_h)
    pa_h2_sys = pct_agreement(h2_vec, sys_vec_h)
    results.append({
        "Comparison": "Human 2 vs System Gate",
        "N": len(ids_for_human),
        "Agreement": f"{pa_h2_sys:.1f}\\%",
        "kappa": k_h2_sys,
        "Interpretation": kappa_interpretation(k_h2_sys),
    })

    # LLM vs H1
    k_llm_h1 = cohen_kappa(llm_vec_h, h1_vec)
    pa_llm_h1 = pct_agreement(llm_vec_h, h1_vec)
    results.append({
        "Comparison": "LLM Judge vs Human 1",
        "N": len(ids_for_human),
        "Agreement": f"{pa_llm_h1:.1f}\\%",
        "kappa": k_llm_h1,
        "Interpretation": kappa_interpretation(k_llm_h1),
    })

    # LLM vs H2
    k_llm_h2 = cohen_kappa(llm_vec_h, h2_vec)
    pa_llm_h2 = pct_agreement(llm_vec_h, h2_vec)
    results.append({
        "Comparison": "LLM Judge vs Human 2",
        "N": len(ids_for_human),
        "Agreement": f"{pa_llm_h2:.1f}\\%",
        "kappa": k_llm_h2,
        "Interpretation": kappa_interpretation(k_llm_h2),
    })
else:
    print("\nNOTE: Human evaluator columns not yet filled.")
    print("  Only LLM Judge vs System Gate metric is available.")
    print("  Fill evaluator_1 and evaluator_2 in human_eval_sample.csv, then re-run.\n")

# ──────────────────────────────────────────────
# Print summary
# ──────────────────────────────────────────────
print("\n" + "=" * 65)
print("EVALUATOR ALIGNMENT SUMMARY")
print("=" * 65)
for r in results:
    print(f"  {r['Comparison']:<35s}  N={r['N']:3d}  "
          f"Agree={r['Agreement']:>7s}  κ={r['kappa']:.3f}  ({r['Interpretation']})")

# ──────────────────────────────────────────────
# Generate LaTeX table
# ──────────────────────────────────────────────
tex = "\\begin{table}[htbp]\n"
tex += "\\renewcommand{\\arraystretch}{1.2}\n"
tex += "\\centering\n"
tex += "\\scriptsize\n"
tex += "\\setlength{\\tabcolsep}{2.5pt}\n"
caption = ("\\caption{Evaluator alignment study: $n=60$ stratified test cases "
           "(20 system-failed, 40 system-passed), evaluated blind by two independent human evaluators "
           "and an LLM-as-judge using a judge model from a different capability tier "
           "within the same model family (partial mitigation of shared-bias risk; "
           "same-family bias cannot be fully excluded)~\\cite{zheng2023judging}. ")
if ids_for_human:
    caption += ("Human evaluator columns completed. "
                "$\\kappa$ interpretation follows Landis \\& Koch~\\cite{landis1977kappa}; "
                "see Section~\\ref{sec:discussion} for disaggregated failure-mode analysis.}\n")
else:
    caption += ("Human evaluator columns pending annotator completion. "
                "$\\kappa$ interpretation follows Landis \\& Koch~\\cite{landis1977kappa}; "
                "see Section~\\ref{sec:discussion} for disaggregated failure-mode analysis.}\n")
tex += caption
tex += "\\label{tab:human_alignment}\n"
tex += "\\begin{tabular}{p{3.0cm}rrr}\n"
tex += "\\toprule\n"
tex += ("\\textbf{Comparison} & \\textbf{N} & "
        "\\textbf{Agree.} & \\textbf{$\\kappa$} \\\\\n")
tex += "\\midrule\n"

for r in results:
    kappa_fmt = f"{r['kappa']:.3f}"
    tex += (f"{r['Comparison']} & {r['N']} & "
            f"{r['Agreement']} & {kappa_fmt} \\\\\n")

tex += "\\bottomrule\n"
tex += "\\end{tabular}\n"
tex += "\\setlength{\\tabcolsep}{6pt}\n"
tex += "\\end{table}\n"

table_path = os.path.join(TABLES_DIR, "human_alignment.tex")
with open(table_path, "w", encoding="utf-8") as f:
    f.write(tex)

print(f"\n✓ LaTeX table written to {table_path}")

# ──────────────────────────────────────────────
# Plain-text report
# ──────────────────────────────────────────────
report_lines = [
    "HUMAN CALIBRATION STUDY — ALIGNMENT REPORT",
    "=" * 50,
    f"Sample size: {len(common_ids)} cases (stratified: 20 failed + 40 passed)",
    "",
]
for r in results:
    report_lines.append(
        f"{r['Comparison']}: "
        f"N={r['N']}, Agreement={r['Agreement']}, κ={r['kappa']:.3f} ({r['Interpretation']})"
    )

# Failure mode breakdown (LLM-based, always available)
tc_fails = sum(1 for eid in ids_for_llm
               if eid in judge and judge[eid] == 0
               and gt[eid] == 1)
fn = sum(1 for eid in ids_for_llm
         if judge[eid] == 0 and gt[eid] == 1)  # LLM rejects but system accepts
fp = sum(1 for eid in ids_for_llm
         if judge[eid] == 1 and gt[eid] == 0)  # LLM accepts but system rejects

report_lines += [
    "",
    "LLM Judge vs System Gate disagreement breakdown:",
    f"  False negatives (LLM rejects, system accepts): {fn}",
    f"  False positives (LLM accepts, system rejects): {fp}",
]

report_path = os.path.join(SCRIPT_DIR, "human_eval_report.txt")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines) + "\n")

print(f"✓ Plain-text report → {report_path}")
print("\nAll done. Add \\input{{tables/human_alignment}} to your LaTeX manuscript.")
