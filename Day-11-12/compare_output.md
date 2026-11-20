## Local (qwen3.5:4b-q4_K_M) vs cloud (gpt-5.6-luna)

Source: eval_results_local.json, eval_results_cloud.json (judge gpt-5.4-mini). Values are mean ± 2×SE.

| Metric | n | Local | Cloud | Cloud minus local (per question) | Verdict |
|---|---|---|---|---|---|
| Faithfulness | 18 | 0.61 ± 0.11 | 0.63 ± 0.11 | +0.02 ± 0.14 | no clear difference |
| Answer Relevancy | 18 | 0.94 ± 0.09 | 0.93 ± 0.10 | -0.01 ± 0.12 | no clear difference |
| Contextual Relevancy | 18 | 0.18 ± 0.07 | 0.20 ± 0.07 | +0.02 ± 0.07 | no clear difference |
| Contextual Recall | 18 | 0.78 ± 0.18 | 0.72 ± 0.20 | -0.06 ± 0.08 | no clear difference |
| Contextual Precision | 18 | 0.81 ± 0.10 | 0.80 ± 0.13 | -0.01 ± 0.07 | no clear difference |

Source: pipeline_outputs_local.json, pipeline_outputs_cloud.json

| Run | Median generation time | Slowest | Avg completion tokens | Empty or failed answers | Unanswerable refused |
|---|---|---|---|---|---|
| Local | 56.7 s | 1010.7 s | 116 | 0 | 1 of 2 |
| Cloud | 1.1 s | 1.4 s | 52 | 0 | 1 of 2 |

Note: tokens_generated is the API's completion_tokens (includes reasoning tokens where reported).
