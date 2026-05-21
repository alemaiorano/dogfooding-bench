import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import numpy as np
import seaborn as sns

sns.set_theme(style="whitegrid")
plt.rcParams.update({
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
})

# Use relative paths from the data/ directory
script_dir = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(script_dir, "decision-log.csv")
output_dir_latex = os.path.join(script_dir, "..", "latex", "tables")
output_dir_figs = os.path.join(script_dir, "..", "latex", "figures")

os.makedirs(output_dir_latex, exist_ok=True)
os.makedirs(output_dir_figs, exist_ok=True)

# Load data
df = pd.read_csv(data_file)
df = df.sort_values(by="Release").reset_index(drop=True)
df['Run_ID'] = df.index + 1

# Parse numeric columns
for col in ['Success_Rate', 'Research_Context', 'Safety_Rate', 'Evidence_Coverage']:
    df[f'{col}_Num'] = df[col].str.rstrip('%').astype(float)
df['Task_Success_Rate_Num'] = df['Success_Rate_Num']

# ============================================================
# 1. LaTeX Decision Log Table (consolidated 5 dimensions)
# ============================================================
latex_table = "\\begin{table*}[htbp]\n"
latex_table += "\\renewcommand{\\arraystretch}{1.2}\n"
latex_table += "\\centering\n"
latex_table += "\\small\n"
latex_table += "\\setlength{\\tabcolsep}{3.5pt}\n"
latex_table += "\\caption{Complete evaluation trace results across 38 runs with 5 quality dimensions (Task Success Rate consolidates the legacy Success/Helpful overlap).}\n"
latex_table += "\\label{tab:decision_log}\n"
latex_table += "\\begin{tabular}{rrrrrrrl}\n"
latex_table += "\\toprule\n"
latex_table += "\\textbf{Run} & \\textbf{Tests} & \\textbf{Task Success} & \\textbf{P95 (ms)} & "
latex_table += "\\textbf{Context} & \\textbf{Safety} & \\textbf{Evidence} & \\textbf{Decision} \\\\\n"
latex_table += "\\midrule\n"

for _, row in df.iterrows():
    ts = str(row['Success_Rate']).replace('%', '\\%')
    rc = str(row['Research_Context']).replace('%', '\\%')
    sa = str(row['Safety_Rate']).replace('%', '\\%')
    ev = str(row['Evidence_Coverage']).replace('%', '\\%')
    dec = row['Decision']
    if dec == 'ROLLBACK':
        dec = '\\textbf{ROLLBACK}'
    latex_table += f"{row['Run_ID']} & {row['Total_Tests']} & {ts} & {row['P95_Latency']} & {rc} & {sa} & {ev} & {dec} \\\\\n"

latex_table += "\\bottomrule\n"
latex_table += "\\end{tabular}\n"
latex_table += "\\setlength{\\tabcolsep}{6pt}\n"
latex_table += "\\end{table*}\n"

with open(os.path.join(output_dir_latex, "decision_log.tex"), "w") as f:
    f.write(latex_table)
print(f"Table: decision_log.tex")

# ============================================================
# 2. Quality Thresholds Table
# ============================================================
thresholds_tex = "\\begin{table}[htbp]\n"
thresholds_tex += "\\renewcommand{\\arraystretch}{1.1}\n"
thresholds_tex += "\\centering\n"
thresholds_tex += "\\small\n"
thresholds_tex += "\\setlength{\\tabcolsep}{3pt}\n"
thresholds_tex += "\\caption{Quality gate dimensions and acceptance thresholds.}\n"
thresholds_tex += "\\label{tab:quality_thresholds}\n"
thresholds_tex += "\\begin{tabular}{p{2.3cm}p{1.8cm}p{1.6cm}}\n"
thresholds_tex += "\\toprule\n"
thresholds_tex += "\\textbf{Dimension} & \\textbf{Threshold} & \\textbf{Direction} \\\\\n"
thresholds_tex += "\\midrule\n"
thresholds_tex += "Task Success Rate & $\\geq 80\\%$ & Higher \\\\\n"
thresholds_tex += "Research Context Preservation & $\\geq 90\\%$ & Higher \\\\\n"
thresholds_tex += "P95 Latency & $< 15{,}000$ ms & Lower \\\\\n"
thresholds_tex += "Safety Pass Rate & $\\geq 95\\%$ & Higher \\\\\n"
thresholds_tex += "Evidence Coverage & $\\geq 80\\%$ & Higher \\\\\n"
thresholds_tex += "\\bottomrule\n"
thresholds_tex += "\\end{tabular}\n"
thresholds_tex += "\\setlength{\\tabcolsep}{6pt}\n"
thresholds_tex += "\\end{table}\n"

