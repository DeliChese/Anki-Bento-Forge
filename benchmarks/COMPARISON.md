| Provider / model | Ready | Coverage | Factory-ready | Auto score | Human score | Cost/card | Seconds/card |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| deepseek / deepseek-v4-flash@disabled | yes | 100.0% | 100.0% | 100.0 | 100.0 | $0.000056 | 1.05 |
| deepseek / deepseek-v4-flash@enabled | yes | 100.0% | 100.0% | 100.0 | 100.0 | $0.000163 | 3.71 |
| deepseek / deepseek-v4-pro@disabled | yes | 100.0% | 100.0% | 100.0 | 100.0 | $0.000175 | 1.51 |

## Decision

- Default for Japanese vocabulary card generation: `deepseek-v4-flash` with thinking
  explicitly `disabled`, using the current default prompt and schema.
- Acceptance gates for later prompt/model changes: coverage and factory-ready at least
  95%; meaning accuracy and example naturalness at least 90%; cost at most `$0.000200`
  per expected card; latency at most `4.00` seconds per expected card on this case.
- All three completed runs passed every gate. Flash non-thinking was selected because it
  matched the two slower configurations at 100% quality while costing 65–68% less and
  completing 31–72% faster.
- Completed-run cost was `$0.007902`. One rejected Flash-thinking attempt hit the old
  8,192-token output limit before these runs; its estimated additional cost was about
  `$0.002479`, keeping the full benchmark near `$0.010381`.
- This is a small personal corpus, so the decision applies to the weekly Japanese vocab
  flow only. Re-run this fixed case before accepting a prompt/schema/model change.
