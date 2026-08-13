"""Small, testable wrappers around Anki's managed collection operations."""


def run_query(parent, op, success, failure):
    """Run a read-only collection operation on Anki's collection executor."""
    from aqt.operations import QueryOp

    return QueryOp(parent=parent, op=op).success(success).failure(failure).run_in_background()


def run_collection(parent, op, success, failure):
    """Run a mutating, undo-aware collection operation on Anki's executor."""
    from aqt.operations import CollectionOp

    return CollectionOp(parent=parent, op=op).success(success).failure(failure).run_in_background()
