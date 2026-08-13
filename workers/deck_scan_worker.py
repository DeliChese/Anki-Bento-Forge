"""Compatibility shim for the retired deck-scan QThread.

Deck scans now run through ``utils.anki_ops.run_query`` so Anki serializes all
Collection access.  The class remains importable for third-party integrations,
but intentionally has no background execution API.
"""


class DeckScanWorker:
    def __init__(self, model_name: str, deck_id: int, front_field: str):
        self.model_name = model_name
        self.deck_id = deck_id
        self.front_field = front_field

    def stop(self):
        """No-op retained for callers migrating to QueryOp."""
