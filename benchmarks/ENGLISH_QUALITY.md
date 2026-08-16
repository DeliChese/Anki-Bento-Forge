# English output-quality baseline

Run date: 2026-08-16. The fixed 20-item corpus supplies the intended Vietnamese
meaning for each headword, matching the normal batch flow when a source provides
meaning/context. It uses `deepseek-v4-flash` with thinking explicitly disabled
and a cache miss.

| Coverage / factory-ready | Meaning review | Natural-example review | Cost/card | Seconds/card |
| ---: | ---: | ---: | ---: | ---: |
| 100% / 100% | 20/20 | 20/20 | $0.000048 | 0.77 |

## Quality contract

- Every vocabulary card has British IPA before import; a missing `pronunciation`
  field is surfaced as an advisory warning.
- When a source meaning is supplied, the headword, `meaning`, both examples, and
  both Vietnamese translations must preserve that one sense and part of speech.
- Examples are natural, distinct, 5–12-word English sentences at the assigned
  CEFR level; usage notes are limited to genuinely helpful collocation/register
  guidance.

The completed reviewed run cost `$0.000966` in total. Retain this corpus and the
reviewed metrics above as the English quality gate before accepting later prompt,
schema, or model changes. Raw local run artifacts are intentionally gitignored.
