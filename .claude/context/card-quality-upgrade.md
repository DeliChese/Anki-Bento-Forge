# Card Quality Upgrade — task contract

## Scope

Opt-in Reviewer upgrade for one managed Language note: ask AI for exactly one
current-schema candidate, preview field diffs, optionally regenerate matching
audio, then write selected fields through one undo-aware collection operation.

## Invariants

- No automatic request or collection mutation while reviewing.
- Preserve note identity, SRS, review history, and every unchecked field.
- Re-read and verify note identity immediately before write.
- Do not claim the quality revision is current after a partial application.
- Bump `CURRENT_QUALITY_VERSION` whenever a released Language content standard
  changes materially, so existing notes become eligible again.

## Acceptance

- Button appears only for an outdated managed Language note.
- Candidate with another target is rejected.
- Field changes are additive/non-empty and selected explicitly.
- Audio is generated only after selection; Anki Undo can revert the write.
