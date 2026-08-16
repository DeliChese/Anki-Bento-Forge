# CJK output-quality baseline

Run date: 2026-08-16. Each corpus contains 20 fixed vocabulary items and uses
`deepseek-v4-flash` with thinking explicitly disabled, cache miss, and the
current built-in prompt/schema.

| Language | Coverage / factory-ready | Meaning review | Natural-example review | Cost/card | Seconds/card |
| --- | ---: | ---: | ---: | ---: | ---: |
| Japanese | 100% / 100% | 20/20 | 20/20 | $0.000052 | 1.03 |
| Chinese | 100% / 100% | 20/20 | 20/20 | $0.000068 | 1.27 |
| Korean | 100% / 100% | 20/20 | 20/20 | $0.000058 | 1.09 |

## Quality contract

- Japanese: contextual meanings, hiragana furigana, and particle/collocation
  agreement for polysemous words.
- Chinese: matching simplified/traditional forms, tone-marked pinyin, and the
  exact source word in its example.
- Korean: Revised Romanization without hyphens in the headword, with matching
  Vietnamese example translations.
- All CJK cards: target-level examples and translations that preserve the
  source sentence's meaning; missing core pronunciation is surfaced before
  import.

## Verified correction

The Japanese model repeatedly used `質問を聞きました` while translating it as
“ask a question”. The card pipeline now safely repairs that exact contradiction
to `質問しました` only when its paired translation means *ask*. Legitimate
“hear a question” cards are unchanged and covered by regression tests.

The completed final runs cost `$0.003571` in total. Retain these corpora and
their local run JSON as the quality gate before accepting later prompt, schema,
or model changes.
