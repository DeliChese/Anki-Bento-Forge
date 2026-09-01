import json
import zipfile

import pytest

from utils import ai_inventory_scanner as scanner


def test_inventory_json_parser_repairs_compact_envelope_and_trailing_comma():
    parsed = scanner._parse_json_object(
        '{r:[[0,"机场","","sân bay","Du lịch","HSK1","k",99,"word"]], metadata: "ignored"}'
    )

    assert parsed["r"][0][1] == "机场"


def test_inventory_json_parser_reports_a_safe_error_for_unrecoverable_content():
    with pytest.raises(ValueError, match="AI trả về dữ liệu quét không đúng định dạng"):
        scanner._parse_json_object('{"r":[}')


def test_pasted_source_keeps_stable_line_anchors_and_heading_context():
    source = scanner.inventory_source_from_text(
        "# Du lịch\n\n机场\tsân bay\n## HSK 2\n酒店\tkhách sạn",
        name="workshop",
    )

    assert [row["source_id"] for row in source["rows"]] == [
        "L000001", "L000003", "L000004", "L000005",
    ]
    assert source["rows"][1]["context"] == "Du lịch"
    assert source["rows"][3]["context"] == "Du lịch > HSK 2"
    assert source["source_hash"]


def test_technical_excel_preview_is_recovered_as_real_cells():
    source = scanner.inventory_source_from_text(
        'A1000!R000001\tC1="STT" | C2="Nhóm" | C3="Từ tiếng Trung" | C4="Pinyin"\n'
        'A1000!R000002\tC1="1" | C2="Du lịch" | C3="机场" | C4="jīchǎng"'
    )

    assert source["rows"][0]["sheet"] == "A1000"
    assert source["rows"][1]["row"] == 2
    assert source["rows"][1]["cells"] == ["1", "Du lịch", "机场", "jīchǎng"]


def test_csv_source_preserves_empty_columns_and_row_numbers(tmp_path):
    path = tmp_path / "words.csv"
    path.write_text("STT,Nhóm,Từ,,Pinyin\n1,Du lịch,机场,,jīchǎng\n", encoding="utf-8")

    source = scanner.inventory_source_from_file(str(path))

    assert source["rows"][1]["source_id"] == "R000002"
    assert source["rows"][1]["cells"] == ["1", "Du lịch", "机场", "", "jīchǎng"]
    assert 'C3="机场"' in source["rows"][1]["text"]
    assert 'C5="jīchǎng"' in source["rows"][1]["text"]


def test_workshop_source_combines_text_and_attached_files_with_unique_ids(tmp_path):
    path = tmp_path / "words.csv"
    path.write_text("word,meaning\nairport,sân bay\n", encoding="utf-8")

    source = scanner.inventory_source_from_files(
        [str(path)], text="# Travel\nhotel : khách sạn",
    )

    assert source["kind"] == "workshop"
    assert [row["source_id"] for row in source["rows"]] == [
        "S001:L000001", "S001:L000002", "S002:R000001", "S002:R000002",
    ]
    assert source["rows"][3]["context"].startswith("words.csv")


def test_xlsx_source_preserves_sheet_row_and_blank_cells(tmp_path):
    path = tmp_path / "words.xlsx"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Vocabulary" sheetId="1" r:id="rId1"/></sheets></workbook>',
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>',
        )
        archive.writestr(
            "xl/sharedStrings.xml",
            '<?xml version="1.0"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<si><t>STT</t></si><si><t>Nhóm</t></si><si><t>Từ</t></si><si><t>Pinyin</t></si>'
            '<si><t>Du lịch</t></si><si><t>机场</t></si><si><t>jīchǎng</t></si></sst>',
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            '<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
            '<row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c>'
            '<c r="C1" t="s"><v>2</v></c><c r="E1" t="s"><v>3</v></c></row>'
            '<row r="2"><c r="A2"><v>1</v></c><c r="B2" t="s"><v>4</v></c>'
            '<c r="C2" t="s"><v>5</v></c><c r="E2" t="s"><v>6</v></c></row>'
            '</sheetData></worksheet>',
        )

    source = scanner._source_from_xlsx_package(str(path))

    assert source["rows"][1]["source_id"] == "Vocabulary!R000002"
    assert source["rows"][1]["cells"] == ["1", "Du lịch", "机场", "", "jīchǎng"]