with open(os.path.join(output_dir_latex, "quality_thresholds.tex"), "w") as f:
    f.write(thresholds_tex)
print(f"Table: quality_thresholds.tex")

# ============================================================
# 3. Metric Operationalization Table
# ============================================================
metric_rows = [
    (
        "Task Success Rate",
        "Per-test validation over route, semantic, and issue-free completion checks; consolidates task success and response utility",
        "passed-tests / total-tests",
        "Rubric-design sensitivity; mitigated by issue taxonomy, question-bank snapshots, and human calibration (Sec.~\\ref{sec:discussion})",
    ),
    (
        "Research Context Preservation",
        "Multi-turn research tests with conversation history and expected research routing",
        "context-preserved / research-tests-with-history",
        "Saturates at 100\\% in stable periods (observed throughout this study); mitigated by harder follow-up injection",
    ),
    (
        "P95 Latency",
        "End-to-end wall-clock latency per test from evaluator trace",
        "95th percentile (ms)",
        "Inflated by suite growth and rate limits; mitigated by per-test runtime reporting",
    ),
    (
        "Safety Pass Rate",
        "Adversarial/boundary behavior via guardrail routing and safety issue checks",
        "safety-tests-passing / safety-tests",
        "May miss novel attacks; mitigated by adversarial tier expansion and spot checks",
    ),
    (
        "Evidence Coverage",
        "Retrieval-required tests with explicit citation signal in response text or source IDs",
        "web-tests-with-evidence / web-tests",
        "Citation heuristic can be gamed; mitigated by source-ID tracking and low-confidence audits",
    ),
]

metric_tex = "\\begin{table*}[t]\n"
metric_tex += "\\renewcommand{\\arraystretch}{1.1}\n"
metric_tex += "\\centering\n"
metric_tex += "\\small\n"
metric_tex += "\\setlength{\\tabcolsep}{3pt}\n"
metric_tex += "\\caption{Operationalization of the five quality dimensions used by the release gate. Task Success Rate consolidates the former separate Success and Helpful dimensions, which exhibited Spearman $\\rho = 1.00$ across all 38 evaluation runs, indicating complete construct overlap.}\n"
metric_tex += "\\label{tab:metric_operationalization}\n"
metric_tex += "\\begin{tabular}{p{2.4cm}p{4.8cm}p{3.1cm}p{4.9cm}}\n"
metric_tex += "\\toprule\n"
metric_tex += "\\textbf{Dimension} & \\textbf{Automated signal} & \\textbf{Scoring rule} & \\textbf{Known limitation and mitigation} \\\\\n"
metric_tex += "\\midrule\n"

for dim, signal, rule, mitigation in metric_rows:
    metric_tex += f"{dim} & {signal} & {rule} & {mitigation} \\\\\n"

metric_tex += "\\bottomrule\n"
metric_tex += "\\end{tabular}\n"
metric_tex += "\\setlength{\\tabcolsep}{6pt}\n"
metric_tex += "\\end{table*}\n"

with open(os.path.join(output_dir_latex, "metric_operationalization.tex"), "w") as f:
    f.write(metric_tex)
print(f"Table: metric_operationalization.tex")

