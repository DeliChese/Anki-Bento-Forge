# Compatibility Matrix

`manifest.json` is the authoritative source for the Bento Forge version and
Anki compatibility metadata. For 18.1.0 it declares Anki 2.1.50 through 26.5.
The installable manifest also maps those endpoints to Anki point versions `50`
and `260500`.

Publication status is separate from compatibility scope. The 18.1.0 release
record remains pending until CI and the manual GUI smoke checklist are recorded
in `RELEASE_CHECKLIST.md`.

| Anki | Bundled Python | Status | Evidence |
| --- | --- | --- | --- |
| 2.1.50 | 3.9 | Legacy compatibility target | Existing legacy adapters and regression suite remain in place; a fresh endpoint GUI smoke is still required before release. |
| 26.5 | 3.13.5 | Validated compatibility target | Real Anki runtime smoke passed on 2026-08-16 for add-on/UI/hook imports and Knowledge Basic/Cloze add, update, card generation, and scoped rollback; GUI smoke remains pending. |

## Compatibility design

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
