"""Collection-side application of an approved AI Deck Blueprint import plan."""

from __future__ import annotations

from .deck_blueprint import (
    create_blueprint_decks,
    read_blueprint_existing_cards,
    recheck_blueprint_import_plan,
)
from .model_lifecycle import ensure_model
from .srs_policy import needs_legacy_srs_migration, prepare_legacy_srs_model


def _apply_import(*args, **kwargs):
    """Load the Anki-bound importer only at the collection adapter boundary."""
    from .import_operations import apply_import

    return apply_import(*args, **kwargs)


def _prepare_legacy_model(collection, cfg):
    """Preserve existing multi-card behavior before template modernization."""
    model = collection.models.by_name(cfg["model_name"])
    if model is None:
        for old_name in cfg.get("old_model_names", ()):
            model = collection.models.by_name(old_name)
            if model is not None:
                break
    if needs_legacy_srs_migration(model):
        prepare_legacy_srs_model(collection, collection.models, model)


def apply_blueprint_import(
    collection,
    organization,
    plan,
    cfg,
    templates,
    css,
    build_qfmt,
    build_afmt,
):
    """Create/reuse approved decks and add planned notes in one CollectionOp.

    ``plan`` is add-only by contract.  Existing notes are never loaded for an
    update here, and audio work is deliberately absent from this first slice.
    """
    if any(
        entry.get("action") != "add"
        for group in plan.get("groups", ())
        for entry in group.get("entries", ())
    ):
        raise ValueError("Blueprint import plans must be add-only")

    latest_cards = read_blueprint_existing_cards(collection, cfg)
    safe_plan = recheck_blueprint_import_plan(
        plan,
        latest_cards,
        detect_key=cfg.get("detect_key", "front"),
    )
    _prepare_legacy_model(collection, cfg)
    ensure_model(
        collection.models,
        cfg,
        templates,
        css,
        build_qfmt,
        build_afmt,
        rename_primary_template=True,
        prune_extra_templates=False,
    )
    deck_result = create_blueprint_decks(collection, organization)

    report = {
        "created": list(deck_result.get("created", ())),
        "reused": list(deck_result.get("reused", ())),
        "added": 0,
        "added_note_ids": [],
        "errors": 0,
        "errors_detail": [],
        "deck_counts": {},
        "late_duplicates": int(safe_plan.get("late_duplicates", 0)),
        "late_conflicts": int(safe_plan.get("late_conflicts", 0)),
    }
    for group in safe_plan.get("groups", ()):
        deck_name = str(group.get("deck_name") or "")
        entries = list(group.get("entries") or ())
        if not deck_name or not entries:
            continue
        deck_id = deck_result["ids"].get(deck_name) or collection.decks.id(deck_name)
        group_report = _apply_import(
            collection,
            entries,
            cfg,
            deck_id,
            audio_tags={},
            is_cancelled=lambda: False,
        )
        report["added"] += int(group_report.get("added", 0))
        report["added_note_ids"].extend(group_report.get("added_note_ids", ()))
        report["errors"] += int(group_report.get("errors", 0))
        report["errors_detail"].extend(group_report.get("errors_detail", ()))
        report["deck_counts"][deck_name] = int(group_report.get("added", 0))
    report["errors_detail"] = report["errors_detail"][:10]
    return report