def test_validator_rejects_unanchored_candidate_and_restores_missing_rows():
    source_rows = [
        {"source_id": "R1", "text": 'C1="1" | C2="机场"'},
        {"source_id": "R2", "text": 'C1="header"'},
    ]
    validated, missing = scanner._validate_chunk_output(
        {
            "rows": [{
                "source_id": "R1",
                "surface": "飞机场",
                "decision": "keep",
                "confidence": 0.99,
            }],
        },
        source_rows,
    )

    assert validated[0]["decision"] == "review"
    assert validated[0]["surface"] == ""
    assert validated[1]["source_id"] == "R2"
    assert validated[1]["decision"] == "review"
    assert missing == 1


def test_language_guard_prevents_chinese_pinyin_from_becoming_keep_item():
    validated, missing = scanner._validate_chunk_output(
        {
            "rows": [{
                "source_id": "R1",
                "surface": "jīchǎng",
                "decision": "keep",
                "confidence": 0.95,
            }],
        },
        [{"source_id": "R1", "text": 'C1="机场" | C2="jīchǎng"'}],
        lang="chinese",
    )

    assert validated[0]["decision"] == "review"
    assert validated[0]["surface"] == "jīchǎng"
    assert "target-language script" in validated[0]["reason"]
    assert missing == 0


def test_user_can_restore_a_source_anchored_skip_as_review_inventory():
    rows = [{
        "source_id": "R1",
        "surface": "机场",
        "meaning": "sân bay",
        "topic": "Du lịch",
        "level": "HSK 2",
        "decision": "skip",
        "confidence": 0.4,
        "reason": "uncertain",
    }]
    assert scanner.inventory_from_scan_rows(rows, "source-hash", "chinese") == []

    rows[0]["decision"] = "review"
    inventory = scanner.inventory_from_scan_rows(rows, "source-hash", "chinese")

    assert inventory[0]["front"] == "机场"
    assert inventory[0]["decision"] == "review"


def test_structured_excel_fast_path_uses_zero_ai_tokens(tmp_path, monkeypatch):
    source = scanner.inventory_source_from_text(
        'A1000!R000001\tC1="STT" | C2="Nhóm" | C3="Từ tiếng Trung" | C4="Pinyin" | '
        'C5="Nghĩa tiếng Việt" | C6="HSK Level"\n'
        'A1000!R000002\tC1="1" | C2="Du lịch" | C3="机场" | C4="jīchǎng" | '
        'C5="sân bay" | C6="HSK 2"\n'
        'Phân nhóm!R000001\tC1="Nhóm" | C2="Số mục" | C3="Vai trò"\n'
        'Phân nhóm!R000002\tC1="Du lịch" | C2="1" | C3="Mô tả phụ"'
    )
    monkeypatch.setattr(
        scanner._api,
        "get_api_config",
        lambda: (_ for _ in ()).throw(AssertionError("AI must not be called")),
    )

    result = scanner.scan_inventory_with_ai(source, "chinese")

    assert result["scan_mode"] == "structured_local"
    assert result["counts"] == {
        "source_rows": 4, "keep": 1, "skip": 3, "review": 0, "unresolved": 0,
    }
    assert result["inventory"][0]["front"] == "机场"
    assert result["inventory"][0]["topic"] == "Du lịch"
    assert result["inventory"][0]["level"] == "HSK2"
    assert result["token_info"]["total_tokens"] == 0
    assert result["token_info"]["requests"] == 0


