"""Use case for creating and migrating Bento Forge Anki note types.

The module is intentionally independent of ``aqt`` and ``anki`` imports.  The
dialog supplies Anki's model manager as an adapter, which keeps this critical
data operation unit-testable and prevents UI code from owning model mutation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable


_SPECIAL_TEMPLATE_FIELDS = {"FrontSide", "Tags", "Deck", "Subdeck", "Card", "Type"}
LTS_NOTE_TYPE_SCHEMA = "18.3"


@dataclass(frozen=True)
class ModelLifecycleResult:
    model: object
    existed: bool
    had_extra_templates: bool
    migrated_from: str = ""
    preserved_extra_templates: int = 0


def collect_template_fields(templates: Iterable[Callable[[], str]]) -> set:
    """Return Anki field names referenced by card templates."""
    fields = set()
    for template in templates:
        try:
            html = template()
        except Exception:
            continue
        for match in re.finditer(r"\{\{([#^/]?)([^{}\n]+?)\}\}", html):
            name = match.group(2).strip()
            if name.startswith(("type:", "cloze:")):
                name = name.split(":", 1)[1].strip()
            if name and name not in _SPECIAL_TEMPLATE_FIELDS:
                fields.add(name)
    return fields


def get_or_migrate_model(model_manager, cfg):
    """Find the current model or migrate one approved historical name."""
    model = model_manager.by_name(cfg["model_name"])
    if model:
        return model
    for old_name in cfg.get("old_model_names", []):
        model = model_manager.by_name(old_name)
        if model:
            model["name"] = cfg["model_name"]
            model_manager.save(model)
            return model
    return None


def _model_before_migration(model_manager, cfg):
    """Return the model and its approved legacy source without broad matching."""
    model = model_manager.by_name(cfg["model_name"])
    if model:
        return model, ""
    for old_name in cfg.get("old_model_names", []):
        model = model_manager.by_name(old_name)
        if model:
            model["name"] = cfg["model_name"]
            model_manager.save(model)
            return model, old_name
    return None, ""


def _ensure_fields(model_manager, model, names):
    existing = {field["name"] for field in model["flds"]}
    for name in names:
        if name and name not in existing:
            model_manager.add_field(model, model_manager.new_field(name))
            existing.add(name)


def ensure_model(
    model_manager,
    cfg,
    templates,
    css: str,
    build_qfmt: Callable,
    build_afmt: Callable,
    *,
    rename_primary_template: bool,
    prune_extra_templates: bool = False,
    allow_destructive_template_prune: bool = False,
) -> ModelLifecycleResult:
    """Create or update a model under the LTS additive-migration contract.

    Fields are only added. Known Bento templates receive the current layout;
    unknown/user-created templates are never overwritten or removed by normal
    startup/import. Destructive pruning requires an explicit opt-in parameter
    kept only for controlled maintenance tools.
    """
    model, migrated_from = _model_before_migration(model_manager, cfg)
    existed = model is not None
    template_count = len(templates) // 2
    if not model:
        model = model_manager.new(cfg["model_name"])
        for name in cfg["all_fields"]:
            model_manager.add_field(model, model_manager.new_field(name))
        for index in range(template_count):
            template = model_manager.new_template(cfg["template_names"][index])
            template["qfmt"] = build_qfmt(cfg, templates, index * 2)
            template["afmt"] = build_afmt(cfg, templates, index * 2 + 1)
            model_manager.add_template(model, template)
        model["css"] = css
        model_manager.add(model)
        return ModelLifecycleResult(model=model, existed=False, had_extra_templates=False)

    _ensure_fields(model_manager, model, cfg["all_fields"])
    _ensure_fields(model_manager, model, collect_template_fields(templates))
    model["css"] = css
    had_extra = len(model["tmpls"]) > template_count
    original_templates = list(model["tmpls"])
    target_names = list(cfg.get("template_names") or [])
    legacy_aliases = dict(cfg.get("legacy_template_aliases") or {})
    for index in range(template_count):
        target_name = target_names[index]
        template = next(
            (item for item in model["tmpls"] if item.get("name") == target_name),
            None,
        )
        # Legacy ownership is name-based as well: position alone must never
        # authorize overwriting a user-created template.
        if template is None:
            template = next(
                (
                    item for item in original_templates
                    if legacy_aliases.get(item.get("name")) == target_name
                ),
                None,
            )
        if template is None:
            template = model_manager.new_template(target_name)
            model_manager.add_template(model, template)
        template["name"] = target_name
        template["qfmt"] = build_qfmt(cfg, templates, index * 2)
        template["afmt"] = build_afmt(cfg, templates, index * 2 + 1)
    if prune_extra_templates and allow_destructive_template_prune:
        while len(model["tmpls"]) > template_count:
            model_manager.remove_template(model, model["tmpls"][-1])
    model_manager.save(model)
    return ModelLifecycleResult(
        model=model,
        existed=True,
        had_extra_templates=had_extra,
        migrated_from=migrated_from,
        preserved_extra_templates=max(0, len(model["tmpls"]) - template_count),
    )