# ============================================================
# 4. Comparison Table (Dogfooding vs. Traditional Testing)
# ============================================================
comparison_tex = "\\begin{table}[htbp]\n"
comparison_tex += "\\renewcommand{\\arraystretch}{1.2}\n"
comparison_tex += "\\centering\n"
comparison_tex += "\\small\n"
comparison_tex += "\\setlength{\\tabcolsep}{3pt}\n"
comparison_tex += "\\caption{Complementary coverage: traditional testing vs.\\ automated self-testing.}\n"
comparison_tex += "\\label{tab:comparison}\n"
comparison_tex += "\\begin{tabular}{p{3.5cm}ccc}\n"
comparison_tex += "\\toprule\n"
comparison_tex += "\\textbf{Aspect} & \\textbf{U/I} & \\textbf{E2E} & \\textbf{Self-Test} \\\\\n"
comparison_tex += "\\midrule\n"
comparison_tex += "Deterministic logic & \\checkmark & \\checkmark & -- \\\\\n"
comparison_tex += "API contracts & \\checkmark & \\checkmark & -- \\\\\n"
comparison_tex += "UI flow validation & -- & \\checkmark & -- \\\\\n"
comparison_tex += "Hallucination detection & -- & -- & \\checkmark \\\\\n"
comparison_tex += "Context preservation & -- & -- & \\checkmark \\\\\n"
comparison_tex += "Safety alignment & -- & -- & \\checkmark \\\\\n"
comparison_tex += "Evidence citation & -- & -- & \\checkmark \\\\\n"
comparison_tex += "Latency regression & -- & Partial & \\checkmark \\\\\n"
comparison_tex += "Multi-turn coherence & -- & -- & \\checkmark \\\\\n"
comparison_tex += "\\bottomrule\n"
comparison_tex += "\\end{tabular}\n"
comparison_tex += "\\setlength{\\tabcolsep}{6pt}\n"
comparison_tex += "\\end{table}\n"

with open(os.path.join(output_dir_latex, "comparison.tex"), "w") as f:
    f.write(comparison_tex)
print(f"Table: comparison.tex")

# ============================================================
# 5. Task Success Rate Trend (with ROLLBACK markers)
# ============================================================
fig, ax = plt.subplots(figsize=(3.5, 2.6))

colors = df['Decision'].map({
    'PROMOTE': '#2ca02c',
    'HOLD': '#ff7f0e',
    'ROLLBACK': '#d62728'
})

ax.plot(df['Run_ID'], df['Task_Success_Rate_Num'], linestyle='-', color='#1f77b4', linewidth=1.5, zorder=1)
ax.scatter(df['Run_ID'], df['Task_Success_Rate_Num'], c=colors, s=50, zorder=2, edgecolors='black', linewidth=0.5)
ax.axhline(y=80, color='r', linestyle='--', alpha=0.7, label='Threshold (80%)')

promote_patch = mpatches.Patch(color='#2ca02c', label='PROMOTE')
rollback_patch = mpatches.Patch(color='#d62728', label='ROLLBACK')
ax.legend(handles=[promote_patch, rollback_patch, plt.Line2D([0], [0], color='r', linestyle='--', label='Threshold')], fontsize=8)

ax.set_title('Task Success Rate Across 38 Evaluation Runs', fontsize=10)
ax.set_xlabel('Run ID (Sequential)', fontsize=9)
ax.set_ylabel('Task Success Rate (%)', fontsize=9)
ax.set_ylim(75, 102)
ax.set_yticks(np.arange(75, 103, 5))
ax.set_xticks(range(1, len(df) + 1, 4))
plt.tight_layout()
plt.savefig(os.path.join(output_dir_figs, "success_rate.pdf"), dpi=300)
print(f"Figure: success_rate.pdf")
plt.close()

# ============================================================
# 6. Latency Distribution (Box Plot by Question Bank Phase)
# ============================================================
fig, ax = plt.subplots(figsize=(3.5, 2.8))

# Define phases by total tests
def get_phase(total):
    if total <= 13:
        return 'Debug (13)'
    elif total <= 59:
        return 'Core (59)'
    elif total <= 88:
        return 'Core+Expanded (86-88)'
    elif total <= 106:
        return 'Extended (106)'
    else:
        return 'Full (133)'

df['Phase'] = df['Total_Tests'].apply(get_phase)
phase_order = ['Debug (13)', 'Core (59)', 'Core+Expanded (86-88)', 'Extended (106)', 'Full (133)']
df['Phase'] = pd.Categorical(df['Phase'], categories=phase_order, ordered=True)

phase_label_map = {
    'Debug (13)': 'D13',
    'Core (59)': 'C59',
    'Core+Expanded (86-88)': 'C86-88',
    'Extended (106)': 'C106',
    'Full (133)': 'C133'
}
df['Phase_Label'] = df['Phase'].map(phase_label_map)

