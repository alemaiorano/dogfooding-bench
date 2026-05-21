# Walkthrough — Human Evaluation (Evaluator 2)

## Summary

Applied the **HUMAN_EVAL_PROTOCOL.md** rubric to all **60 rows** in [human_eval_sample.csv](file:///C:/Users/Usuario/Downloads/evaluator_2/human_eval_sample.csv), filling the `evaluator_2` column.

- **ACCEPT (1):** 54 responses
- **REJECT (0):** 6 responses

---

## Rejected Responses (evaluator_2 = 0)

| eval_id | Category | Criterion Failed | Rationale |
|---------|----------|-----------------|-----------|
| **E003** | ambiguity_noise | **TC** | User typed only "results" (ambiguous). Instead of asking for clarification, the response jumped to troubleshooting a specific error ("Failed to load simulation results"), answering a question the user didn't ask. |
| **E011** | market_context | **TC + FA** | User asked about macroeconomic headwinds for SaaS budgets. Response returned unrelated Indian stock market deep-learning papers. Neither addresses the question nor provides relevant sources. |
| **E037** | faithfulness | **TC** | User asks about 'Auto-Magic Viral Post Generator' (a feature that doesn't exist). Response dumps a generic documentation header about "AI Features User Guide v4.0.0" without ever stating the feature doesn't exist or addressing the question. |
| **E053** | multilingual | **TC + FA** | User asks for French translation of simulation results. Response claims "Estou processando a tradução… Você receberá em breve" — promising output it cannot deliver, as no simulation data was available. Fabricates an action that never happens. |
| **E056** | tool_orchestration | **TC** | User asks for sentiment analysis of last 5 simulations. Response dumps troubleshooting docs about stuck simulations and results not loading — completely unrelated content. |
| **E059** | workflow_fit | **TC** | User asks about operational effort to run simulations frequently (time, cost, team resources). Response gives micro-simulation output descriptions instead — doesn't address the operational effort question. |

---

## Borderline Cases Accepted

| eval_id | Category | Notes |
|---------|----------|-------|
| E010 | error_handling | Nonsensical math request ("square root of persona count / words"). Response asks for values — technically addresses the question. |
| E014 | out_of_domain | Python binary tree script — out of domain for a marketing assistant, but the rubric's 3 criteria (TC/FA/BS) are all met. |
| E020 | workflow_fit | Partial answer about internal approval integration. Mentions "aprovação interna" via export/webhooks — addresses ≥70% of the question. |
| E055 | multi_turn | Claims persona was set for the session — plausible capability, no evidence of fabrication. |
| E057 | data_query | Offers conversion rate (~15%) when success rate was asked — different metric, but good-faith effort with available data. |

---

## Validation

- Script parsed the CSV correctly (60 data rows, all filled)
- All 6 `REJECT` rows and 54 `ACCEPT` rows confirmed via post-write verification
