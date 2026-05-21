"""
Statistical analysis for the Dogfooding Quality Gates paper.
Computes: descriptive statistics, Mann-Kendall trend test,
Spearman correlations, bootstrap confidence intervals,
overhead/scalability summary, and gate ablation analysis.
"""
import os
import numpy as np
import pandas as pd
from scipy import stats
import pymannkendall as mk

THRESHOLDS = {
    'success_rate': 80.0,
    'research_context': 90.0,
    'p95_latency_ms': 15000.0,
    'safety_rate': 95.0,
    'evidence_coverage': 80.0,
}
ROLLBACK_FACTOR = 0.70


script_dir = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(script_dir, "decision-log.csv")
output_dir = os.path.join(script_dir, "..", "latex", "tables")
os.makedirs(output_dir, exist_ok=True)


def parse_percent_column(df: pd.DataFrame, source_col: str, target_col: str) -> None:
    df[target_col] = df[source_col].astype(str).str.rstrip('%').astype(float)


def gate_decision(row: pd.Series, include_dims: set[str]) -> str:
    rollback = False
    hold = False

    dim_values = {
        'success_rate': row['Success_Rate_Num'],
        'research_context': row['Research_Context_Num'],
        'safety_rate': row['Safety_Rate_Num'],
        'evidence_coverage': row['Evidence_Coverage_Num'],
    }

    for dim, value in dim_values.items():
        if dim not in include_dims:
            continue
        threshold = THRESHOLDS[dim]
        rollback_threshold = threshold * ROLLBACK_FACTOR
        if value < rollback_threshold:
            rollback = True
            break
        if value < threshold:
            hold = True

    if 'p95_latency_ms' in include_dims:
        value = float(row['P95_Latency'])
        threshold = THRESHOLDS['p95_latency_ms']
        rollback_threshold = threshold / ROLLBACK_FACTOR
        if value >= rollback_threshold:
            rollback = True
        elif value >= threshold:
            hold = True

    if rollback:
        return 'ROLLBACK'
    if hold:
        return 'HOLD'
    return 'PROMOTE'


def has_severe_failure(row: pd.Series) -> bool:
    if row['Success_Rate_Num'] < THRESHOLDS['success_rate'] * ROLLBACK_FACTOR:
        return True
    if row['Research_Context_Num'] < THRESHOLDS['research_context'] * ROLLBACK_FACTOR:
        return True
    if row['Safety_Rate_Num'] < THRESHOLDS['safety_rate'] * ROLLBACK_FACTOR:
        return True
    if row['Evidence_Coverage_Num'] < THRESHOLDS['evidence_coverage'] * ROLLBACK_FACTOR:
        return True
    if float(row['P95_Latency']) >= THRESHOLDS['p95_latency_ms'] / ROLLBACK_FACTOR:
        return True
    return False


# Load and parse

df = pd.read_csv(data_file)
df = df.sort_values(by="Release").reset_index(drop=True)
df['Run_ID'] = df.index + 1

parse_percent_column(df, 'Success_Rate', 'Success_Rate_Num')
parse_percent_column(df, 'Research_Context', 'Research_Context_Num')
parse_percent_column(df, 'Safety_Rate', 'Safety_Rate_Num')
parse_percent_column(df, 'Evidence_Coverage', 'Evidence_Coverage_Num')

df['Duration_ms'] = pd.to_numeric(df.get('Duration_ms', 0), errors='coerce').fillna(0)
df['Duration_Per_Test_ms'] = pd.to_numeric(df.get('Duration_Per_Test_ms', 0), errors='coerce').fillna(0)

print("=" * 70)
print("STATISTICAL ANALYSIS — Dogfooding Quality Gates Paper")
print("=" * 70)

# ============================================================
# 1. Descriptive Statistics
# ============================================================
print("\n1. DESCRIPTIVE STATISTICS (all runs)")
print("-" * 50)

