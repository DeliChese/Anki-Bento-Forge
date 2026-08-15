# AI model benchmark

`japanese_vocab_20_v1.json` is the fixed first case: 20 Japanese vocabulary items sent through the same Xưởng/batch flow, with an empty deck and cache miss. Do not alter its terms while comparing models.

For each model, retain only the generated card JSON (never an API key or source text), then score it:

```powershell
python scripts/benchmark_ai_models.py score `
  --case benchmarks/japanese_vocab_20_v1.json `
  --cards path\to\generated-cards.json `
  --provider deepseek --model deepseek-chat `
  --cost-usd 0.001221 --latency-seconds 12.4 `
  --input-tokens 0 --output-tokens 0 --cache-status miss `
  --correct-meanings 20 --natural-examples 19 `
  --output benchmarks/runs/deepseek-chat.json
```

`generated-cards.json` may be a JSON array, an object containing `cards`, or a model JSON wrapper such as `{"items": [...]}`. If the provider only reports a running cumulative cost, record the delta from the immediately preceding request, not the cumulative value.

Review all 20 cards before filling the two human counts:

- `correct-meanings`: cards whose Vietnamese meaning is correct for the headword.
- `natural-examples`: cards whose first example is grammatical, natural, and fits the headword.

The automated result measures only factory readiness: coverage, required fields, duplicates, and deterministic warnings. It does not claim that a translation or example is semantically correct. A run becomes decision-ready only when coverage and factory-ready rate are both at least 95%, and both manual rates are at least 90%.

Compare completed runs:

```powershell
python scripts/benchmark_ai_models.py compare benchmarks/runs/gemini-flash.json benchmarks/runs/deepseek-chat.json benchmarks/runs/deepseek-reasoner.json
```

Start with Gemini Flash, DeepSeek Chat, then DeepSeek Reasoner. Use 20 items for Chat/Flash; use 10–20 for Reasoner if its output reaches the token limit.
