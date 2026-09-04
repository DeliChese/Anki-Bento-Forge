# Compatibility Matrix

`manifest.json` is the authoritative source for the Bento Forge version and
Anki compatibility metadata. For 18.3.0 it declares Anki 2.1.50 through 26.5.
The installable manifest also maps those endpoints to Anki point versions `50`
and `260500`.

Publication status is separate from compatibility scope. The 18.3.0 release
record remains pending until CI and the manual GUI smoke checklist are recorded
in `RELEASE_CHECKLIST.md`.

| Anki | Bundled Python | Status | Evidence |
| --- | --- | --- | --- |
| 2.1.50 | 3.9 | Legacy compatibility target | Existing legacy adapters and regression suite remain in place; a fresh endpoint GUI smoke is still required before release. |
| 26.5 | 3.13.5 | Validated compatibility target | Real Anki runtime smoke passed on 2026-08-16 for add-on/UI/hook imports and Knowledge Basic/Cloze add, update, card generation, and scoped rollback; GUI smoke remains pending. |

## Compatibility design

### LTS Note Type contract

- Add-on release versions and Language Note Type schema versions are independent. Normal feature releases keep the `V18.3` Note Type names; a new name is allowed only for an intentional schema epoch with an explicit migration plan.
- Runtime migration is additive: Bento Forge may add required fields and refresh templates it owns, but it does not remove fields, unknown templates, cards, media, or SRS history.
- Historical model discovery is allowlist-only through `old_model_names`; broad/fuzzy model matching is not permitted.
- Content quality uses `Bento Quality Version`, separate from the Note Type name. New notes receive the current revision; old revisions expose the opt-in Reviewer upgrade with diff, audio choice, identity re-check, and Anki Undo.
- Legacy multi-card SRS compatibility may touch notes only after the user confirms and an Anki checkpoint is created.

- `Collection.update_note()` is preferred on current Anki so updates remain in
  the surrounding undo-aware operation; `Note.flush()` is retained only as a
  compatibility fallback for legacy runtimes.
- Query and collection work stays behind the public `QueryOp`/`CollectionOp`
  adapter, including the keyword-only QueryOp constructor used by Anki 26.5.
- Reviewer and overview integrations use public `gui_hooks` and degrade when an
  optional hook is unavailable.
- Language and Knowledge use separate note types; widening the runtime matrix
  does not migrate existing user notes.

## Remaining release verification

Before publishing, run the isolated suite twice and complete
`work_items/V18_SMOKE_PROFILE.md` on a copied profile:

1. Open Bento Forge from Tools and switch Language/Knowledge without losing drafts.
2. Import a new note and update an existing note; verify undo and result counts.
3. Review Language combo cards and verify public reviewer-hook controls.
4. Exercise Language TTS cancellation/offline handling and config migration.
5. Verify Knowledge strict validation, deck/model duplicate scope, history, and rollback.

The headless runtime smoke is reproducible with Anki's bundled Python:

```powershell
& '<Anki>/.venv/Scripts/python.exe' scripts/smoke_anki_26_5.py
```
