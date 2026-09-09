"""Small adapter boundary around the Anki collection used by the factory UI."""

from __future__ import annotations


class AnkiCollectionAdapter:
    """Expose only the read operations needed while preparing an import."""

    def __init__(self, collection):
        self._collection = collection

    def model_id_by_name(self, model_name):
        model = self._collection.models.by_name(model_name)
        return model.get("id") if model else None

    def notes_for_model(self, model_id, *, deck_id=None):
        """Return model notes, optionally limited to one deck subtree.

        A deck group in Anki is represented by a parent deck plus all of its
        descendants.  Filtering by the cards' deck IDs (rather than just the
        deck name) keeps duplicate verification aligned with the learner's
        selected curriculum branch.
        """
        if not model_id:
            return []
        note_ids = self._collection.find_notes(f'"mid:{model_id}"')
        if deck_id is not None:
            deck_note_ids = set()
            for did in self._collection.decks.deck_and_child_ids(deck_id):
                deck_note_ids.update(self._collection.db.list(
                    "SELECT DISTINCT nid FROM cards WHERE did = ?", did,
                ))
            note_ids = [note_id for note_id in note_ids if note_id in deck_note_ids]
        return [self._collection.get_note(note_id) for note_id in note_ids]