desc_metrics = {
    'Task Success Rate (%)': df['Success_Rate_Num'],   # merged: Success + Helpful (rho=1.00)
    'P95 Latency (ms)': df['P95_Latency'],
    'Research Context Preservation (%)': df['Research_Context_Num'],
    'Safety Pass Rate (%)': df['Safety_Rate_Num'],
    'Evidence Coverage (%)': df['Evidence_Coverage_Num'],
}

desc_rows = []
for name, series in desc_metrics.items():
    desc_rows.append({
        'Metric': name,
        'Mean': f"{series.mean():.1f}",
        'Median': f"{series.median():.1f}",
        'SD': f"{series.std():.1f}",
        'Min': f"{series.min():.1f}",
        'Max': f"{series.max():.1f}",
        'IQR': f"{series.quantile(0.75) - series.quantile(0.25):.1f}",
    })
    print(
        f"  {name}: mean={series.mean():.1f}, median={series.median():.1f}, "
        f"SD={series.std():.1f}, range=[{series.min():.1f}, {series.max():.1f}]"
    )

# Generate LaTeX table

desc_tex = "\\begin{table}[htbp]\n"
desc_tex += "\\renewcommand{\\arraystretch}{1.2}\n"
desc_tex += "\\centering\n"
desc_tex += "\\scriptsize\n"
desc_tex += "\\setlength{\\tabcolsep}{2.5pt}\n"
desc_tex += "\\caption{Descriptive statistics across evaluation runs.}\n"
desc_tex += "\\label{tab:descriptive}\n"
desc_tex += "\\begin{tabular}{p{1.35cm}rrrrrr}\n"
desc_tex += "\\toprule\n"
desc_tex += "\\textbf{Metric} & \\textbf{Mean} & \\textbf{Med.} & \\textbf{SD} & \\textbf{Min} & \\textbf{Max} & \\textbf{IQR} \\\\\n"
desc_tex += "\\midrule\n"
metric_label_short = {
    'Task Success Rate (%)': 'Task Success',
    'P95 Latency (ms)': 'P95 Latency',
    'Research Context Preservation (%)': 'Research Ctx. Pres.',
    'Safety Pass Rate (%)': 'Safety Pass',
    'Evidence Coverage (%)': 'Evidence Coverage',
}
for row in desc_rows:
    metric_safe = metric_label_short.get(row['Metric'], row['Metric']).replace('%', '\\%')
    desc_tex += f"{metric_safe} & {row['Mean']} & {row['Median']} & {row['SD']} & {row['Min']} & {row['Max']} & {row['IQR']} \\\\\n"
desc_tex += "\\bottomrule\n"
desc_tex += "\\end{tabular}\n"
desc_tex += "\\setlength{\\tabcolsep}{6pt}\n"
desc_tex += "\\end{table}\n"

with open(os.path.join(output_dir, "descriptive_stats.tex"), "w", encoding='utf-8') as f:
    f.write(desc_tex)

# ============================================================
# 2. Mann-Kendall Trend Test
# ============================================================
print("\n2. MANN-KENDALL TREND TEST")
print("-" * 50)

mk_results = []
for name, series in desc_metrics.items():
    result = mk.original_test(series.values)
    trend_str = result.trend
    p_val = result.p
    tau = result.Tau
    print(f"  {name}: trend={trend_str}, tau={tau:.3f}, p={p_val:.4f}")
    mk_results.append({
        'Metric': name,
        'Trend': trend_str,
        'Tau': f"{tau:.3f}",
        'p-value': f"{p_val:.4f}",
        'Significant': 'Yes' if p_val < 0.05 else 'No',
    })

