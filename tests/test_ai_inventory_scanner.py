import json
import zipfile

from utils import ai_inventory_scanner as scanner


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


def test_ai_scan_keeps_only_source_anchored_candidates_and_caches(tmp_path, monkeypatch):
    source = scanner.inventory_source_from_text("STT | Từ | Pinyin\n1 | 机场 | jīchǎng")
    monkeypatch.setattr(scanner, "INVENTORY_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr(scanner._api, "_record_token_info", lambda *args, **kwargs: None)
    calls = []

    def fake_post(_url, payload, _headers, **_kwargs):
        calls.append(payload)
        response_rows = [
            {
                "source_id": "L000001",
                "surface": "",
                "decision": "skip",
                "confidence": 1,
                "reason": "header",
            },
            {
                "source_id": "L000002",
                "surface": "机场",
                "reading": "jīchǎng",
                "meaning": "sân bay",
                "topic": "Du lịch",
                "level": "HSK 2",
                "decision": "keep",
                "confidence": 0.98,
                "reason": "headword",
            },
        ]
        return json.dumps({
            "choices": [{
                "finish_reason": "stop",
                "message": {"content": json.dumps({"rows": response_rows}, ensure_ascii=False)},
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
    assert 'item.get("decision") == decision' in source