sns.boxplot(data=df, x='Phase_Label', y='P95_Latency', hue='Phase_Label', legend=False, ax=ax, palette='Set2')
ax.axhline(y=15000, color='r', linestyle='--', alpha=0.7, label='Threshold (15,000ms)')
ax.set_title('P95 Latency by Suite Phase', fontsize=10)
ax.set_xlabel('Suite Phase', fontsize=9)
ax.set_ylabel('P95 Latency (ms)', fontsize=9)
ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig(os.path.join(output_dir_figs, "latency_distribution.pdf"), dpi=300)
print(f"Figure: latency_distribution.pdf")
plt.close()

# ============================================================
# 7. Multi-Dimension Evolution (5 KPIs over time)
# ============================================================
fig, axes = plt.subplots(2, 3, figsize=(7.2, 4.4), sharex=True)

metrics = [
    ('Task_Success_Rate_Num', 'Task Success Rate (%)', 80, '#1f77b4'),
    ('Research_Context_Num', 'Research Context Preservation (%)', 90, '#2ca02c'),
    ('P95_Latency', 'P95 Latency (ms)', 15000, '#d62728'),
    ('Safety_Rate_Num', 'Safety Pass Rate (%)', 95, '#ff7f0e'),
    ('Evidence_Coverage_Num', 'Evidence Coverage (%)', 80, '#8c564b'),
]

for ax, (col, title, threshold, color) in zip(axes.flat, metrics):
    ax.plot(df['Run_ID'], df[col], marker='.', color=color, linewidth=1.2, markersize=4)
    ax.axhline(y=threshold, color='r', linestyle='--', alpha=0.5, linewidth=0.8)
    ax.set_title(title, fontsize=9)
    ax.set_ylabel(title.split('(')[1].rstrip(')') if '(' in title else '', fontsize=8)

# Hide the 6th panel (unused in 5D consolidated gate).
axes.flat[len(metrics)].axis('off')

for ax in axes[1]:
    ax.set_xlabel('Run ID', fontsize=8)

plt.suptitle('Evolution of Five Quality Dimensions Across 38 Runs', fontsize=11, y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(output_dir_figs, "quality_evolution.pdf"), dpi=300, bbox_inches='tight')
print(f"Figure: quality_evolution.pdf")
plt.close()

# ============================================================
# 8. Decision Flowchart (simple text-based TikZ generation)
# ============================================================
tikz_flowchart = r"""\begin{figure}[htbp]
\centering
\resizebox{\columnwidth}{!}{
\begin{tikzpicture}[
    node distance=1.2cm,
    box/.style={draw, rounded corners, minimum width=2.8cm, minimum height=0.8cm, align=center, font=\small, drop shadow},
    decision/.style={draw, diamond, aspect=2.5, minimum width=2cm, align=center, font=\small, drop shadow},
    arrow/.style={->, >=stealth, thick}
]

\node[box, fill=blue!10] (eval) {Run Evaluation\\(133 scenarios)};
\node[decision, below=of eval, fill=yellow!10] (check) {All 5 dims\\meet targets?};
\node[decision, below left=1.5cm and 1.5cm of check, fill=orange!10] (severe) {Any dim\\$< 70\%$ target?};
\node[box, below right=1.5cm and 1.5cm of check, fill=green!20] (promote) {\textbf{PROMOTE}};
\node[box, below=of severe, fill=red!20] (rollback) {\textbf{ROLLBACK}};
\node[box, right=of rollback, fill=yellow!20] (hold) {\textbf{HOLD}};

\draw[arrow] (eval) -- (check);
\draw[arrow] (check) -- node[right, font=\scriptsize] {Yes} (promote);
\draw[arrow] (check) -- node[above, font=\scriptsize] {No} (severe);
\draw[arrow] (severe) -- node[left, font=\scriptsize] {Yes} (rollback);
\draw[arrow] (severe) -- node[above, font=\scriptsize] {No} (hold);

\end{tikzpicture}
}
\caption{Decision flowchart: PROMOTE, HOLD, or ROLLBACK based on five quality dimensions.}
\label{fig:decision_flowchart}
\end{figure}
"""

with open(os.path.join(output_dir_figs, "decision_flowchart.tex"), "w") as f:
    f.write(tikz_flowchart)
print(f"Figure: decision_flowchart.tex (TikZ)")

print("\nAll figures and tables generated successfully.")
