"""V18-05 regression tests for Knowledge preview/duplicate planning."""

from utils.knowledge_workflow import (
    prepare_knowledge_batch,
    read_knowledge_notes_for_deck,
)


def _basic(answer="Central Processing Unit", source="notes"):
    return {
        "type": "basic", "question": "What is CPU?", "answer": answer,
        "explanation": "", "source": source, "tags": ["computing"], "cloze_text": "",
    }


def test_knowledge_duplicate_scan_is_model_and_deck_scoped():
    class Models:
        @staticmethod
        def by_name(name):
            assert name == "Bento Forge Knowledge V18 (Add-on)"
            return {"id": 18}

    class DB:
        @staticmethod
        def list(query, mid, did):
            assert "n.mid = ? AND c.did = ?" in query
            assert (mid, did) == (18, 42)
            return [7]

    class Note(dict):
        id = 7
        tags = ["computing"]

    class Collection:
        models = Models()
        db = DB()

        @staticmethod
        def get_note(nid):
            assert nid == 7
            return Note({
                "Type": "basic", "Question": "What is CPU?", "Answer": "old",
                "Explanation": "", "Source": "book", "Cloze Text": "",
                "Duplicate Key": "whatiscpu",
            })

    rows = read_knowledge_notes_for_deck(Collection(), 42)
    planned = prepare_knowledge_batch([_basic(answer="new", source="")], rows)
    assert planned["counts"] == {"new": 0, "update": 1, "duplicate": 0}
    assert planned["prepared"][0]["nid"] == 7
    assert "Answer" in planned["prepared"][0]["update_fields"]
    assert "Source" not in planned["prepared"][0]["update_fields"]


def test_knowledge_batch_deduplicates_normalized_question_and_keeps_cloze_separate():
    cloze = {
        "type": "cloze", "question": "", "answer": "", "explanation": "",
        "source": "", "tags": [], "cloze_text": "CPU means {{c1::Central Processing Unit}}.",
    }
    result = prepare_knowledge_batch([_basic(), _basic(), cloze], [])
    assert result["counts"] == {"new": 2, "update": 0, "duplicate": 1}
    assert [row["action"] for row in result["prepared"]] == ["add", "add"]
