"""Score and compare manually captured AI card-generation benchmark runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.ai_benchmark import build_run_report, render_markdown_comparison


def _read_json(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str, value: object) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _score(args: argparse.Namespace) -> int:
    metadata = {
        "provider": args.provider,
        "model": args.model,
        "cost_usd": args.cost_usd,
        "latency_seconds": args.latency_seconds,
        "input_tokens": args.input_tokens,
        "output_tokens": args.output_tokens,
        "cache_status": args.cache_status,
    }
    human_review = None
    if args.correct_meanings is not None or args.natural_examples is not None:
        if args.correct_meanings is None or args.natural_examples is None:
            raise ValueError("provide both --correct-meanings and --natural-examples")
        human_review = {
            "correct_meanings": args.correct_meanings,
            "natural_examples": args.natural_examples,
        }
    report = build_run_report(
        _read_json(args.case), _read_json(args.cards), metadata, human_review
    )
    _write_json(args.output, report)
    print(render_markdown_comparison([report]))
    print(f"Saved benchmark report: {args.output}")
    return 0


def _compare(args: argparse.Namespace) -> int:
    table = render_markdown_comparison([_read_json(path) for path in args.reports])
    if args.output:
        Path(args.output).write_text(table + "\n", encoding="utf-8")
        print(f"Saved comparison: {args.output}")
    print(table)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    score = commands.add_parser("score", help="score one captured provider response")
    score.add_argument("--case", required=True, help="fixed benchmark-case JSON file")
    score.add_argument("--cards", required=True, help="generated cards JSON file")
    score.add_argument("--provider", required=True)
    score.add_argument("--model", required=True)
    score.add_argument("--cost-usd", type=float)
    score.add_argument("--latency-seconds", type=float)
    score.add_argument("--input-tokens", type=int)
    score.add_argument("--output-tokens", type=int)
    score.add_argument("--cache-status", choices=("miss", "hit", "unknown"), default="miss")
    score.add_argument("--correct-meanings", type=int)
    score.add_argument("--natural-examples", type=int)
    score.add_argument("--output", required=True, help="report output path")
    score.set_defaults(handler=_score)

    compare = commands.add_parser("compare", help="render a comparison table")
    compare.add_argument("reports", nargs="+", help="one or more score-report JSON files")
    compare.add_argument("--output", help="optional Markdown output path")
    compare.set_defaults(handler=_compare)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return args.handler(args)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Benchmark error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
