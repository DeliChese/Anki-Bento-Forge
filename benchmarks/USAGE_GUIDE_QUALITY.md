# Usage Guide V1 quality gate

Final review date: 2026-08-16. Model: `deepseek-v4-flash@disabled`, cache miss. The final evidence combines CJK round 2 with English round 5; later iterations changed only the English prompt/schema and deterministic post-parse normalization. Raw cards and provider reports remain local under ignored `benchmarks/runs/p1-05-*` directories.

| Language | Coverage / factory-ready | Usage rubric | Cost | Seconds/card |
| --- | ---: | ---: | ---: | ---: |
| Japanese | 5/5 · 5/5 | 5/5 | `$0.000487` | `1.60` |
| Chinese | 5/5 · 5/5 | 5/5 | `$0.000583` | `1.97` |
| Korean | 5/5 · 5/5 | 4/5 | `$0.000531` | `1.78` |
| English | 5/5 · 5/5 | 5/5 | `$0.000434` | `1.40` |
| **Total** | **20/20 · 20/20** | **19/20 (95%)** | **`$0.002035`** | **`1.69`** |

The gate passes: semantic review is above 90%, final-run cost is below `$0.005`, latency is below `3 seconds/card`, and no empty placeholder, repeated example, multi-collocation, or front-side Usage Guide content survives the final pipeline.

One Korean item, `약속하다`, is conservatively rejected because its generated note generalized time/place noun usage too broadly. The card remains editable in preview and demonstrates why P1-06 must stay advisory rather than auto-mutating content.

Prompt iteration also exposed and fixed two deterministic pipeline boundaries: inflected Japanese `質問を聞いて…` translated as “ask” is narrowly repaired to `質問して…`, and an explicitly empty optional collocation no longer crashes normalization. The English final run retained British `granted /ɡrɑːntɪd/` and omitted pseudo-collocations for an already-fixed phrase.

Recorded tuning spend before the final evidence was `$0.005351`, plus one failed English response whose usage was not persisted after the empty-string crash (bounded by the approved `$0.001` request cap). No card or collection data was written by benchmark runs.

## Anki 26.5 compatibility smoke

The bundled Anki 26.5 Python passed `scripts/smoke_anki_26_5.py` against a disposable collection for all four languages. The smoke removes the three fields to emulate a pre-P1-05 model, migrates them exactly once, imports and updates a note, uses Anki's native undo backend, rolls back only the newly added note, keeps one default card, and verifies rendered question/answer HTML is front-safe and back-visible. No personal profile was opened.
