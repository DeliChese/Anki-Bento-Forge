"""Small adapter boundary around the Anki collection used by the factory UI."""

from __future__ import annotations


class AnkiCollectionAdapter:
    """Expose only the read operations needed while preparing an import."""

    def __init__(self, collection):
        self._collection = collection

    def model_id_by_name(self, model_name):
        model = self._collection.models.by_name(model_name)
        return model.get("id") if model else None

    def notes_for_model(self, model_id):
        if not model_id:
            return []
        note_ids = self._collection.find_notes(f'"mid:{model_id}"')
        return [self._collection.get_note(note_id) for note_id in note_ids]