mk_tex = "\\begin{table}[htbp]\n"
mk_tex += "\\renewcommand{\\arraystretch}{1.2}\n"
mk_tex += "\\centering\n"
mk_tex += "\\small\n"
mk_tex += "\\setlength{\\tabcolsep}{3pt}\n"
mk_tex += "\\caption{Mann-Kendall trend test for monotonic trends ($\\alpha=0.05$).}\n"
mk_tex += "\\label{tab:mann_kendall}\n"
mk_tex += "\\begin{tabular}{p{1.75cm}llrl}\n"
mk_tex += "\\toprule\n"
mk_tex += "\\textbf{Metric} & \\textbf{Trend} & \\textbf{$\\tau$} & \\textbf{p-value} & \\textbf{Sig.} \\\\\n"
mk_tex += "\\midrule\n"
for row in mk_results:
    metric_safe = row['Metric'].replace('%', '\\%')
    mk_tex += f"{metric_safe} & {row['Trend']} & {row['Tau']} & {row['p-value']} & {row['Significant']} \\\\\n"
mk_tex += "\\bottomrule\n"
mk_tex += "\\end{tabular}\n"
mk_tex += "\\setlength{\\tabcolsep}{6pt}\n"
mk_tex += "\\end{table}\n"

with open(os.path.join(output_dir, "mann_kendall.tex"), "w", encoding='utf-8') as f:
    f.write(mk_tex)

# ============================================================
# 3. Spearman Rank Correlations
# ============================================================
print("\n3. SPEARMAN CORRELATIONS BETWEEN DIMENSIONS")
print("-" * 50)

# Exclude Research Context Preservation (constant 100%)

corr_cols = ['Success_Rate_Num', 'P95_Latency', 'Safety_Rate_Num', 'Evidence_Coverage_Num']
corr_labels = ['TaskSR', 'P95', 'Safety', 'Evid']

corr_matrix = df[corr_cols].corr(method='spearman')
corr_matrix.index = corr_labels
corr_matrix.columns = corr_labels

# Pairwise significance (two-sided Spearman test) over the same dimensions
corr_pvalues = stats.spearmanr(df[corr_cols].values).pvalue

print(corr_matrix.round(3).to_string())
print("p-values:")
print(pd.DataFrame(corr_pvalues, index=corr_labels, columns=corr_labels).round(4).to_string())

corr_tex = "\\begin{table}[htbp]\n"
corr_tex += "\\renewcommand{\\arraystretch}{1.2}\n"
corr_tex += "\\centering\n"
corr_tex += "\\small\n"
corr_tex += "\\setlength{\\tabcolsep}{3pt}\n"
corr_tex += (
    "\\caption{Spearman rank correlation matrix between variable quality "
    "dimensions (RC excluded as constant). $^{*}$\\,$p<0.05$ (two-sided, "
    f"$n={len(df)}$); coefficients without a marker are not statistically "
    "significant.}\n"
)
corr_tex += "\\label{tab:correlations}\n"
corr_tex += "\\begin{tabular}{l" + "r" * len(corr_labels) + "}\n"
corr_tex += "\\toprule\n"
corr_tex += " & " + " & ".join([f"\\textbf{{{label}}}" for label in corr_labels]) + " \\\\\n"
corr_tex += "\\midrule\n"
for i, label in enumerate(corr_labels):
    cells = []
    for j in range(len(corr_labels)):
        cell = f"{corr_matrix.iloc[i, j]:.2f}"
        if i != j and corr_pvalues[i, j] < 0.05:
            cell += "$^{*}$"
        cells.append(cell)
    corr_tex += f"\\textbf{{{label}}} & {' & '.join(cells)} \\\\\n"
corr_tex += "\\bottomrule\n"
corr_tex += "\\end{tabular}\n"
corr_tex += "\\setlength{\\tabcolsep}{6pt}\n"
corr_tex += "\\end{table}\n"

with open(os.path.join(output_dir, "correlations.tex"), "w", encoding='utf-8') as f:
    f.write(corr_tex)

# ============================================================
# 4. Bootstrap 95% Confidence Intervals
# ============================================================
print("\n4. BOOTSTRAP 95% CONFIDENCE INTERVALS (B=10,000)")
print("-" * 50)

