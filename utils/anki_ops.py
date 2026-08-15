"""Small, testable wrappers around Anki's managed collection operations."""


def run_query(parent, op, success, failure):
    """Run a read-only collection operation on Anki's collection executor."""
    from aqt.operations import QueryOp

    try:
        # Anki >= 25.09: `success` is a keyword-only constructor argument and
        # QueryOp no longer exposes a chained .success() method.
        query = QueryOp(parent=parent, op=op, success=success)
    except TypeError:
        # Older Anki: `success` is attached through the chained .success() method.
        query = QueryOp(parent=parent, op=op).success(success)
    return query.failure(failure).run_in_background()


class _OpResult(dict):
    """dict kết quả cũ, kèm thuộc tính ``.changes`` mà ``CollectionOp`` Anki >= 25 yêu cầu.

    Anki 25.09+ yêu cầu op của ``CollectionOp`` trả về một object có ``.changes``
    (một ``OpChanges`` protobuf). Các op cũ của addon trả về dict báo cáo; lớp này
    vừa là dict (để callback success / code cũ dùng ``report.get(...)`` như cũ),
    vừa mang ``.changes`` để Anki không crash.
    """

    __slots__ = ("changes",)

    def __init__(self, data, changes):
        super().__init__(data or {})
        self.changes = changes


def run_collection(parent, op, success, failure):
    """Run a mutating, undo-aware collection operation on Anki's executor."""
    from aqt.operations import CollectionOp

    def wrapped_op(col):
        result = op(col)
        if hasattr(result, "changes"):
            # Anki >= 25: op đã trả object mang OpChanges.
            return result
        try:
            from anki.collection import OpChanges

            # Anki >= 25: bọc dict cũ để `on_op_finished` đọc được `.changes`.
            return _OpResult(result, OpChanges())
        except Exception:
            # Anki cũ / môi trường test: giữ nguyên hình dạng kết quả.
            return result

    return (
        CollectionOp(parent=parent, op=wrapped_op)
        .success(success)
        .failure(failure)
        .run_in_background()
    )
