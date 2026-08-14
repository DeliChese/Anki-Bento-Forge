# Compatibility Matrix

`manifest.json` is the authoritative source for the Bento Forge version and the
minimum/maximum Anki versions. For 17.1.0 it declares exactly Anki 2.1.50; this
document explains that scope without widening it. A version
outside this matrix may run because the add-on detects missing public hooks and
disables only the affected feature, but it is not a supported release target.

Publication status is separate from the declared compatibility scope. The
17.1.0 release record remains pending until CI and real-Anki smoke evidence are
recorded in `RELEASE_CHECKLIST.md`.

| Anki | Bundled Python | Status | Evidence |
| --- | --- | --- | --- |
| 2.1.50 | 3.9 | Supported release target | Local isolated harness: four rounds × 383 tests passed on 2026-08-14; CI 3.9/3.11 and real-Anki smoke remain pending. |

## Not yet supported

- Anki 2.1.51 and later, including date-based releases, have no completed smoke
  test for import, reviewer hooks, combo mode, config migration, and undo.
- Python versions used only by CI are development-test environments; they do not
  expand the supported Anki runtime matrix.

## Release verification

Before widening `manifest.json` or publishing a release, run the isolated test
suite twice, then verify on a backed-up Anki profile:

1. Import a new note and update an existing note; confirm undo and audio result counts.
2. Review a combo card; confirm mode sync, letter-gap, and speed controls.
3. Start Anki after a config migration and confirm the prior configuration survives.
4. Confirm the add-on stays usable when an optional public hook is unavailable.

Anki warns that add-ons can break when Anki internals change; this matrix avoids
claiming compatibility that has not been exercised.