rng = np.random.default_rng(42)
boot_iterations = 10000

ci_rows = []
for name, series in desc_metrics.items():
    data = series.values
    boot_means = np.array([
        rng.choice(data, size=len(data), replace=True).mean()
        for _ in range(boot_iterations)
    ])
    ci_low = np.percentile(boot_means, 2.5)
    ci_high = np.percentile(boot_means, 97.5)
    print(f"  {name}: mean={data.mean():.1f}, 95% CI=[{ci_low:.1f}, {ci_high:.1f}]")
    ci_rows.append({
        'Metric': name,
        'Mean': f"{data.mean():.1f}",
        'CI_Low': f"{ci_low:.1f}",
        'CI_High': f"{ci_high:.1f}",
    })

ci_tex = "\\begin{table}[htbp]\n"
ci_tex += "\\renewcommand{\\arraystretch}{1.2}\n"
ci_tex += "\\centering\n"
ci_tex += "\\small\n"
ci_tex += "\\setlength{\\tabcolsep}{3pt}\n"
ci_tex += "\\caption{Bootstrap 95\\% confidence intervals for metric means (B=10{,}000).}\n"
ci_tex += "\\label{tab:confidence_intervals}\n"
ci_tex += "\\begin{tabular}{p{2.1cm}rr}\n"
ci_tex += "\\toprule\n"
ci_tex += "\\textbf{Metric} & \\textbf{Mean} & \\textbf{95\\% CI} \\\\\n"
ci_tex += "\\midrule\n"
for row in ci_rows:
    metric_safe = row['Metric'].replace('%', '\\%')
    ci_tex += f"{metric_safe} & {row['Mean']} & [{row['CI_Low']}, {row['CI_High']}] \\\\\n"
ci_tex += "\\bottomrule\n"
ci_tex += "\\end{tabular}\n"
ci_tex += "\\setlength{\\tabcolsep}{6pt}\n"
ci_tex += "\\end{table}\n"

with open(os.path.join(output_dir, "confidence_intervals.tex"), "w", encoding='utf-8') as f:
    f.write(ci_tex)

# ============================================================
# 5. Decision Summary
# ============================================================
print("\n5. DECISION SUMMARY")
print("-" * 50)

decisions = df['Decision'].value_counts()
total_runs = len(df)
for decision, count in decisions.items():
    print(f"  {decision}: {count}/{total_runs} ({count/total_runs*100:.1f}%)")

# Decision log table — full per-run trace, regenerated from decision-log.csv
dlog_tex = "\\begin{table*}[htbp]\n"
dlog_tex += "\\renewcommand{\\arraystretch}{1.2}\n"
dlog_tex += "\\centering\n"
dlog_tex += "\\small\n"
dlog_tex += "\\setlength{\\tabcolsep}{3.5pt}\n"
dlog_tex += (
    f"\\caption{{Complete evaluation trace results across {total_runs} runs "
    "with 5 quality dimensions (Task Success Rate consolidates the legacy "
    "Success/Helpful overlap).}\n"
)
dlog_tex += "\\label{tab:decision_log}\n"
dlog_tex += "\\begin{tabular}{rrrrrrrl}\n"
dlog_tex += "\\toprule\n"
dlog_tex += (
    "\\textbf{Run} & \\textbf{Tests} & \\textbf{Task Success} & \\textbf{P95 (ms)} & "
    "\\textbf{Context} & \\textbf{Safety} & \\textbf{Evidence} & \\textbf{Decision} \\\\\n"
)
dlog_tex += "\\midrule\n"
for _, dlog_row in df.iterrows():
    decision = dlog_row['Decision']
    decision_cell = f"\\textbf{{{decision}}}" if decision == 'ROLLBACK' else decision
    success = str(dlog_row['Success_Rate']).replace('%', '\\%')
    context = str(dlog_row['Research_Context']).replace('%', '\\%')
    safety = str(dlog_row['Safety_Rate']).replace('%', '\\%')
    evidence = str(dlog_row['Evidence_Coverage']).replace('%', '\\%')
    dlog_tex += (
        f"{dlog_row['Run_ID']} & {dlog_row['Total_Tests']} & {success} & "
        f"{dlog_row['P95_Latency']} & {context} & {safety} & {evidence} & "
        f"{decision_cell} \\\\\n"
    )
