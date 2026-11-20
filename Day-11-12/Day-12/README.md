# Day 12: Evaluation, where to find everything

Day 12 evaluates the Day 11 pipeline. The Day 12 brief says to run `eval_pipeline.py` and
`security_probe.py` next to `pipeline.py`, because they import `retrieve.py` and `generate.py`.
So all Day 12 scripts and result files are in the project root (`Day-11-12/`), and this folder
holds the written report and this index.

Pipeline evaluated: my own (qwen3.5:4b-q4_K_M, thinking off, 1000 characters, overlap 80, top_k 5).

The first Day 12 run used top_k 8. After an extra test showed top_k 5 gives the same 17/18 about twice as fast,
the final setup was switched to top_k 5 and every Day 12 step was run again. The top_k 8 results are kept
with `_k8` in the file name (for example `eval_results_local_k8.json`, `security_results_cloud_k8.json`,
`compare_output_k8.md`).

## Exercise to file map

| Exercise | Script | Result files (project root) |
|---|---|---|
| 3. Local evaluation with DeepEval (judge gpt-5.4-mini, 5 metrics) | `eval_pipeline.py` | `pipeline_outputs_local.json`, `eval_results_local.json` |
| 3. Earlier runs without chunk labels (kept to show judge variance) | `eval_pipeline.py` | `eval_results_local_nolabels.json`, `eval_results_local_nolabels_run2.json` |
| 4. Cloud run (gpt-5.6-luna) and its evaluation | `pipeline.py`, `eval_pipeline.py` | `pipeline_outputs_cloud.json`, `eval_results_cloud.json` |
| 4. Local vs cloud comparison (mean plus/minus 2 SE, per question difference) | `compare.py` | `compare_output.md` |
| 5. Security probes, 7 given attacks plus 4 own attacks, verdicts filled by hand | `security_probe.py` | `security_results_local.json`, `security_results_cloud.json` |
| 5. Garak (optional): DAN 11.0 and LatentInjectionReport, 41 prompts on the local model | `garak_ollama.yaml` | `garak_report.html` (open in a browser), `garak_report.jsonl` |
| 6. Evaluation report | | `Day-12/evaluation_report.md` |

## How to re-run

```powershell
uv run python eval_pipeline.py local                     # needs JUDGE_BASE_URL and AZURE_OPENAI_API_KEY in the shell
uv run python security_probe.py local
uv run python compare.py
```

Garak was installed with `uv tool install --python 3.12 garak` (separate from the project).
On this Windows machine Smart App Control blocked `garak.exe` and two compiled dependencies, so it was
run through the tool's own Python with the project's trusted versions of pydantic-core and jiter:

```powershell
$garakPy = "$(uv tool dir)\garak\Scripts\python.exe"
& $garakPy -m garak --config garak_ollama.yaml --spec probes.dan.Dan_11_0,probes.latentinjection.LatentInjectionReport
```

The Day 11 decision log is in `Day-11/decision_log.md`.
