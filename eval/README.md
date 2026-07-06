# Evaluation Harness

Reproducible evaluation for Hybrid Observability AI, implementing whitepaper §6.
Scores the live agent on **quality** (grounding, tool-use), **robustness** (no
unwarranted refusal, prompt-injection resistance), and **performance** (latency,
convergence, tokens). Zero third-party dependencies.

## Placeholders (substitute for your environment)
The suite is **generic and reusable**: it models an enterprise where autonomous
application streams each chose their own best-of-breed observability stack, and the
assistant correlates a distributed transaction across all of them. Replace the
placeholders with real values from your deployment before running for meaningful
data-dependent scores:
`<TRANSACTION_ID>` (a correlation/trace/request id), `service-a`/`service-b` (real
service names), `region-x` (a real region). Behavior/robustness items (no unwarranted
refusal, injection resistance, "no data" grounding) are meaningful even without
substitution.

## Why grounding, not exact-match
Observability answers are **data-dependent** (they change with live telemetry), so
exact-match accuracy is the wrong target. We score **faithfulness/grounding** (does the
answer cite real evidence or clearly say none was found?) and **behavior** — the honest,
correct evaluation target for a production observability assistant.

## Run

```bash
# Point at the running app (local port-forward or in-cluster service)
BASE_URL=http://localhost:1800 python3 run_eval.py

# Enable LLM-as-judge on the SAME corporate model endpoint (no public egress)
BASE_URL=http://localhost:8000 \
OLLAMA_BASE_URL=https://ollama.internal \
JUDGE_MODEL=qwen3:14b \
python3 run_eval.py
```

Outputs `results.json` (machine-readable) and `report.md` (human-readable).

## Files
- `dataset.jsonl` — labeled question suite (quality / robustness / performance).
- `run_eval.py` — runner + automatic metrics + optional LLM-as-judge.
- `results.json`, `report.md` — generated.

## Metrics produced
- `answer_rate_pct`, `grounded_rate_pct`, `tool_use_accuracy_pct`, `pass_rate_pct`
- `unwarranted_refusal_pct`, `injection_leak_pct`
- `latency_mean_s`, `latency_p95_s`, `cache_latency_s`
- `judge_faithfulness_avg` (when judge enabled)

## Interop
`results.json` is intentionally simple to plug into **DeepEval** (as a custom metric
source), **RAGAS** (retrieval/faithfulness on the evidence set), or **Phoenix/Langfuse**
(import runs/spans). Instrument the app with OpenTelemetry for online tracing per §6.2.

## Extending
Add rows to `dataset.jsonl`:
```json
{"id":"q-new","category":"quality","question":"…","expect_tool":"…|null","expect_grounded":true,"deep":false,"note":"…"}
```
