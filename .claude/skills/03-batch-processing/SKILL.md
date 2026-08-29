---
name: batch-processing
description: Xử lý danh sách từ vựng LỚN qua AI — utils/batch_processor.py. Parse, smart grouping, batch AI calls, deck organization. Đọc khi sửa Batch dialog / hai-pass AI.
---

# 🚀 SKILL-03: BATCH PROCESSING (`utils/batch_processor.py`)

> Chiến lược: SMART CHUNKING theo Quality V2 → TWO-PASS AI (Pass1 enrich vocab, Pass2 organize decks) → RATE LIMITING → CACHE từng batch (14 ngày).

## HẰNG SỐ (đầu file, dòng 73-80)

| Hằng | Giá trị | Dòng |
|------|---------|------|
| `DEFAULT_BATCH_SIZE` | 10 | 73 |
| `MAX_WORDS_PER_REQUEST` | 30 | 74 |
| `MIN_DELAY_BETWEEN_BATCHES` | 1.5s | 75 |
| `CACHE_TTL` | 14 ngày | 80 |

## API CÔNG KHAI

```python
parse_word_list(raw_text, lang="japanese") -> list[{front, meaning, level, topic}]
smart_group_words(words, batch_size=10) -> list[list]           # nhóm theo level/topic, sort
process_large_word_list(raw_text, lang, custom_instruction="", existing_words=None,
                        batch_size=10, progress_callback=None, should_abort=None, grammar=False) -> list[dict]
organize_decks_with_ai(vocab_list, lang, progress_callback=None, should_abort=None,
                       source_sections=None, custom_instruction="") -> dict{suggestion, decks:[{parent, sub_decks}]}
create_decks_from_organization(organization, vocab_list, lang, progress_callback=None) -> dict{deck_name: deck_id}
estimate_batch_cost(word_count, lang, batch_size=10) -> dict    # ước tính USD + thời gian
# internal: _fallback_deck_organization:1251
```

## DATA FLOW (`process_large_word_list` — dòng 715)

```
1. parse_word_list → words
2. Lọc từ trùng existing_words (lowercase)
3. smart_group_words → batches
4. Với mỗi batch:
   - check _batch_cache_get (grammar-aware)
   - _call_ai_for_batch → AI enrich (system prompt vocab/grammar + JSON template)
   - Lọc trùng (seen_fronts + existing_set)
   - _batch_cache_set
   - Nếu >=3 lỗi → raise RuntimeError dừng
   - sleep(MIN_DELAY_BETWEEN_BATCHES) giữa batch (rate limit)
5. Trả all_vocab
```

## DECK ORGANIZATION (Pass 2, dòng 1063)

- `organize_decks_with_ai`: gửi `word_summaries` (front|meaning|level|topic|SOURCE path) — sampling nếu >500 từ, `MAX_WORDS_FOR_ORG=500`.
- `source_sections` là outline bounded, không gửi content lặp; H1–H3 là deck candidate, H4–H6 mặc định chỉ làm context.
- Prompt system: `_DECK_ORGANIZER_SYSTEM_PROMPT` (1000). Output JSON: `{suggestion, decks:[{parent, sub_decks:[{name, description, word_count, words}]}]}`.
- **Fallback quan trọng**: mọi lỗi → `_fallback_deck_organization` (1257) nhóm theo topic/source heading→level. KHÔNG được để crash.
- `create_decks_from_organization` (1359): tạo parent/sub bằng `collection.decks.id(name)`; import `aqt` bên trong try khi caller không truyền collection.

## TRAPS

1. **Sửa prompt batch** → phải bump `_PROMPT_VERSION` (xem SKILL-02) vì batch cache dùng riêng key nhưng version chung `_PROMPT_VERSION`.
2. **Không gửi quá 30 từ/request** (`MAX_WORDS_PER_REQUEST`); policy Quality V2 có thể chọn nhỏ hơn.
3. `parse_word_list` có nhánh JSON (`raw_text.startswith("[")`) — giữ nguyên để nhận JSON từ AI Chat.
4. **Grammar mode**: `grammar=True` đổi label + dùng prompt ngữ pháp + cache key riêng.

## VERIFY

```
python -m pytest --rootdir=tests tests/test_batch_processor.py tests/test_deck_blueprint.py tests/test_comprehensive.py tests/test_grammar.py -v
```