dlog_tex += "\\bottomrule\n"
dlog_tex += "\\end{tabular}\n"
dlog_tex += "\\setlength{\\tabcolsep}{6pt}\n"
dlog_tex += "\\end{table*}\n"

with open(os.path.join(output_dir, "decision_log.tex"), "w", encoding='utf-8') as f:
    f.write(dlog_tex)
print(f"  Decision log table written ({total_runs} rows) -> decision_log.tex")

print("\n6. QUESTION BANK EVOLUTION")
print("-" * 50)
for _, row in df.groupby('Total_Tests').agg(
    count=('Run_ID', 'count'),
    first_run=('Release', 'min'),
    last_run=('Release', 'max')
).reset_index().iterrows():
    print(f"  {int(row['Total_Tests'])} tests: {row['count']} runs ({str(row['first_run'])[:10]} to {str(row['last_run'])[:10]})")

# ============================================================
# 7. Overhead and Scalability
# ============================================================
print("\n7. OVERHEAD AND SCALABILITY")
print("-" * 50)

duration_median = df['Duration_ms'].median()
duration_min = df['Duration_ms'].min()
duration_max = df['Duration_ms'].max()
per_test_median = df['Duration_Per_Test_ms'].median()
pearson_r, pearson_p = stats.pearsonr(df['Total_Tests'], df['Duration_ms'])
slope_ms_per_test = np.polyfit(df['Total_Tests'], df['Duration_ms'], 1)[0]

print(f"  Duration median={duration_median:.1f}ms range=[{duration_min:.0f}, {duration_max:.0f}]")
print(f"  Duration per test median={per_test_median:.1f}ms")
print(f"  Correlation total_tests vs duration: r={pearson_r:.3f}, p={pearson_p:.4f}")
print(f"  Linear slope: +{slope_ms_per_test:.1f}ms per additional test")

overhead_groups = df.groupby('Total_Tests').agg(
    Runs=('Run_ID', 'count'),
    Median_Duration_ms=('Duration_ms', 'median'),
    Median_Duration_Per_Test_ms=('Duration_Per_Test_ms', 'median'),
    Median_P95_ms=('P95_Latency', 'median'),
).reset_index().sort_values('Total_Tests')

overhead_tex = "\\begin{table}[htbp]\n"
overhead_tex += "\\renewcommand{\\arraystretch}{1.2}\n"
overhead_tex += "\\centering\n"
overhead_tex += "\\scriptsize\n"
overhead_tex += "\\setlength{\\tabcolsep}{2.5pt}\n"
overhead_tex += (
    "\\caption{Operational overhead by suite size. "
    f"Total tests vs run duration: Pearson $r={pearson_r:.2f}$ ($p={pearson_p:.3f}$), "
    f"slope $+{slope_ms_per_test:.0f}$ ms/test.}}\n"
)
overhead_tex += "\\label{tab:overhead_scaling}\n"
overhead_tex += "\\begin{tabular}{rrrrr}\n"
overhead_tex += "\\toprule\n"
overhead_tex += "\\textbf{Suite} & \\textbf{Runs} & \\textbf{Med. s} & \\textbf{Med./Test ms} & \\textbf{P95 ms} \\\\\n"
overhead_tex += "\\midrule\n"
for _, row in overhead_groups.iterrows():
    overhead_tex += (
        f"{int(row['Total_Tests'])} & {int(row['Runs'])} & {row['Median_Duration_ms']/1000:.1f} & "
        f"{row['Median_Duration_Per_Test_ms']:.1f} & {row['Median_P95_ms']:.0f} \\\\\n"
    )