def test_chinese_register_column_is_not_a_level_and_is_enriched_as_hsk(tmp_path, monkeypatch):
    source = scanner.inventory_source_from_text(
        'A1000!R000001\tC1="STT" | C2="Nhóm" | C3="Từ tiếng Trung" | '
        'C4="Pinyin" | C5="Nghĩa" | C6="Mức độ / sắc thái"\n'
        'A1000!R000002\tC1="1" | C2="Du lịch" | C3="机场" | '
        'C4="jīchǎng" | C5="sân bay" | C6="A – cực thường dùng"'
    )
    monkeypatch.setattr(scanner, "INVENTORY_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(scanner, "TOPIC_CATALOG_PATH", str(tmp_path / "topics.json"))
    monkeypatch.setattr(scanner._api, "_record_token_info", lambda *args, **kwargs: None)
    calls = []

    def fake_post(_url, payload, _headers, **_kwargs):
        calls.append(payload)
        content = payload["messages"][1]["content"]
        assert "Structured columns:" in content
        assert "Mức độ / sắc thái is not proficiency" in content
        return json.dumps({
            "choices": [{
                "finish_reason": "stop",
                "message": {"content": json.dumps({
                    "r": [[0, "机场", "jīchǎng", "sân bay", "Du lịch", "HSK 1", "k", 99, "word"]],
                }, ensure_ascii=False)},
            }],
            "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
        })

    monkeypatch.setattr(scanner._api, "_http_post_json", fake_post)
    result = scanner.scan_inventory_with_ai(source, "chinese", runtime_config={
        "api_key": "test", "api_base": "http://localhost:11434/v1",
        "model": "test", "temperature": 0.2, "max_tokens": 4096,
    })

    assert result["scan_mode"] == "hybrid"
    assert result["inventory"][0]["level"] == "HSK1"
    assert result["counts"]["keep"] == 1
    assert len(calls) == 1


def test_chinese_rejects_bare_a_as_invalid_proficiency_level():
    validated, _missing = scanner._validate_chunk_output(
        {"r": [[0, "机场", "", "sân bay", "Du lịch", "A", "k", 99, "word"]]},
        [{"source_id": "R1", "text": 'C1="机场"'}],
        lang="chinese",
    )

    assert validated[0]["decision"] == "review"
    assert validated[0]["level"] == ""
    assert "not valid" in validated[0]["reason"]


def test_turbo_compact_protocol_uses_fewer_chunks_and_expands_output():
    source_rows = [
        {"source_id": f"L{index:06d}", "text": f"word {index}", "context": "List"}
        for index in range(200)
    ]

    normal = scanner._chunk_rows(source_rows, turbo=False)
    turbo = scanner._chunk_rows(source_rows, turbo=True)
    payload = {"r": [[0, "word 0", "", "nghĩa", "Topic", "A1", "k", 95, "word"]]}
    validated, missing = scanner._validate_chunk_output(payload, normal[0], lang="english")

    assert len(normal) == 3
    assert len(turbo) == 2
    assert set(normal[0][0]["compact"]) == {"i", "v", "x"}
    assert "source_id" not in normal[0][0]["compact"]
    assert validated[0]["source_id"] == "L000000"
    assert validated[0]["decision"] == "keep"
    assert validated[0]["confidence"] == 0.95
    assert missing == len(normal[0]) - 1


def test_compact_protocol_reduces_repeated_json_overhead():
    source_row = {
        "source_id": "A1000!R000002",
        "text": 'C1="1" | C2="Du lịch" | C3="机场" | C4="jīchǎng"',
        "context": "Sheet: A1000",
        "cells": ["1", "Du lịch", "机场", "jīchǎng"],
    }
    compact = scanner._chunk_rows([source_row])[0][0]["compact"]
    verbose_output = {
        "source_id": source_row["source_id"], "surface": "机场", "reading": "jīchǎng",
        "meaning": "sân bay", "topic": "Du lịch", "level": "HSK 2",
        "decision": "keep", "confidence": 0.98, "reason": "headword",
    }
    compact_output = [0, "机场", "jīchǎng", "sân bay", "Du lịch", "HSK 2", "k", 98, "headword"]

    assert len(json.dumps(compact, ensure_ascii=False)) < len(json.dumps(source_row, ensure_ascii=False))
    assert len(json.dumps(compact_output, ensure_ascii=False)) < len(
        json.dumps(verbose_output, ensure_ascii=False)
    ) * 0.6


def test_ai_scan_keeps_only_source_anchored_candidates_and_caches(tmp_path, monkeypatch):
    source = scanner.inventory_source_from_text("STT | Từ | Pinyin\n1 | 机场 | jīchǎng")
    monkeypatch.setattr(scanner, "INVENTORY_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(scanner._api, "_record_token_info", lambda *args, **kwargs: None)
    calls = []

    def fake_post(_url, payload, _headers, **_kwargs):
        calls.append(payload)
        user_content = payload["messages"][1]["content"]
        assert '"i":0' in user_content and '"v":' in user_content
        assert "source_id" not in user_content
        response_rows = [
            [0, "", "", "", "", "", "s", 100, "header"],
            [1, "机场", "jīchǎng", "sân bay", "Du lịch", "HSK 2", "k", 98, "headword"],
        ]
        return json.dumps({
            "choices": [{
                "finish_reason": "stop",
                "message": {"content": json.dumps({"r": response_rows}, ensure_ascii=False)},
            }],
            "usage": {"prompt_tokens": 100, "completion_tokens": 40, "total_tokens": 140},
        })

    monkeypatch.setattr(scanner._api, "_http_post_json", fake_post)
    config = {
        "api_key": "test",
        "api_base": "http://localhost:11434/v1",
        "model": "test-model",
        "temperature": 0.7,
        "max_tokens": 4096,
    }

    result = scanner.scan_inventory_with_ai(source, "chinese", runtime_config=config)
    cached = scanner.scan_inventory_with_ai(source, "chinese", runtime_config=config)

    assert result["counts"] == {
        "source_rows": 2, "keep": 1, "skip": 1, "review": 0, "unresolved": 0,
    }
    assert result["inventory"][0]["front"] == "机场"
    assert result["inventory"][0]["decision"] == "keep"
    assert result["token_info"]["prompt_tokens"] == 100
    assert cached == result
    assert len(calls) == 1


def test_dialog_wires_ai_scanner_excel_and_decision_filter():
    dialog = (
        scanner.os.path.join(scanner.os.path.dirname(scanner.os.path.dirname(__file__)), "ui", "batch_dialog.py")
    )
    source = open(dialog, encoding="utf-8").read()

    assert "InventoryScanThread" in source
    assert "inventory_source_from_file" in source
    assert "self.cbo_decision" in source
    assert "self.chk_turbo_scan" in source
    assert 'lines.append("\\t".join(str(cell) for cell in cells))' in source
    assert 'item.get("decision") == decision' in source


def test_topic_catalog_merges_only_visible_label_variants():
    rows, catalog = scanner.canonicalize_topics([
        {"surface": "机场", "topic": "05. Du lịch", "decision": "keep"},
        {"surface": "酒店", "topic": "DU LỊCH", "decision": "keep"},
        {"surface": "预订", "topic": "Du lich", "decision": "review"},
        {"surface": "登机", "topic": "Giao thông", "decision": "keep"},
    ])

    assert [row["topic"] for row in rows] == [
        "Du lịch", "Du lịch", "Du lịch", "Giao thông",
    ]
    assert catalog == [
        {"id": "du lich", "name": "Du lịch", "count": 3},
        {"id": "giao thong", "name": "Giao thông", "count": 1},
    ]


def test_structured_topic_catalog_is_saved_without_source_content(tmp_path, monkeypatch):
    source = scanner.inventory_source_from_text(
        'A1000!R000001\tC1="STT" | C2="Nhóm" | C3="Từ tiếng Trung" | C4="HSK Level"\n'
        'A1000!R000002\tC1="1" | C2="05. Du lịch" | C3="机场" | C4="HSK 1"\n'
        'A1000!R000003\tC1="2" | C2="DU LỊCH" | C3="酒店" | C4="HSK 1"'
    )
    catalog_path = tmp_path / "topics.json"
    monkeypatch.setattr(scanner, "TOPIC_CATALOG_PATH", str(catalog_path))

    result = scanner.scan_inventory_with_ai(source, "chinese")
    persisted = json.loads(catalog_path.read_text(encoding="utf-8"))

    assert result["topic_catalog"] == [
        {"id": "du lich", "name": "Du lịch", "count": 2},
    ]
    serialized = json.dumps(persisted, ensure_ascii=False)
    assert "机场" not in serialized
    assert "酒店" not in serialized
    assert "Du lịch" in serialized


def test_structured_rows_missing_topic_use_ai_only_for_topic_enrichment(tmp_path, monkeypatch):
    source = scanner.inventory_source_from_text(
        'Sheet1!R000001\tC1="STT" | C2="Từ tiếng Trung" | C3="Nghĩa"\n'
        'Sheet1!R000002\tC1="1" | C2="机场" | C3="sân bay"'
    )
    monkeypatch.setattr(scanner, "INVENTORY_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(scanner, "TOPIC_CATALOG_PATH", str(tmp_path / "topics.json"))
    monkeypatch.setattr(scanner._api, "_record_token_info", lambda *args, **kwargs: None)
    calls = []

    def fake_post(_url, payload, _headers, **_kwargs):
        calls.append(payload)
        content = payload["messages"][1]["content"]
        assert '"v":["1","机场","sân bay"]' in content
        assert '"STT"' not in content
        return json.dumps({
            "choices": [{
                "finish_reason": "stop",
                "message": {"content": json.dumps({
                    "r": [[0, "机场", "", "sân bay", "Du lịch", "HSK 2", "k", 99, "word"]],
                }, ensure_ascii=False)},
            }],
            "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
        })

    monkeypatch.setattr(scanner._api, "_http_post_json", fake_post)
    result = scanner.scan_inventory_with_ai(source, "chinese", runtime_config={
        "api_key": "test", "api_base": "http://localhost:11434/v1",
        "model": "test", "temperature": 0.2, "max_tokens": 4096,
    })

    assert result["scan_mode"] == "hybrid"
    assert result["topic_catalog"][0]["name"] == "Du lịch"
    assert result["inventory"][0]["topic"] == "Du lịch"
    assert len(calls) == 1


def test_prepared_inventory_filters_generation_and_forces_saved_topic():
    inventory = [{
        "identity": "takeabreak", "front": "take a break", "topic": "Daily life",
        "decision": "keep",
    }, {
        "identity": "outofcontext", "front": "out of context", "topic": "",
        "decision": "review",
    }]
    generated = [
        {"chunk": "take a break", "topic": "Everyday routine", "meaning": "nghỉ giải lao"},
        {"chunk": "invented phrase", "topic": "Daily life", "meaning": "bịa"},
    ]

    result = scanner.apply_prepared_inventory(
        generated,
        inventory,
        [{"id": "daily life", "name": "Daily life", "count": 1}],
        card_kind="collocation",
    )

    assert result == [{
        "chunk": "take a break", "topic": "Daily life", "meaning": "nghỉ giải lao",
    }]


def test_ai_extract_worker_has_topic_preflight_before_all_language_generation():
    worker_path = scanner.os.path.join(
        scanner.os.path.dirname(scanner.os.path.dirname(__file__)), "workers", "ai_workers.py",
    )
    source = open(worker_path, encoding="utf-8").read()

    preflight = source.index("scan_inventory_with_ai(")
    vocabulary = source.index("extract_vocabulary_long_text(")
    grammar = source.index("extract_grammar_long_text(")
    assert preflight < vocabulary
    assert preflight < grammar
    assert "apply_prepared_inventory(" in source
