"""Score and compare manually captured AI card-generation benchmark runs."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def _read_json(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str, value: object) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _score(args: argparse.Namespace) -> int:
    from utils.ai_benchmark import build_run_report, render_markdown_comparison

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
    from utils.ai_benchmark import render_markdown_comparison

    table = render_markdown_comparison([_read_json(path) for path in args.reports])
    if args.output:
        Path(args.output).write_text(table + "\n", encoding="utf-8")
        print(f"Saved comparison: {args.output}")
    print(table)
    return 0


def _parse_variant(value: str) -> tuple[str, str | None]:
    """Parse MODEL or MODEL@enabled/disabled without restricting provider names."""
    model, marker, thinking = value.rpartition("@")
    if not marker:
        model, thinking = value, None
    elif thinking not in ("enabled", "disabled"):
        raise ValueError("variant thinking mode must be enabled or disabled")
    model = model.strip()
    if not model:
        raise ValueError("variant model cannot be empty")
    return model, thinking


def _safe_run_name(model: str, thinking: str | None) -> str:
    suffix = f"-{thinking}" if thinking else ""
    return re.sub(r"[^a-z0-9._-]+", "-", f"{model}{suffix}".lower()).strip("-")


def _run_one(case: dict, cfg: dict, variant: str) -> tuple[list[dict], dict]:
    """Run the fixed case through the same prompt/transport/parser as batch import."""
    from utils.ai_extractor import (
        _apply_reasoning_effort,
        _calculate_cost,
        _http_post_json,
    )
    from utils.ai_response_guard import enable_deepseek_json_output, get_final_model_content
    from utils.ai_output_repairs import repair_vocabulary_cards
    from utils.ai_response_parser import parse_ai_json_with_comment
    from utils.batch_processor import _build_batch_user_prompt
    from utils.prompt_config import get_system_prompt

    model, thinking = _parse_variant(variant)
    runtime_cfg = dict(cfg, model=model)
    words = case.get("source_items")
    if not isinstance(words, list) or not words:
        words = [{"front": term} for term in case["expected_terms"]]
    kind = "grammar" if case.get("grammar") else "vocab"
    messages = [
        {"role": "system", "content": get_system_prompt(case["language"], kind)},
        {
            "role": "user",
            "content": _build_batch_user_prompt(
                words, case["language"], [], "", 1, 1, bool(case.get("grammar"))
            ),
        },
    ]
    payload = {
        "model": model,
        "messages": messages,
        "temperature": runtime_cfg.get("temperature", 0.3),
        "max_tokens": runtime_cfg.get("max_tokens", 8192),
    }
    _apply_reasoning_effort(payload, runtime_cfg)
    enable_deepseek_json_output(payload, runtime_cfg)
    if thinking:
        payload["thinking"] = {"type": thinking}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {runtime_cfg['api_key']}",
    }
    started = time.monotonic()
    body = _http_post_json(
        f"{runtime_cfg['api_base'].rstrip('/')}/chat/completions",
        payload,
        headers,
        timeout=600 if thinking == "enabled" else 300,
    )
    latency = time.monotonic() - started
    response = json.loads(body)
    if not response.get("choices"):
        raise RuntimeError("provider returned no choices")
    content = get_final_model_content(response["choices"][0])
    cards, _comment = parse_ai_json_with_comment(content)
    if not case.get("grammar"):
        cards = repair_vocabulary_cards(cards, case["language"])
    usage = response.get("usage") or {}
    token_info = _calculate_cost(
        model,
        int(usage.get("prompt_tokens") or 0),
        int(usage.get("completion_tokens") or 0),
        usage.get("cost"),
    )
    metadata = {
        "provider": runtime_cfg.get("provider") or "custom",
        "model": f"{model}@{thinking}" if thinking else model,
        "cost_usd": token_info["total_cost"],
        "latency_seconds": round(latency, 4),
        "input_tokens": token_info["prompt_tokens"],
        "output_tokens": token_info["completion_tokens"],
        "cache_status": "miss",
    }
    return cards, metadata


def _run(args: argparse.Namespace) -> int:
    if args.data_dir:
        os.environ["BENTO_FORGE_DATA_DIR"] = str(Path(args.data_dir).resolve())

    from utils.ai_benchmark import build_run_report, render_markdown_comparison, validate_case
    from utils.ai_extractor import get_api_config, get_api_key_for_provider

    case = _read_json(args.case)
    normalized = validate_case(case)
    if isinstance(case, dict) and isinstance(case.get("source_items"), list):
        normalized["source_items"] = case["source_items"]
    cfg = get_api_config()
    if args.api_base:
        cfg["api_base"] = args.api_base.strip().rstrip("/")
    if args.provider:
        cfg["provider"] = args.provider
    if args.max_tokens:
        cfg["max_tokens"] = args.max_tokens
    if not cfg.get("api_key"):
        cfg["api_key"] = get_api_key_for_provider(
            cfg.get("provider", ""), cfg.get("api_base", "")
        )
    if not cfg.get("api_key") and "localhost" not in cfg.get("api_base", ""):
        raise ValueError("active Bento Forge provider has no usable API key")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    for variant in args.variant:
        model, thinking = _parse_variant(variant)
        print(f"Running {model}" + (f" ({thinking} thinking)" if thinking else "") + "...")
        cards, metadata = _run_one(normalized, cfg, variant)
        name = _safe_run_name(model, thinking)
        _write_json(str(output_dir / f"{name}-cards.json"), cards)
        report = build_run_report(normalized, cards, metadata)
        _write_json(str(output_dir / f"{name}.json"), report)
        reports.append(report)

    comparison = render_markdown_comparison(reports)
    comparison_path = Path(args.comparison)
    comparison_path.parent.mkdir(parents=True, exist_ok=True)
    comparison_path.write_text(comparison + "\n", encoding="utf-8")
    print(comparison)
    print(f"Saved {len(reports)} run(s) and comparison: {comparison_path}")
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

    run = commands.add_parser("run", help="call configured provider and capture benchmark runs")
    run.add_argument("--case", required=True, help="fixed benchmark-case JSON file")
    run.add_argument(
        "--variant",
        action="append",
        required=True,
        help="model, optionally suffixed with @enabled or @disabled thinking mode",
    )
    run.add_argument("--data-dir", help="profile bento_forge directory containing ai_config.json")
    run.add_argument("--provider", help="override provider id used to select a stored credential")
    run.add_argument("--api-base", help="override the configured OpenAI-compatible API base")
    run.add_argument(
        "--max-tokens",
        type=int,
        choices=range(1, 384001),
        metavar="N",
        help="override output limit for benchmark requests",
    )
    run.add_argument("--output-dir", default="benchmarks/runs")
    run.add_argument("--comparison", default="benchmarks/COMPARISON.md")
    run.set_defaults(handler=_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return args.handler(args)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"Benchmark error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