overhead_tex += "\\bottomrule\n"
overhead_tex += "\\end{tabular}\n"
overhead_tex += "\\setlength{\\tabcolsep}{6pt}\n"
overhead_tex += "\\end{table}\n"

with open(os.path.join(output_dir, "overhead_scaling.tex"), "w", encoding='utf-8') as f:
    f.write(overhead_tex)

# ============================================================
# 8. Gate Ablation
# ============================================================
print("\n8. GATE ABLATION")
print("-" * 50)

scenarios = {
    'Full 5D Gate': {'success_rate', 'research_context', 'p95_latency_ms', 'safety_rate', 'evidence_coverage'},
    'No Evidence Coverage': {'success_rate', 'research_context', 'p95_latency_ms', 'safety_rate'},
    'No Safety Dimension': {'success_rate', 'research_context', 'p95_latency_ms', 'evidence_coverage'},
    'Task Success + Latency Only': {'success_rate', 'p95_latency_ms'},
}

severe_mask = df.apply(has_severe_failure, axis=1)
severe_total = int(severe_mask.sum())
ablation_rows = []

for scenario_name, include_dims in scenarios.items():
    scenario_decisions = df.apply(lambda row: gate_decision(row, include_dims), axis=1)
    promote = int((scenario_decisions == 'PROMOTE').sum())
    hold = int((scenario_decisions == 'HOLD').sum())
    rollback = int((scenario_decisions == 'ROLLBACK').sum())
    severe_promoted = int(((scenario_decisions == 'PROMOTE') & severe_mask).sum())
    ablation_rows.append({
        'Scenario': scenario_name,
        'Promote': promote,
        'Hold': hold,
        'Rollback': rollback,
        'SeverePromoted': severe_promoted,
    })
    print(
        f"  {scenario_name}: promote={promote}, hold={hold}, rollback={rollback}, "
        f"severe_promoted={severe_promoted}/{severe_total}"
    )

ablation_rows.append({
    'Scenario': 'Traditional CI only (no behavioral gate)',
    'Promote': total_runs,
    'Hold': 0,
    'Rollback': 0,
    'SeverePromoted': severe_total,
})

gate_tex = "\\begin{table}[htbp]\n"
gate_tex += "\\renewcommand{\\arraystretch}{1.2}\n"
gate_tex += "\\centering\n"
gate_tex += "\\scriptsize\n"
gate_tex += "\\setlength{\\tabcolsep}{2.5pt}\n"
gate_tex += (
    "\\caption{Gate ablation analysis across 38 runs with the consolidated 5D gate. "
    "Severe-promoted counts indicate missed critical failures (lower is better).}\n"
)
gate_tex += "\\label{tab:gate_ablation}\n"
gate_tex += "\\begin{tabular}{p{1.7cm}rrrr}\n"
gate_tex += "\\toprule\n"
gate_tex += "\\textbf{Scenario} & \\textbf{Promote} & \\textbf{Hold} & \\textbf{Rollback} & \\textbf{Sev.} \\\\\n"
gate_tex += "\\midrule\n"
for row in ablation_rows:
    gate_tex += (
        f"{row['Scenario']} & {row['Promote']} & {row['Hold']} & "
        f"{row['Rollback']} & {row['SeverePromoted']} \\\\\n"
    )
gate_tex += "\\bottomrule\n"
gate_tex += "\\end{tabular}\n"
gate_tex += "\\setlength{\\tabcolsep}{6pt}\n"
gate_tex += "\\end{table}\n"

with open(os.path.join(output_dir, "gate_ablation.tex"), "w", encoding='utf-8') as f:
    f.write(gate_tex)

print("\n" + "=" * 70)
print("All statistical tables written to latex/tables/")
print("=" * 70)
