# AI model benchmark

> Status: active
> Authority: evidence index; acceptance thresholds live in `work_items/PERSONAL_ROADMAP.md`
> Read when: thay đổi model, prompt, schema hoặc quality gate

`japanese_vocab_20_v1.json` is the fixed first case: 20 Japanese vocabulary items sent through the same Xưởng/batch flow, with an empty deck and cache miss. Do not alter its terms while comparing models.

`chinese_vocab_20_v1.json` and `korean_vocab_20_v1.json` are the corresponding
CJK quality corpora. Their reviewed baseline and acceptance contract are in
[`CJK_QUALITY.md`](CJK_QUALITY.md).

`english_vocab_20_v1.json` is the fixed English vocabulary corpus. Its reviewed
baseline and IPA requirement are in [`ENGLISH_QUALITY.md`](ENGLISH_QUALITY.md).

The automated runner uses the provider configured in Bento Forge, retains only generated
cards and aggregate usage (never an API key), and writes all run reports plus a comparison:

```powershell
python scripts/benchmark_ai_models.py run `
  --case benchmarks/japanese_vocab_20_v1.json `
  --data-dir "C:\Users\<you>\AppData\Roaming\Anki2\<profile>\bento_forge" `
  --max-tokens 32768 `
  --variant deepseek-v4-flash@disabled `
  --variant deepseek-v4-flash@enabled `
  --variant deepseek-v4-pro@disabled
```

If provider metadata is missing but the key is already in the OS credential store, add
`--provider __custom__ --api-base https://api.deepseek.com/v1`. The key remains in the
credential store and is never accepted as a command-line argument.

Thinking-mode suffixes are optional and useful when a provider exposes one model in two
distinct modes. The command always bypasses Bento Forge's result cache so model latency
and cost remain comparable.

If a response was captured elsewhere, score it with the fallback command below:

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
