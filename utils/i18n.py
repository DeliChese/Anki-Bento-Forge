"""
i18n Module — Hỗ trợ đa ngôn ngữ cho AnkiTool.

Cung cấp:
- t(key, lang=None): Lấy chuỗi dịch theo key
- set_language(lang): Đặt ngôn ngữ mặc định
- get_language(): Lấy ngôn ngữ hiện tại
- SUPPORTED_LANGUAGES: Danh sách ngôn ngữ được hỗ trợ

Sử dụng:
    from utils.i18n import t, set_language
    set_language("en")
    print(t("ai_extract"))  # "AI Extract"
"""

import json
import os

from .user_data import atomic_write_json, get_user_data_path, migrate_legacy_json, read_json

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
_LEGACY_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n_config.json")
_CONFIG_PATH = get_user_data_path("i18n_config.json")

SUPPORTED_LANGUAGES = {
    "vi": "🇻🇳 Tiếng Việt",
    "en": "🇬🇧 English",
}

_current_lang = "vi"

# ═══════════════════════════════════════════════════════════
#  TRANSLATIONS DATABASE
# ═══════════════════════════════════════════════════════════

_TRANSLATIONS = {
    # ── App / Menu ──────────────────────────────────────
    "app_title": {
        "vi": "Bento Forge — Vocabulary Factory",
        "en": "Bento Forge — Vocabulary Factory",
    },
    "app_short": {
        "vi": "Bento Forge",
        "en": "Bento Forge",
    },
    "app_title_knowledge": {
        "vi": "Bento Forge — Knowledge Factory",
        "en": "Bento Forge — Knowledge Factory",
    },
    "menu_entry": {
        "vi": "🧪 Bento Forge",
        "en": "🧪 Bento Forge",
    },

    # ── Language Selector ───────────────────────────────
    "lang_japanese": {
        "vi": "🇯🇵 Tiếng Nhật",
        "en": "🇯🇵 Japanese",
    },
    "lang_chinese": {
        "vi": "🇨🇳 Tiếng Trung",
        "en": "🇨🇳 Chinese",
    },
    "lang_korean": {
        "vi": "🇰🇷 Tiếng Hàn",
        "en": "🇰🇷 Korean",
    },
    "lang_english": {
        "vi": "🇬🇧 Tiếng Anh",
        "en": "🇬🇧 English",
    },

    # ── Deck & File ─────────────────────────────────────
    "deck_label": {
        "vi": "📦 Deck:",
        "en": "📦 Deck:",
    },
    "open_file_btn": {
        "vi": "📁 MỞ FILE (JSON/TXT)",
        "en": "📁 OPEN FILE (JSON/TXT)",
    },
    "sample_json_btn": {
        "vi": "💡 Xem mẫu JSON",
        "en": "💡 View JSON sample",
    },

    # ── AI Section ──────────────────────────────────────
    "ai_group_title": {
        "vi": "🏭 Lò đúc AI — Dây chuyền học liệu",
        "en": "🏭 AI Forge — Learning-material production line",
    },
    "ai_group_title_knowledge": {
        "vi": "⚙️ Lò Đúc Kiến Thức (AI)",
        "en": "⚙️ Knowledge Forge (AI)",
    },
    "ai_settings_btn": {
        "vi": "⚙️ Cài Đặt API",
        "en": "⚙️ API Settings",
    },
    "ai_clear_text_btn": {
        "vi": "🗑 Xóa",
        "en": "🗑 Clear",
    },
    "ai_extract_btn": {
        "vi": "✨ Tạo thẻ",
        "en": "✨ Create cards",
    },
    "ai_extract_btn_count": {
        "vi": "✨ Tạo tối đa {count} thẻ",
        "en": "✨ Create up to {count} cards",
    },
    "ai_card_count_label": {
        "vi": "Số thẻ:",
        "en": "Cards:",
    },
    "knowledge_generate_btn": {
        "vi": "✨ GỬI & TẠO THẺ",
        "en": "✨ SEND & GENERATE CARDS",
    },
    "knowledge_generate_tip": {
        "vi": "Gửi nguồn học và yêu cầu thêm cho AI để tạo thẻ Knowledge Basic/Cloze theo schema nghiêm ngặt.",
        "en": "Send the source and extra request to generate strict Knowledge Basic/Cloze cards.",
    },
    "ai_stop_btn": {
        "vi": "⏹ Dừng",
        "en": "⏹ Stop",
    },
    "history_scan_cancel_btn": {
        "vi": "⏹ Dừng quét",
        "en": "⏹ Stop scan",
    },
    "history_scan_cancel_tip": {
        "vi": "Dừng quét lịch sử ban đầu; dữ liệu quét dở sẽ không được lưu.",
        "en": "Stop the initial history scan; partial results will not be saved.",
    },
    "ai_input_placeholder": {
        "vi": "📥 Dán nguồn học liệu cần phân tích.",
        "en": "📥 Paste learning material to analyze.",
    },
    "ai_instruction_placeholder": {
        "vi": "VD: Chỉ lấy từ HSK3+, chủ đề ẩm thực, ưu tiên từ khó...",
        "en": "e.g.: Only HSK3+ words, food topic, prioritize difficult words...",
    },
    "ai_instruction_label": {
        "vi": "🎯 Yêu cầu đúc nhanh:",
        "en": "🎯 Quick-forge brief:",
    },
    "knowledge_instruction_label": {
        "vi": "🎯 Yêu cầu thêm:",
        "en": "🎯 Extra request:",
    },
    "knowledge_instruction_placeholder": {
        "vi": "VD: Tạo tối đa 5 thẻ Cloze, ưu tiên định nghĩa và ví dụ thực tế...",
        "en": "e.g. Create at most 5 Cloze cards, prioritizing definitions and practical examples...",
    },

    # ── JSON Input ──────────────────────────────────────
    "json_input_label": {
        "vi": "📝 Dán dữ liệu JSON (hỗ trợ array hoặc multiple objects):",
        "en": "📝 Paste JSON data (supports array or multiple objects):",
    },
    "json_lock_btn": {
        "vi": "🔒 Khóa JSON",
        "en": "🔒 Lock JSON",
    },
    "json_unlock_btn": {
        "vi": "🔓 Mở khóa JSON",
        "en": "🔓 Unlock JSON",
    },
    "json_lock_tip": {
        "vi": "Khóa JSON riêng cho ngôn ngữ và chế độ hiện tại. Nội dung được lưu bền vững, kể cả sau khi thoát Anki.",
        "en": "Lock JSON for the current language and card type. It is retained after closing Anki.",
    },
    "json_unlock_tip": {
        "vi": "Mở khóa để sửa hoặc thay thế JSON của ngôn ngữ và chế độ hiện tại.",
        "en": "Unlock to edit or replace JSON for the current language and card type.",
    },
    "json_locked_tip": {
        "vi": "JSON đang bị khóa. Hãy mở khóa trước khi thay thế nội dung.",
        "en": "JSON is locked. Unlock it before replacing the content.",
    },

    # ── Filter Section ──────────────────────────────────
    "filter_group_title": {
        "vi": "🛡️ Trạm Kiểm Định & Phân Loại",
        "en": "🛡️ Inspection & Sorting Station",
    },
    "filter_raw_count": {
        "vi": "📦 Tồn Kho Nguyên Liệu: {count} mục",
        "en": "📦 Raw Material Stock: {count} items",
    },
    "filter_level_label": {
        "vi": "🎓 Cấp độ:",
        "en": "🎓 Level:",
    },
    "filter_topic_label": {
        "vi": "🔍 Topic:",
        "en": "🔍 Topic:",
    },
    "filter_topic_placeholder": {
        "vi": "Lọc theo topic...",
        "en": "Filter by topic...",
    },
    "filter_audio_label": {
        "vi": "🔊 Auto Audio:",
        "en": "🔊 Auto Audio:",
    },
    "filter_audio_vocab": {
        "vi": "🎵 Vocab",
        "en": "🎵 Vocab",
    },
    "filter_audio_ex1": {
        "vi": "🎵 Ví dụ 1",
        "en": "🎵 Example 1",
    },
    "filter_audio_ex2": {
        "vi": "🎵 Ví dụ 2",
        "en": "🎵 Example 2",
    },

    # ── Action Buttons ──────────────────────────────────
    "btn_verify": {
        "vi": "🌪️ Kiểm Định",
        "en": "🌪️ Verify",
    },
    "btn_rebuild": {
        "vi": "🔨 Tái Tạo Model",
        "en": "🔨 Rebuild Model",
    },
    "btn_diff_meaning": {
        "vi": "🔍 Nghĩa Khác",
        "en": "🔍 Diff Meaning",
    },

    # ── Voice Section ───────────────────────────────────
    "voice_group_title": {
        "vi": "🎤 Chọn Giọng Đọc & Tốc Độ",
        "en": "🎤 Voice & Speed",
    },
    "voice_label": {
        "vi": "Giọng:",
        "en": "Voice:",
    },
    "voice_preview_btn": {
        "vi": "▶ Nghe thử",
        "en": "▶ Preview",
    },
    "voice_speed_label": {
        "vi": "⏩ Tốc độ:",
        "en": "⏩ Speed:",
    },
    "tts_settings_btn": {
        "vi": "☁ Nguồn giọng",
        "en": "☁ Voice source",
    },
    "tts_settings_tip": {
        "vi": "Chọn Edge Neural hoặc cấu hình Azure Speech Neural bằng Key lưu an toàn trong hệ điều hành",
        "en": "Choose Edge Neural or configure Azure Speech Neural with an OS-secured key",
    },
    "tts_settings_title": {
        "vi": "Nguồn giọng Neural",
        "en": "Neural voice source",
    },
    "tts_provider_label": {
        "vi": "Nguồn:",
        "en": "Provider:",
    },
    "tts_provider_edge": {
        "vi": "Edge Neural (không cần Key)",
        "en": "Edge Neural (no key)",
    },
    "tts_provider_azure": {
        "vi": "Azure Speech Neural (API chính thức)",
        "en": "Azure Speech Neural (official API)",
    },
    "tts_region_label": {
        "vi": "Region Azure:",
        "en": "Azure region:",
    },
    "tts_region_placeholder": {
        "vi": "Ví dụ: southeastasia",
        "en": "For example: southeastasia",
    },
    "tts_key_label": {
        "vi": "Speech Key:",
        "en": "Speech key:",
    },
    "tts_key_placeholder": {
        "vi": "Dán Azure Speech Key",
        "en": "Paste Azure Speech Key",
    },
    "tts_key_saved_placeholder": {
        "vi": "Đã có Key lưu an toàn — để trống nếu không đổi",
        "en": "A key is stored securely — leave blank to keep it",
    },
    "tts_key_saved_status": {
        "vi": "✓ Speech Key đã lưu trong Credential Manager của hệ điều hành; không nằm trong file add-on.",
        "en": "✓ Speech key is in the OS Credential Manager, not in an add-on file.",
    },
    "tts_key_missing_status": {
        "vi": "Chưa có Speech Key. Dán Key để bật Azure Speech.",
        "en": "No Speech key is stored. Paste one to enable Azure Speech.",
    },
    "tts_save_btn": {
        "vi": "Lưu nguồn giọng",
        "en": "Save voice source",
    },
    "tts_cancel_btn": {
        "vi": "Hủy",
        "en": "Cancel",
    },
    "tts_save_error": {
        "vi": "Không thể lưu Azure Speech. Hãy kiểm tra Region, Speech Key và Credential Manager của hệ điều hành.",
        "en": "Could not save Azure Speech. Check the region, Speech key, and OS Credential Manager.",
    },
    "tts_save_success": {
        "vi": "Đã lưu nguồn giọng. Bấm Nghe thử để kiểm tra.",
        "en": "Voice source saved. Use Preview to verify it.",
    },

    # ── Preview List ────────────────────────────────────
    "tts_usage_btn": {
        "vi": "📊 Lịch sử Azure",
        "en": "📊 Azure usage",
    },
    "tts_usage_tip": {
        "vi": "Xem số ký tự và lượt gọi Azure Speech ghi tại máy này",
        "en": "View local Azure Speech character and request estimates",
    },
    "tts_usage_title": {
        "vi": "📊 Lịch sử dùng Azure Speech",
        "en": "📊 Azure Speech usage history",
    },
    "tts_usage_notice": {
        "vi": "Số liệu ước tính tại máy này: không lưu nội dung đọc hay Speech Key. Cache không tạo gọi API mới. Azure Portal là nguồn quyết toán chính thức.",
        "en": "Local estimate only: no spoken text or Speech key is stored. Cache hits make no new API call. Azure Portal remains the billing authority.",
    },
    "tts_usage_month": {
        "vi": "Tháng {month}: {requests} lượt gọi · {characters} ký tự gửi · thành công {successes} · lỗi {failures} · dùng cache {cache_hits}",
        "en": "{month}: {requests} requests · {characters} submitted characters · {successes} succeeded · {failures} failed · {cache_hits} cache hits",
    },
    "tts_usage_all_time": {
        "vi": "Tổng đã lưu: {requests} lượt gọi · {characters} ký tự gửi · thành công {successes} · lỗi {failures} · dùng cache {cache_hits}",
        "en": "Saved total: {requests} requests · {characters} submitted characters · {successes} succeeded · {failures} failed · {cache_hits} cache hits",
    },
    "tts_usage_daily_title": {
        "vi": "Theo ngày (tối đa 90 ngày gần nhất):",
        "en": "By day (up to the last 90 days):",
    },
    "tts_usage_day": {
        "vi": "{date} — {requests} lượt · {characters} ký tự · OK {successes} · lỗi {failures} · cache {cache_hits}",
        "en": "{date} — {requests} requests · {characters} characters · OK {successes} · failed {failures} · cache {cache_hits}",
    },
    "tts_usage_empty": {
        "vi": "Chưa có lệnh Azure Speech nào được ghi trên máy này.",
        "en": "No Azure Speech request has been recorded on this machine yet.",
    },
    "tts_usage_close": {
        "vi": "Đóng",
        "en": "Close",
    },
    "preview_label": {
        "vi": "🚂 Lô Hàng Chờ Lên Tàu (✨ New | 🔄 Update | ⚠️ Trùng mờ):",
        "en": "🚂 Cargo Waiting for Train (✨ New | 🔄 Update | ⚠️ Partial match):",
    },
    "preview_range_from": {
        "vi": "🔢 Từ:",
        "en": "🔢 From:",
    },
    "preview_range_to": {
        "vi": "đến:",
        "en": "to:",
    },
    "preview_ready": {
        "vi": "✅ Sẵn sàng: {count} thẻ",
        "en": "✅ Ready: {count} cards",
    },

    # ── Import Buttons ──────────────────────────────────
    "btn_import": {
        "vi": "🚀 XUẤT BẾN (NẠP VÀO ANKI)",
        "en": "🚀 DEPART (LOAD INTO ANKI)",
    },
    "ai_input_accessible_name": {
        "vi": "Văn bản nguồn cho AI",
        "en": "AI source text",
    },
    "search_accessible_name": {
        "vi": "Tìm kiếm thẻ chờ xuất xưởng",
        "en": "Search cards awaiting import",
    },
    "accessibility_control_description": {
        "vi": "Dùng phím Tab để chuyển điều khiển, Space hoặc Enter để kích hoạt.",
        "en": "Use Tab to move between controls and Space or Enter to activate.",
    },
    "model_rebuilt": {
        "vi": "✅ Đã tái tạo model: {model}",
        "en": "✅ Rebuilt model: {model}",
    },
    "model_created": {
        "vi": "✅ Đã tạo model mới: {model}",
        "en": "✅ Created model: {model}",
    },
    "ai_set_session_input_label": {
        "vi": "Giới hạn ký tự đầu vào mỗi phiên AI",
        "en": "AI session input-character limit",
    },
    "ai_set_session_input_tip": {
        "vi": "Chặn phiên AI khi tổng văn bản vượt giới hạn này; không lưu nội dung văn bản.",
        "en": "Blocks an AI run when its total text exceeds this limit; no text is stored.",
    },
    "ai_set_session_tokens_label": {
        "vi": "Ngân sách token mỗi phiên AI",
        "en": "AI session token budget",
    },
    "ai_set_session_tokens_tip": {
        "vi": "Áp dụng cho tổng ước tính trước khi chạy và usage do provider báo về trong phiên hiện tại.",
        "en": "Applies to the pre-run estimate and provider-reported usage in this session.",
    },
    "ai_set_session_cost_label": {
        "vi": "Ngân sách chi phí mỗi phiên AI (USD, 0 = không giới hạn)",
        "en": "AI session cost budget (USD, 0 = unlimited)",
    },
    "ai_set_session_cost_tip": {
        "vi": "Chỉ theo dõi token/chi phí tổng hợp, không lưu prompt hay phản hồi AI.",
        "en": "Tracks aggregate tokens/cost only; prompts and AI responses are never stored.",
    },
    "preview_suffix_near_duplicate": {
        "vi": " (gần giống: {match}, {score:.0%} — cần xem lại)",
        "en": " (similar to: {match}, {score:.0%} — review needed)",
    },
    "btn_rollback_import": {
        "vi": "↩️ HOÀN TÁC BATCH VỪA IMPORT",
        "en": "↩️ UNDO LAST IMPORT BATCH",
    },
    "btn_cancel": {
        "vi": "⏹️ DỪNG LẠI",
        "en": "⏹️ STOP",
    },
    "confirm_import_preview": {
        "vi": "Bạn sắp import {new} note mới và cập nhật {updates} note.\\n\\n"
              "Bạn có thể hoàn tác các note mới tạo của batch này trong phiên Forge hiện tại. "
              "Các note cập nhật và file audio không được tự động hoàn tác.\\n\\nTiếp tục?",
        "en": "You are about to import {new} new notes and update {updates} notes.\\n\\n"
              "You can undo the newly created notes from this batch while this Forge window remains open. "
              "Updates and audio files cannot be undone automatically.\\n\\nContinue?",
    },
    "confirm_ai_budget": {
        "vi": "Phiên AI này ước tính {calls} lần gọi, tối đa {tokens:,} token và ${cost:.4f}.\n"
              "Ngân sách còn lại: {remaining_tokens:,} token, ${remaining_cost:.4f}.\n\n"
              "Ước tính chỉ dùng độ dài văn bản và cấu hình model; không lưu prompt hay phản hồi. Tiếp tục?",
        "en": "This AI session is estimated at {calls} call(s), up to {tokens:,} tokens and ${cost:.4f}.\n"
              "Remaining budget: {remaining_tokens:,} tokens, ${remaining_cost:.4f}.\n\n"
              "The estimate uses only text length and model settings; prompts and responses are not stored. Continue?",
    },
    "ai_budget_blocked": {
        "vi": "Yêu cầu AI vượt giới hạn phiên. Giới hạn hiện tại: {input_limit:,} ký tự, {token_limit:,} token, ${cost_limit:.2f}.\n"
              "Hãy giảm nội dung hoặc điều chỉnh giới hạn trong Cài Đặt AI.",
        "en": "The AI request exceeds the session limits: {input_limit:,} characters, {token_limit:,} tokens, ${cost_limit:.2f}.\n"
              "Reduce the content or adjust the limits in AI Settings.",
    },
    "ai_budget_estimate_failed": {
        "vi": "Không thể ước tính ngân sách AI an toàn. Yêu cầu chưa được gửi.",
        "en": "Could not safely estimate the AI budget. The request was not sent.",
    },
    "confirm_rollback_import": {
        "vi": "Hoàn tác {count} note mới tạo bởi batch import gần nhất?\\n\\n"
              "Các note đã cập nhật và file audio không bị thay đổi.",
        "en": "Undo the {count} notes created by the latest import batch?\\n\\n"
              "Updated notes and audio files will not be changed.",
    },
    "rollback_import_done": {
        "vi": "↩️ Đã hoàn tác {count} note mới tạo từ batch gần nhất.",
        "en": "↩️ Undid {count} notes created by the latest batch.",
    },
    "rollback_import_failed": {
        "vi": "Không thể hoàn tác batch import: {error}",
        "en": "Could not undo the import batch: {error}",
    },

    # ── Dialog Titles ───────────────────────────────────
    "dlg_ai_settings": {
        "vi": "⚙️ Cài Đặt AI — API Key & Model",
        "en": "⚙️ AI Settings — API Key & Model",
    },
    "dlg_ai_preview": {
        "vi": "🔍 Xem Trước & Chỉnh Sửa — {count} Từ Vựng",
        "en": "🔍 Preview & Edit — {count} Vocabulary",
    },
    "dlg_diff_meaning": {
        "vi": "🔍 Báo Cáo Nghĩa Khác — Xác Nhận Thêm Từ Vựng",
        "en": "🔍 Diff Meaning Report — Confirm Adding Vocabulary",
    },
    "dlg_ai_chat": {
        "vi": "💬 AI Chat — Trợ Lý Anki Thông Minh",
        "en": "💬 AI Chat — Smart Anki Assistant",
    },
    "dlg_batch": {
        "vi": "📋 Batch Xử Lý Từ Vựng Lớn",
        "en": "📋 Batch Large Vocabulary Processing",
    },

    # ── Messages ────────────────────────────────────────
    "msg_import_success": {
        "vi": "🚀 XUẤT XƯỞNG THÀNH CÔNG! [{language}]\n──────────────────────────────\n✨ Thêm mới   : {added} thẻ\n🔄 Cập nhật  : {updated} thẻ\n🎵 Audio      : {audio} file\n",
        "en": "🚀 EXPORT COMPLETE! [{language}]\n──────────────────────────────\n✨ New        : {added} cards\n🔄 Updated    : {updated} cards\n🎵 Audio      : {audio} files\n",
    },
    "msg_no_api_key": {
        "vi": "Bạn chưa cấu hình API Key.\n\nNếu dùng DeepSeek/OpenAI/OpenRouter: cần API Key.\nNếu dùng Ollama/LM Studio local: có thể để trống.\n\nMở Cài Đặt AI?",
        "en": "No API Key configured.\n\nFor DeepSeek/OpenAI/OpenRouter: API Key required.\nFor Ollama/LM Studio local: can be empty.\n\nOpen AI Settings?",
    },
    "msg_reasoner_warning": {
        "vi": "⚠️ Bạn đang dùng model '{model}'.\nModel này suy nghĩ rất kỹ trước khi trả lời,\ncó thể mất 3-10 phút. Hãy kiên nhẫn chờ đợi.\n\n💡 Mẹo: Chuyển sang 'deepseek-v4-flash' để nhanh hơn.",
        "en": "⚠️ You are using model '{model}'.\nThis model thinks carefully before responding,\nmay take 3-10 minutes. Please be patient.\n\n💡 Tip: Switch to 'deepseek-v4-flash' for faster results.",
    },
    "msg_history_count": {
        "vi": "📚 Lịch sử: {count} từ vựng đã có",
        "en": "📚 History: {count} existing vocabulary",
    },

    # ── AI Status ───────────────────────────────────────
    "status_scanning_deck": {
        "vi": "🔍 Đang quét deck Anki...",
        "en": "🔍 Scanning Anki deck...",
    },
    "status_calling_ai": {
        "vi": "⏳ Đang gọi AI...",
        "en": "⏳ Calling AI...",
    },
    "status_deck_count": {
        "vi": "📚 Deck có {count} từ → AI sẽ tránh trùng",
        "en": "📚 Deck has {count} words → AI will avoid duplicates",
    },
    "status_connecting": {
        "vi": "Đang kết nối...",
        "en": "Connecting...",
    },
    "status_cancelled": {
        "vi": "⏹ Đã dừng sau {elapsed}",
        "en": "⏹ Stopped after {elapsed}",
    },

    # ── Error Messages ──────────────────────────────────
    "err_no_words": {
        "vi": "⚠️ Không có từ vựng nào sau khi chỉnh sửa.",
        "en": "⚠️ No vocabulary after editing.",
    },
    "err_no_text": {
        "vi": "⚠️ Vui lòng dán văn bản vào ô trên trước.",
        "en": "⚠️ Please paste text in the box above first.",
    },
    "small_run_source_too_large": {
        "vi": "Nguồn hiện có {length} ký tự. Chế độ học tập trung chỉ nhận tối đa {limit} ký tự mỗi lượt. Hãy giữ lại một đoạn hoặc vài dòng bạn muốn học ngay rồi bấm tạo lại.",
        "en": "The source has {length} characters. Focused learning accepts at most {limit} characters per run. Keep one passage or a few lines you want to study now, then create again.",
    },
    "err_file_read": {
        "vi": "Lỗi đọc file: {error}",
        "en": "File read error: {error}",
    },

    # ── Deck Manager ─────────────────────────────────────
    "deck_manage_btn": {
        "vi": "🗂️ Deck Center",
        "en": "🗂️ Deck Center",
    },
    "deck_refresh_btn": {
        "vi": "🔄",
        "en": "🔄",
    },
    "deck_manage_title": {
        "vi": "🗂️ Deck Center — Parent / Sub",
        "en": "🗂️ Deck Center — Parent / Sub",
    },
    "deck_manage_desc": {
        "vi": "Quản lý Parent/Sub Deck hoặc mở AI Blueprint để đề xuất cây từ nguồn H1–H6.",
        "en": "Manage Parent/Sub Decks or open AI Blueprint to propose a tree from H1–H6 sources.",
    },
    "deck_col_name": {
        "vi": "Deck",
        "en": "Deck",
    },
    "deck_col_cards": {
        "vi": "Thẻ",
        "en": "Cards",
    },
    "deck_add_parent": {
        "vi": "➕ Tạo Parent",
        "en": "➕ Add Parent",
    },
    "deck_add_sub": {
        "vi": "📁 Tạo Sub",
        "en": "📁 Add Sub",
    },
    "deck_rename": {
        "vi": "✏️ Đổi tên",
        "en": "✏️ Rename",
    },
    "deck_move_to": {
        "vi": "↳ Chuyển vào...",
        "en": "↳ Move into...",
    },
    "deck_move_to_tip": {
        "vi": "Chuyển các deck đã tích vào một deck đích; toàn bộ sub deck đi cùng",
        "en": "Move checked deck roots under a destination deck; their complete sub-trees move with them",
    },
    "deck_detach": {
        "vi": "⇱ Tách ra gốc",
        "en": "⇱ Make root",
    },
    "deck_detach_tip": {
        "vi": "Tách các deck đã tích thành deck cha ở cây gốc",
        "en": "Detach checked deck roots so they become top-level decks",
    },
    "deck_move_title": {
        "vi": "Di chuyển deck",
        "en": "Move decks",
    },
    "deck_move_root": {
        "vi": "(Cây gốc — deck cha)",
        "en": "(Top level — parent deck)",
    },
    "deck_move_destination_prompt": {
        "vi": "Chuyển các deck đã chọn đến:",
        "en": "Move selected decks to:",
    },
    "deck_move_confirm": {
        "vi": "Chuyển deck đã chọn và toàn bộ sub deck vào '{destination}'? Thẻ và lịch học không bị thay đổi.",
        "en": "Move the selected deck and its complete sub-tree into '{destination}'? Cards and scheduling stay unchanged.",
    },
    "deck_move_confirm_many": {
        "vi": "Chuyển {count} deck đã chọn (kèm sub deck) vào '{destination}'? Thẻ và lịch học không bị thay đổi.",
        "en": "Move {count} selected deck roots (with their sub-trees) into '{destination}'? Cards and scheduling stay unchanged.",
    },
    "deck_moved": {
        "vi": "✅ Đã chuyển {count} deck đến {destination}",
        "en": "✅ Moved {count} deck(s) to {destination}",
    },
    "deck_move_failed": {
        "vi": "Không thể di chuyển: đích không hợp lệ, gây vòng lặp hoặc đã có deck trùng tên.",
        "en": "Could not move: the destination is invalid, would create a cycle, or already has a deck with that name.",
    },
    "deck_delete": {
        "vi": "🗑 Xóa đã tích",
        "en": "🗑 Delete checked",
    },
    "deck_refresh": {
        "vi": "🔄 Làm mới",
        "en": "🔄 Refresh",
    },
    "deck_add_parent_title": {
        "vi": "Tạo Parent Deck",
        "en": "Add Parent Deck",
    },
    "deck_add_parent_prompt": {
        "vi": "Tên deck cha:",
        "en": "Parent deck name:",
    },
    "deck_add_sub_title": {
        "vi": "Tạo Sub Deck",
        "en": "Add Sub Deck",
    },
    "deck_add_sub_prompt": {
        "vi": "Tên sub deck (trong '{parent}'):",
        "en": "Sub deck name (inside '{parent}'):",
    },
    "deck_add_sub_tip": {
        "vi": "Tạo sub deck bên trong deck đang chọn",
        "en": "Create a sub deck inside the selected deck",
    },
    "deck_rename_title": {
        "vi": "Đổi Tên Deck",
        "en": "Rename Deck",
    },
    "deck_rename_prompt": {
        "vi": "Tên mới:",
        "en": "New name:",
    },
    "deck_delete_title": {
        "vi": "Xóa Deck",
        "en": "Delete Deck",
    },
    "deck_delete_confirm": {
        "vi": "Xóa deck '{name}' và toàn bộ sub deck + thẻ bên trong?\nHành động này không thể hoàn tác.",
        "en": "Delete deck '{name}' and all sub decks + cards inside?\nThis action cannot be undone.",
    },
    "deck_select_first": {
        "vi": "⚠️ Chọn một deck trước",
        "en": "⚠️ Select a deck first",
    },
    "deck_created": {
        "vi": "✅ Đã tạo deck: {name}",
        "en": "✅ Deck created: {name}",
    },
    "deck_renamed": {
        "vi": "✅ Đã đổi tên: {old} → {new}",
        "en": "✅ Renamed: {old} → {new}",
    },
    "deck_deleted": {
        "vi": "🗑 Đã xóa deck: {name}",
        "en": "🗑 Deck deleted: {name}",
    },
    "deck_select_all": {
        "vi": "☑ Chọn tất cả",
        "en": "☑ Select all",
    },
    "deck_select_all_tip": {
        "vi": "Tích toàn bộ deck cha và deck con đang hiển thị",
        "en": "Check every visible parent and child deck",
    },
    "deck_clear_selection": {
        "vi": "☐ Bỏ chọn",
        "en": "☐ Clear checks",
    },
    "deck_clear_selection_tip": {
        "vi": "Bỏ toàn bộ dấu tích; không thay đổi deck",
        "en": "Clear all checks without changing decks",
    },
    "deck_selected_count": {
        "vi": "☑ Đã tích {count} deck",
        "en": "☑ {count} decks checked",
    },
    "deck_delete_many_confirm": {
        "vi": "Xóa {count} deck đã tích? Nếu đã tích cả deck cha và con, chỉ deck cha được xóa vì Anki đã xóa toàn bộ deck con và thẻ bên trong. Hành động này không thể hoàn tác.",
        "en": "Delete {count} checked decks? When both a parent and child are checked, only the parent is deleted because Anki also deletes its child decks and cards. This cannot be undone.",
    },
    "deck_deleted_many": {
        "vi": "🗑 Đã xóa {count} deck đã chọn",
        "en": "🗑 Deleted {count} selected decks",
    },
    "deck_count_parents": {
        "vi": "✅ {count} deck cha",
        "en": "✅ {count} parent decks",
    },

    # ── Main Window Toolbar ──────────────────────────────
    "brand_label": {
        "vi": "⚒️ BENTO FORGE",
        "en": "⚒️ BENTO FORGE",
    },
    "btn_theme": {
        "vi": "🎨 Giao diện",
        "en": "🎨 Theme",
    },
    "btn_theme_tip": {
        "vi": "Tùy chỉnh giao diện glassmorphism (theme, màu nhấn, độ trong, cỡ chữ, bo góc)",
        "en": "Customize glassmorphism theme (theme, accent color, glass level, font size, corner radius)",
    },
    "btn_snap_max": {
        "vi": "⛶ Phóng to",
        "en": "⛶ Maximize",
    },
    "btn_snap_max_tip": {
        "vi": "Phóng to toàn màn hình",
        "en": "Maximize to full screen",
    },
    "lbl_tip": {
        "vi": "💡 Kéo phân cách giữa 2 cột",
        "en": "💡 Drag divider between 2 columns",
    },

    # ── Main Window Selectors ────────────────────────────
    "lang_grp_title": {
        "vi": "🌐 Ngôn ngữ",
        "en": "🌐 Language",
    },
    "mode_grp_title": {
        "vi": "🧭 Router mặc định / Nhập thủ công",
        "en": "🧭 Router fallback / Manual import",
    },
    "factory_card_type_tip": {
        "vi": "Làm fallback khi Router không đủ tín hiệu và chọn Note Type cho JSON nhập thủ công. Dây chuyền AI vẫn có Router Tự động/override riêng.",
        "en": "Used as the router fallback and the note type for manual JSON imports. The AI production line still has its own Auto/manual router.",
    },
    "learning_mode_grp_title": {
        "vi": "🧭 Chế độ học",
        "en": "🧭 Learning Mode",
    },
    "btn_learning_language": {
        "vi": "🌐 Ngôn ngữ",
        "en": "🌐 Language",
    },
    "btn_learning_knowledge": {
        "vi": "🧠 Kiến thức",
        "en": "🧠 Knowledge",
    },
    "btn_mode_vocab": {
        "vi": "📖 Từ vựng",
        "en": "📖 Vocabulary",
    },
    "btn_mode_grammar": {
        "vi": "📘 Ngữ pháp",
        "en": "📘 Grammar",
    },
    "btn_lang_toggle": {
        "vi": "🌐 EN",
        "en": "🌐 VI",
    },
    "btn_lang_toggle_tip": {
        "vi": "Chuyển ngôn ngữ giao diện: Tiếng Việt ⇄ English",
        "en": "Switch UI language: Vietnamese ⇄ English",
    },
    "btn_refresh_deck_tip": {
        "vi": "Làm mới danh sách deck từ Anki",
        "en": "Refresh deck list from Anki",
    },
    "btn_manage_deck_tip": {
        "vi": "Mở Deck Center: quản lý deck và AI đề xuất cây deck tại một nơi.",
        "en": "Open Deck Center for deck management and AI tree proposals in one place.",
    },
    "btn_history": {
        "vi": "📚 Lịch Sử AI",
        "en": "📚 AI History",
    },
    "btn_history_tip": {
        "vi": "Xem lại lịch sử từ vựng đã lưu (AI trích xuất / import) — xem được ngay cả sau khi đóng Factory.\nTích chọn các từ cần và đưa sang trạm Kiểm định & Import.",
        "en": "Review saved vocabulary history (AI extract / import) — viewable even after closing the Factory.\nSelect the required words and send them to Review & Import.",
    },
    "btn_ai_stop_tip": {
        "vi": "Dừng yêu cầu AI đang chạy",
        "en": "Stop the running AI request",
    },
    "btn_ai_attach": {
        "vi": "📎 Nạp file vào nguồn",
        "en": "📎 Load file into source",
    },
    "btn_ai_attach_tip": {
        "vi": "Đính kèm file tài liệu tham khảo (TXT/MD/DOCX/PDF/XLSX/CSV).\nAI sẽ đọc nội dung file để trích xuất từ vựng / ngữ pháp.\nLưu ý: DeepSeek chỉ nhận TEXT → add-on tự trích text từ file tại máy.",
        "en": "Attach reference document file (TXT/MD/DOCX/PDF/XLSX/CSV).\nAI reads the file content to extract vocabulary / grammar.\nNote: DeepSeek only accepts TEXT → the add-on extracts text from the file locally.",
    },
    "btn_ai_attach_clear": {
        "vi": "🧹 Bỏ File",
        "en": "🧹 Remove File",
    },
    "btn_ai_attach_clear_tip": {
        "vi": "Bỏ toàn bộ file đã kẹp và xóa nội dung trong ô AI",
        "en": "Remove all attached files and clear the AI input",
    },
    "btn_verify_tip": {
        "vi": "Kiểm định lô hàng — kiểm tra trùng lặp, cập nhật, từ mới",
        "en": "Verify the batch — check duplicates, updates, new words",
    },
    "btn_rebuild_tip": {
        "vi": "Tái tạo / cập nhật Model Note (template, CSS, fields)",
        "en": "Rebuild / update the Note Model (template, CSS, fields)",
    },
    "btn_diff_meaning_tip": {
        "vi": "Xem các từ vựng có cùng mặt chữ nhưng khác nghĩa để xác nhận thêm",
        "en": "View words with the same spelling but different meanings to confirm adding",
    },
    "btn_select_all": {
        "vi": "✅ Chọn Tất Cả",
        "en": "✅ Select All",
    },
    "btn_select_all_tip": {
        "vi": "Tích chọn tất cả thẻ đang hiển thị (theo bộ lọc)",
        "en": "Select all visible cards (per filter)",
    },
    "btn_select_none": {
        "vi": "☐ Bỏ Chọn",
        "en": "☐ Select None",
    },
    "btn_select_none_tip": {
        "vi": "Bỏ chọn tất cả thẻ đang hiển thị",
        "en": "Deselect all visible cards",
    },
    "lbl_sel_count": {
        "vi": "☑️ Đã chọn: {selected}/{total} thẻ",
        "en": "☑️ Selected: {selected}/{total} cards",
    },
    "btn_cancel_order": {
        "vi": "🗑️ HỦY LÔ HÀNG",
        "en": "🗑️ CANCEL CARGO",
    },
    "btn_cancel_order_tip": {
        "vi": "Chỉ xóa thẻ KHỎI XƯỞNG (danh sách chờ xuất xưởng) — không ảnh hưởng tới Anki.\nThẻ trong xưởng được lưu lại ngay cả khi đóng cửa sổ; chỉ mất khi bấm Hủy Hàng.",
        "en": "Only removes cards FROM THE FACTORY (pending export list) — doesn't affect Anki.\nFactory cards are saved even when the window closes; they're only lost when you click Cancel Order.",
    },
    "cbo_filter_all": {
        "vi": "📂 Tất cả",
        "en": "📂 All",
    },
    "cbo_filter_new": {
        "vi": "✨ Mới",
        "en": "✨ New",
    },
    "cbo_filter_update": {
        "vi": "🔄 Cập nhật",
        "en": "🔄 Update",
    },
    "cbo_filter_conflict": {
        "vi": "⚠️ Trùng mờ",
        "en": "⚠️ Partial match",
    },
    "cbo_filter_diff": {
        "vi": "🔍 Nghĩa khác",
        "en": "🔍 Diff meaning",
    },
    "cbo_filter_tip": {
        "vi": "Lọc nhanh theo loại thẻ sau khi Kiểm Định",
        "en": "Quick filter by card type after Verify",
    },
    "preview_filter_all_levels": {
        "vi": "🎓 Mọi cấp độ",
        "en": "🎓 All levels",
    },
    "preview_filter_all_topics": {
        "vi": "🏷 Mọi chủ đề",
        "en": "🏷 All topics",
    },
    "preview_filter_level_tip": {
        "vi": "Lọc Lô chờ lên tàu theo cấp độ có trong danh sách",
        "en": "Filter the waiting queue by a level present in the list",
    },
    "preview_filter_topic_tip": {
        "vi": "Chọn hoặc gõ một phần chủ đề để lọc Lô chờ lên tàu",
        "en": "Choose or type part of a topic to filter the waiting queue",
    },
    "rng_from_label": {
        "vi": "🔢 Từ số:",
        "en": "🔢 From #:",
    },
    "rng_to_label": {
        "vi": "đến:",
        "en": "to:",
    },
    "rng_hint": {
        "vi": "(đổi khoảng = tự tích chọn)",
        "en": "(changing range auto-selects)",
    },
    "rng_tip": {
        "vi": "Thay đổi khoảng sẽ TỰ ĐỘNG tích chọn các thẻ trong khoảng đó",
        "en": "Changing the range AUTO-selects the cards in that range",
    },
    "study_mode_label": {
        "vi": "🎯 Mode:",
        "en": "🎯 Mode:",
    },
    "srs_layout_label": {
        "vi": "🧠 Lịch SRS:",
        "en": "🧠 SRS schedule:",
    },
    "srs_layout_combo": {
        "vi": "Combo · 1 lịch chung",
        "en": "Combo · one shared schedule",
    },
    "srs_layout_independent": {
        "vi": "Độc lập · 5 lịch",
        "en": "Independent · five schedules",
    },
    "srs_layout_tip": {
        "vi": "Áp dụng cho note nhập mới trong deck này. Combo tạo 1 card; Độc lập tạo 5 card, mỗi kỹ năng có lịch riêng. Note hiện có không tự đổi.",
        "en": "Applies to new notes imported into this deck. Combo creates one card; Independent creates five separately scheduled skills. Existing notes are not changed automatically.",
    },
    "srs_layout_changed": {
        "vi": "Đã đổi mặc định cho note nhập mới; card hiện có và lịch sử học không bị thay đổi.",
        "en": "Default changed for new imports; existing cards and review history were not modified.",
    },
    "srs_migrate_btn": {
        "vi": "Chuyển card cũ",
        "en": "Migrate existing",
    },
    "srs_migrate_tip": {
        "vi": "Chuyển tường minh các note Combo hiện có trong deck sang 5 lịch độc lập. Có thể hoàn tác ngay bằng Undo của Anki.",
        "en": "Explicitly migrate existing Combo notes in this deck to five schedules. The operation can be reverted immediately with Anki Undo.",
    },
    "srs_migrate_confirm": {
        "vi": "Chuyển các note Combo hiện có trong deck này sang SRS độc lập?\n\nCard Nhận diện cũ (ord=0) và toàn bộ lịch sử của nó được giữ nguyên; Anki chỉ sinh thêm 4 card có lịch riêng. Thao tác có checkpoint và có thể Undo ngay.",
        "en": "Migrate existing Combo notes in this deck to independent SRS?\n\nThe existing Recognition card (ord=0) and all of its history are preserved; Anki only generates four new separately scheduled cards. A checkpoint is created for immediate Undo.",
    },
    "srs_migrate_checkpoint": {
        "vi": "Bento Forge: chuyển deck sang SRS độc lập",
        "en": "Bento Forge: migrate deck to independent SRS",
    },
    "srs_legacy_checkpoint": {
        "vi": "Bento Forge: bảo toàn lịch SRS card cũ",
        "en": "Bento Forge: preserve legacy SRS cards",
    },
    "srs_migrate_done": {
        "vi": "✅ Đã chuyển {count} note. Card Nhận diện cũ giữ nguyên lịch sử; 4 lịch kỹ năng mới đã được tạo. Có thể dùng Undo của Anki ngay nếu cần.",
        "en": "✅ Migrated {count} notes. Existing Recognition history was preserved and four new skill schedules were created. Use Anki Undo immediately if needed.",
    },
    "srs_migrate_none": {
        "vi": "Không có note Combo nào cần chuyển; thao tác chạy lại không tạo card trùng.",
        "en": "No Combo notes needed migration; running migration again does not create duplicate cards.",
    },
    "srs_migrate_no_deck": {
        "vi": "Chưa chọn được deck để chuyển.",
        "en": "No deck is selected for migration.",
    },
    "srs_migrate_failed": {
        "vi": "Không thể chuyển SRS: {error}",
        "en": "Could not migrate SRS: {error}",
    },
    "voice_tooltip": {
        "vi": "🎤 Dùng giọng Edge Neural chất lượng cao (cần internet; không tự hạ xuống gTTS)",
        "en": "🎤 Uses high-quality Edge Neural voices (needs internet; never silently downgrades to gTTS)",
    },
    "ai_input_placeholder_vocab": {
        "vi": "📥 Dán một đoạn nhỏ hoặc vài từ muốn học ngay. Mỗi lượt chỉ tạo tối đa 5 thẻ để dễ kiểm tra.",
        "en": "📥 Paste one short passage or a few items to study now. Each run creates at most 5 cards for easy review.",
    },
    "ai_input_placeholder_grammar": {
        "vi": "📥 Dán nguồn học liệu cần phân tích. Router của dây chuyền có thể chọn Ngữ pháp tự động hoặc bạn khóa thủ công.",
        "en": "📥 Paste learning material to analyze. The production-line router can select Grammar automatically or you can lock it manually.",
    },
    "ai_input_placeholder_knowledge": {
        "vi": "📥 Dán ghi chú hoặc tài liệu để tạo thẻ Kiến thức Q&A/Cloze. Nguồn chỉ được giữ khi có trong nội dung.",
        "en": "📥 Paste notes or source material for Knowledge Q&A/Cloze cards. Sources are kept only when supplied.",
    },
    "knowledge_json_input_label": {
        "vi": "🧠 JSON Kiến thức (sẽ preview ở bước workflow)",
        "en": "🧠 Knowledge JSON (preview arrives with the workflow)",
    },
    "knowledge_preview_label": {
        "vi": "🧠 Xem trước thẻ Kiến thức",
        "en": "🧠 Knowledge card preview",
    },
    "item_label_knowledge": {
        "vi": "thẻ Kiến thức",
        "en": "Knowledge cards",
    },
    "knowledge_schema_error": {
        "vi": "JSON Kiến thức không hợp lệ: {error}",
        "en": "Invalid Knowledge JSON: {error}",
    },
    "knowledge_no_valid_cards": {
        "vi": "Không có thẻ Kiến thức hợp lệ để kiểm định.",
        "en": "There are no valid Knowledge cards to verify.",
    },
    "knowledge_deck_required": {
        "vi": "Hãy chọn deck trước khi kiểm định thẻ Kiến thức.",
        "en": "Select a deck before verifying Knowledge cards.",
    },
    "knowledge_verify_summary": {
        "vi": "Sẵn sàng: {new} mới · {update} cập nhật · bỏ qua {duplicate} trùng",
        "en": "Ready: {new} new · {update} updates · {duplicate} duplicates skipped",
    },
    "knowledge_preview_valid": {
        "vi": "✓ {count} thẻ Kiến thức hợp lệ; nguồn thiếu được giữ rỗng.",
        "en": "✓ {count} valid Knowledge cards; missing sources remain empty.",
    },
    "knowledge_rollback_done": {
        "vi": "Đã hoàn tác batch Kiến thức: xóa {removed} thẻ mới, khôi phục {restored} thẻ cập nhật.",
        "en": "Knowledge batch undone: removed {removed} new notes and restored {restored} updates.",
    },
    "status_cache_knowledge": {
        "vi": "Dùng cache: {count} thẻ Kiến thức",
        "en": "Using cache: {count} Knowledge cards",
    },
    "status_new_knowledge": {
        "vi": "Đã tạo {count} thẻ Kiến thức mới",
        "en": "Created {count} new Knowledge cards",
    },
    "worker_progress_knowledge": {
        "vi": "Đang trích xuất thẻ Kiến thức…",
        "en": "Extracting Knowledge cards…",
    },
    "regen_instr_knowledge": {
        "vi": "Tạo lại đúng các thẻ Kiến thức sau từ tài liệu nguồn, giữ schema JSON nghiêm ngặt:\n",
        "en": "Regenerate exactly these Knowledge cards from the source, preserving the strict JSON schema:\n",
    },
    "empty_knowledge": {
        "vi": "AI không trả về thẻ Kiến thức hợp lệ hoặc mới.",
        "en": "AI returned no valid or new Knowledge cards.",
    },
    "cost_label": {
        "vi": "💰 Chi phí AI: {cost} USD · {calls} lượt gọi",
        "en": "💰 AI cost: {cost} USD · {calls} calls",
    },
    "usage_history_open_tip": {
        "vi": "Bấm để xem chi tiết từng lần gọi AI",
        "en": "Click to inspect each AI request",
    },
    "usage_history_title": {
        "vi": "Chi tiết sử dụng AI",
        "en": "AI usage details",
    },
    "usage_history_header": {
        "vi": "📊 Chi tiết sử dụng AI",
        "en": "📊 AI usage details",
    },
    "usage_history_desc": {
        "vi": "Lịch sử chỉ lưu metadata sử dụng; không lưu prompt, phản hồi, API key hoặc URL API.",
        "en": "This history keeps usage metadata only; prompts, responses, API keys, and API URLs are never stored.",
    },
    "usage_filter_model": {
        "vi": "Model:",
        "en": "Model:",
    },
    "usage_filter_operation": {
        "vi": "Công việc:",
        "en": "Task:",
    },
    "usage_filter_date": {
        "vi": "Ngày:",
        "en": "Date:",
    },
    "usage_filter_all": {
        "vi": "Tất cả",
        "en": "All",
    },
    "usage_date_all": {
        "vi": "Mọi ngày",
        "en": "All dates",
    },
    "usage_date_today": {
        "vi": "Hôm nay",
        "en": "Today",
    },
    "usage_date_7d": {
        "vi": "7 ngày qua",
        "en": "Last 7 days",
    },
    "usage_date_30d": {
        "vi": "30 ngày qua",
        "en": "Last 30 days",
    },
    "usage_date_custom": {
        "vi": "Khoảng tùy chọn",
        "en": "Custom range",
    },
    "usage_sort_label": {
        "vi": "Sắp xếp:",
        "en": "Sort:",
    },
    "usage_sort_newest": {
        "vi": "Mới nhất",
        "en": "Newest first",
    },
    "usage_sort_oldest": {
        "vi": "Cũ nhất",
        "en": "Oldest first",
    },
    "usage_sort_cost_high": {
        "vi": "Chi phí cao → thấp",
        "en": "Cost: high to low",
    },
    "usage_sort_cost_low": {
        "vi": "Chi phí thấp → cao",
        "en": "Cost: low to high",
    },
    "usage_sort_input_high": {
        "vi": "Input nhiều → ít",
        "en": "Input: most first",
    },
    "usage_sort_input_low": {
        "vi": "Input ít → nhiều",
        "en": "Input: least first",
    },
    "usage_sort_output_high": {
        "vi": "Output nhiều → ít",
        "en": "Output: most first",
    },
    "usage_sort_output_low": {
        "vi": "Output ít → nhiều",
        "en": "Output: least first",
    },
    "usage_col_model": {
        "vi": "Model",
        "en": "Model",
    },
    "usage_col_time": {
        "vi": "Thời gian",
        "en": "Time",
    },
    "usage_col_duration": {
        "vi": "Xử lý",
        "en": "Duration",
    },
    "usage_col_operation": {
        "vi": "Công việc",
        "en": "Task",
    },
    "usage_col_input": {
        "vi": "Input",
        "en": "Input",
    },
    "usage_col_output": {
        "vi": "Output",
        "en": "Output",
    },
    "usage_col_cost": {
        "vi": "Chi phí thực tế",
        "en": "Actual cost",
    },
    "usage_total": {
        "vi": "Tổng: {calls} lượt · Input {input_tokens:,} · Output {output_tokens:,} · ${total_cost:.8f}",
        "en": "Total: {calls} calls · Input {input_tokens:,} · Output {output_tokens:,} · ${total_cost:.8f}",
    },
    "usage_clear_history": {
        "vi": "🗑 Xóa lịch sử",
        "en": "🗑 Clear history",
    },
    "usage_clear_confirm": {
        "vi": "Xóa toàn bộ lịch sử chi tiết sử dụng AI? Không thể hoàn tác.",
        "en": "Clear all detailed AI usage history? This cannot be undone.",
    },
    "usage_operation_vocab_extraction": {
        "vi": "Trích từ vựng",
        "en": "Vocabulary extraction",
    },
    "usage_operation_grammar_extraction": {
        "vi": "Trích ngữ pháp",
        "en": "Grammar extraction",
    },
    "usage_operation_ai_chat": {
        "vi": "AI chat",
        "en": "AI chat",
    },
    "usage_operation_batch_vocabulary": {
        "vi": "Xử lý batch từ vựng",
        "en": "Batch vocabulary processing",
    },
    "usage_operation_batch_grammar": {
        "vi": "Xử lý batch ngữ pháp",
        "en": "Batch grammar processing",
    },
    "usage_operation_deck_organization": {
        "vi": "Tổ chức deck AI",
        "en": "AI deck organization",
    },
    "usage_operation_unknown": {
        "vi": "Không xác định",
        "en": "Unknown",
    },
    "preview_quality_complete": {
        "vi": "✓ Kiểm tra tự động: {total}/{total} thẻ không có cảnh báo xác định được · {score}/100. Độ đúng nghĩa, ngữ pháp và độ tự nhiên vẫn cần bạn rà soát.",
        "en": "✓ Automated check: {total}/{total} cards have no deterministic warnings · {score}/100. Semantic accuracy, grammar, and naturalness still need your review.",
    },
    "preview_quality_warning": {
        "vi": "⚠️ Kiểm tra tự động: {flagged}/{total} thẻ có {issues} cảnh báo trường/nội dung · {score}/100. Di chuột lên hàng để xem chi tiết; bạn vẫn có thể sửa hoặc import.",
        "en": "⚠️ Automated check: {flagged}/{total} cards have {issues} field/content warnings · {score}/100. Hover a row for details; you can still edit or import.",
    },
    "preview_quality_issue_invalid_card": {
        "vi": "Dữ liệu thẻ không hợp lệ.",
        "en": "Invalid card data.",
    },
    "preview_quality_issue_missing_front": {
        "vi": "Thiếu từ hoặc mẫu ngữ pháp.",
        "en": "Missing the word or grammar pattern.",
    },
    "preview_quality_issue_missing_meaning": {
        "vi": "Thiếu nghĩa.",
        "en": "Missing meaning.",
    },
    "preview_quality_issue_missing_example": {
        "vi": "Thiếu ví dụ.",
        "en": "Missing example.",
    },
    "preview_quality_issue_placeholder_front": {
        "vi": "Từ/mẫu đang là giá trị giữ chỗ (ví dụ N/A hoặc unknown).",
        "en": "The word/pattern is a placeholder value (such as N/A or unknown).",
    },
    "preview_quality_issue_placeholder_meaning": {
        "vi": "Nghĩa đang là giá trị giữ chỗ (ví dụ N/A hoặc unknown).",
        "en": "The meaning is a placeholder value (such as N/A or unknown).",
    },
    "preview_quality_issue_placeholder_example": {
        "vi": "Ví dụ đang là giá trị giữ chỗ (ví dụ N/A hoặc unknown).",
        "en": "The example is a placeholder value (such as N/A or unknown).",
    },
    "preview_quality_issue_meaning_repeats_front": {
        "vi": "Nghĩa giống hệt từ/mẫu; hãy kiểm tra lại bản dịch.",
        "en": "Meaning is identical to the word/pattern; check the translation.",
    },
    "preview_quality_issue_example_wrong_script": {
        "vi": "Ví dụ không có chữ viết của ngôn ngữ đích; hãy kiểm tra ngôn ngữ đầu ra.",
        "en": "Example has no target-language script; check the output language.",
    },
    "preview_quality_issue_target_not_in_example": {
        "vi": "Từ tiếng Trung không xuất hiện trong ví dụ.",
        "en": "The Chinese headword does not appear in the example.",
    },
    "preview_quality_issue_pattern_not_in_example": {
        "vi": "Mẫu ngữ pháp dạng nguyên văn không xuất hiện trong ví dụ.",
        "en": "The literal grammar pattern does not appear in the example.",
    },
    "preview_quality_issue_example_is_only_target": {
        "vi": "Ví dụ chỉ lặp lại từ/mẫu, chưa có ngữ cảnh.",
        "en": "Example only repeats the word/pattern and provides no context.",
    },
    "preview_quality_issue_duplicate_examples": {
        "vi": "Hai ví dụ trùng nội dung; hãy bỏ ví dụ không có information gain riêng.",
        "en": "Two examples duplicate each other; remove the one with no independent information gain.",
    },
    "preview_quality_issue_missing_pronunciation": {
        "vi": "Thiếu IPA tiếng Anh.",
        "en": "Missing English IPA.",
    },
    "preview_quality_issue_missing_pinyin": {
        "vi": "Thiếu pinyin.",
        "en": "Missing pinyin.",
    },
    "preview_quality_issue_missing_furigana": {
        "vi": "Thiếu furigana cho từ có kanji.",
        "en": "Missing furigana for a kanji headword.",
    },
    "preview_quality_issue_missing_reading": {
        "vi": "Thiếu cách đọc của mẫu ngữ pháp.",
        "en": "Missing the grammar pattern reading.",
    },
    "preview_quality_issue_missing_romanization": {
        "vi": "Thiếu Revised Romanization.",
        "en": "Missing Revised Romanization.",
    },
    "preview_quality_issue_romanization_contains_hyphen": {
        "vi": "Romanization có dấu gạch nối; Bento Forge dùng Revised Romanization không gạch nối.",
        "en": "Romanization contains a hyphen; Bento Forge uses unhyphenated Revised Romanization.",
    },
    "preview_quality_issue_confusion_candidate": {
        "vi": "Confusion Guard: deck đã có mục dễ nhầm ({candidates}). Hãy kiểm tra contrast; cảnh báo này không chặn import.",
        "en": "Confusion Guard: the deck contains a confusable item ({candidates}). Review the contrast; this warning never blocks import.",
    },

    # ── Main Window Status / Tooltips ────────────────────
    "status_history_count": {
        "vi": "📚 Lịch sử: {count} từ vựng đã có",
        "en": "📚 History: {count} existing vocabulary",
    },
    "status_history_scanning": {
        "vi": "🔍 Đang lập chỉ mục lịch sử ({processed}/{total})…",
        "en": "🔍 Building history index ({processed}/{total})…",
    },
    "status_history_scan_cancelling": {
        "vi": "⏹ Đang dừng quét lịch sử…",
        "en": "⏹ Stopping history scan…",
    },
    "status_history_scan_cancelled": {
        "vi": "⏹ Đã dừng quét lịch sử; không lưu dữ liệu dở dang.",
        "en": "⏹ History scan stopped; partial data was not saved.",
    },
    "status_history_scan_error": {
        "vi": "⚠ Không thể lập chỉ mục lịch sử; sẽ thử lại khi mở lần sau.",
        "en": "⚠ Could not build the history index; it will retry next time.",
    },
    "status_cleared_factory": {
        "vi": "🧹 Đã xóa toàn bộ thẻ trong xưởng.",
        "en": "🧹 Cleared all cards in the factory.",
    },
    "status_done": {
        "vi": "✅ Hoàn tất!",
        "en": "✅ Done!",
    },
    "status_stopping": {
        "vi": "⏸️ Đang dừng...",
        "en": "⏸️ Stopping...",
    },
    "status_reading_file": {
        "vi": "📖 Đang đọc nội dung file...",
        "en": "📖 Reading file content...",
    },
    "status_document_dependency_missing": {
        "vi": "Thiếu {package}. Add-on không tự cài dependency. Hãy sao chép và chạy thủ công: {command}",
        "en": "Missing {package}. The add-on does not install dependencies. Copy and run manually: {command}",
    },
    "status_no_file_content": {
        "vi": "⚠️ Không đọc được nội dung file nào.\n\n{errors}",
        "en": "⚠️ Could not read any file content.\n\n{errors}",
    },
    "status_batch_done": {
        "vi": "✅ Batch: {count} {label} đã xử lý!",
        "en": "✅ Batch: {count} {label} processed!",
    },
    "status_batch_empty": {
        "vi": "⚠️ Batch: Không có kết quả",
        "en": "⚠️ Batch: No results",
    },
    "status_connecting_elapsed": {
        "vi": "⏱ {elapsed} | Dự kiến: {estimate} | Đang kết nối...",
        "en": "⏱ {elapsed} | ETA: {estimate} | Connecting...",
    },
    "status_chat_done": {
        "vi": "✅ Hoàn tất sau {elapsed}!",
        "en": "✅ Finished after {elapsed}!",
    },
    "status_chat_error": {
        "vi": "❌ Lỗi sau {elapsed}: {error}",
        "en": "❌ Error after {elapsed}: {error}",
    },
    "status_stopped_ai": {
        "vi": "⏹ Đã dừng sau {elapsed}",
        "en": "⏹ Stopped after {elapsed}",
    },
    "tooltip_stopped_ai": {
        "vi": "⏹ Đã dừng yêu cầu AI.",
        "en": "⏹ Stopped the AI request.",
    },
    "status_poured_vocab": {
        "vi": "✅ Đã đổ {count} từ vựng vào xưởng!",
        "en": "✅ Poured {count} vocabulary into the factory!",
    },
    "status_poured_grammar": {
        "vi": "✅ Đã đưa {count} thẻ ngữ pháp RAW vào Xưởng!",
        "en": "✅ Sent {count} RAW grammar cards to the Factory!",
    },
    "status_pulled_history": {
        "vi": "📥 Đã đưa {count} từ từ lịch sử vào xưởng!",
        "en": "📥 Pulled {count} words from history into the factory!",
    },
    "tooltip_pulled_history": {
        "vi": "📥 Đã đưa {count} từ vào xưởng. Bấm 'Kiểm Định' để kiểm tra & xuất xưởng.",
        "en": "📥 Pulled {count} words into the factory. Click 'Verify' to check & export.",
    },
    "tooltip_switched_grammar": {
        "vi": "📘 Đã chuyển sang Ngữ pháp",
        "en": "📘 Switched to Grammar",
    },
    "tooltip_switched_vocab": {
        "vi": "📖 Đã chuyển sang Từ vựng",
        "en": "📖 Switched to Vocabulary",
    },
    "tooltip_switched_learning_language": {
        "vi": "🌐 Đã chuyển sang chế độ Ngôn ngữ",
        "en": "🌐 Switched to Language mode",
    },
    "tooltip_switched_learning_knowledge": {
        "vi": "🧠 Đã chuyển sang chế độ Kiến thức",
        "en": "🧠 Switched to Knowledge mode",
    },
    "grammar_suffix": {
        "vi": " (Ngữ pháp)",
        "en": " (Grammar)",
    },

    # ── AI Chat Dialog ───────────────────────────────────
    "chat_header_title": {
        "vi": "💬 Trợ Lý AI Anki",
        "en": "💬 Anki AI Assistant",
    },
    "chat_header_sub": {
        "vi": "AI làm việc thông minh, chỉ truy vấn dữ liệu cần thiết",
        "en": "AI works smartly, only queries needed data",
    },
    "chat_error_html": {
        "vi": "<b>❌ Lỗi:</b><br>{error}",
        "en": "<b>❌ Error:</b><br>{error}",
    },
    "chat_vocab_group": {
        "vi": "📝 AI Đề Xuất {count} Từ Vựng",
        "en": "📝 AI Suggested {count} Vocabulary",
    },
    "chat_grammar_group": {
        "vi": "📝 AI Đề Xuất {count} Thẻ Ngữ Pháp",
        "en": "📝 AI Suggested {count} Grammar Cards",
    },
    "chat_vocab_hint": {
        "vi": "AI đã trích xuất từ vựng từ phản hồi. Bạn có thể <b>đổ vào xưởng</b> để import vào Anki.",
        "en": "AI extracted vocabulary from the reply. You can <b>pour it into the factory</b> to import into Anki.",
    },
    "chat_grammar_hint": {
        "vi": "AI đã trích xuất cấu trúc ngữ pháp. Bạn có thể đưa dữ liệu RAW vào Xưởng để kiểm định trước khi import.",
        "en": "AI extracted grammar patterns. You can send the RAW data to the Factory for validation before import.",
    },
    "chat_close": {
        "vi": "❌ Đóng",
        "en": "❌ Close",
    },
    "chat_accept": {
        "vi": "✅ Đổ {count} Từ Vựng Vào Xưởng",
        "en": "✅ Pour {count} Vocabulary Into Factory",
    },
    "chat_accept_grammar": {
        "vi": "✅ Đưa {count} Thẻ Ngữ Pháp Vào Xưởng",
        "en": "✅ Send {count} Grammar Cards Into Factory",
    },
    "chat_copy": {
        "vi": "📋 Copy Phản Hồi",
        "en": "📋 Copy Reply",
    },
    "chat_copied_tip": {
        "vi": "✅ Đã copy phản hồi!",
        "en": "✅ Reply copied!",
    },
    "chat_no_reply": {
        "vi": "Không có phản hồi.",
        "en": "No reply.",
    },
    "chat_card_warning_truncation": {
        "vi": "⚠️ Dữ liệu thẻ bị cắt nên không được đưa vào Xưởng. Phần trả lời chat còn lại vẫn được giữ.",
        "en": "⚠️ The card data was truncated and was not sent to the Factory. The remaining chat reply is still shown.",
    },
    "chat_card_warning_schema": {
        "vi": "⚠️ Dữ liệu thẻ không khớp ngôn ngữ hoặc loại thẻ hiện tại nên không được đưa vào Xưởng.",
        "en": "⚠️ The card data did not match the current language or card type and was not sent to the Factory.",
    },
    "chat_card_warning_ambiguous": {
        "vi": "⚠️ Phản hồi chứa nhiều payload thẻ nên hệ thống không tự chọn và không đưa thẻ vào Xưởng.",
        "en": "⚠️ The response contained multiple card payloads, so none was selected or sent to the Factory.",
    },
    "chat_card_warning_rejected": {
        "vi": "⚠️ Dữ liệu thẻ không vượt qua kiểm tra an toàn nên không được đưa vào Xưởng.",
        "en": "⚠️ The card data did not pass safety validation and was not sent to the Factory.",
    },

    # ── AI Preview Dialog ────────────────────────────────
    "item_label_vocab": {
        "vi": "Từ Vựng",
        "en": "Vocabulary",
    },
    "item_label_grammar": {
        "vi": "Cấu Trúc Ngữ Pháp",
        "en": "Grammar Pattern",
    },
    "item_label_vocab_lower": {
        "vi": "từ vựng",
        "en": "vocabulary",
    },
    "item_label_grammar_lower": {
        "vi": "cấu trúc ngữ pháp",
        "en": "grammar pattern",
    },
    "item_label_grammar_short": {
        "vi": "cấu trúc",
        "en": "structure",
    },
    "item_label_vocab_short": {
        "vi": "từ",
        "en": "word",
    },
    "preview_header_html": {
        "vi": "🤖 AI đã trích xuất <span style='color:#e67e22;'>{count} {item}</span>",
        "en": "🤖 AI extracted <span style='color:#e67e22;'>{count} {item}</span>",
    },
    "preview_hint": {
        "vi": "<p style='color:#555;'>✏️ <b>Click đúp</b> vào ô để sửa. Chọn thẻ và dùng nút bên dưới để <b>Xóa</b> hoặc <b>Tái Tạo</b> từng thẻ. Có thể <b>Shift/Ctrl+Click</b> để chọn nhiều thẻ.</p>",
        "en": "<p style='color:#555;'>✏️ <b>Double-click</b> a cell to edit. Select cards and use the buttons below to <b>Delete</b> or <b>Regenerate</b> each card. Use <b>Shift/Ctrl+Click</b> to select multiple cards.</p>",
    },
    "btn_accept_all": {
        "vi": "✅ CHẤP NHẬN TẤT CẢ → Đổ Vào Xưởng",
        "en": "✅ ACCEPT ALL → Pour Into Factory",
    },
    "btn_edit_selected": {
        "vi": "✏️ Sửa Thẻ Đã Chọn",
        "en": "✏️ Edit Selected Cards",
    },
    "btn_delete_selected": {
        "vi": "🗑 Xóa Thẻ Đã Chọn",
        "en": "🗑 Delete Selected Cards",
    },
    "btn_regenerate": {
        "vi": "🔄 Tái Tạo Thẻ Đã Chọn",
        "en": "🔄 Regenerate Selected Cards",
    },
    "btn_regenerate_all": {
        "vi": "🔁 Tái Tạo Tất Cả",
        "en": "🔁 Regenerate All",
    },
    "btn_cancel_modal": {
        "vi": "❌ Hủy Bỏ",
        "en": "❌ Cancel",
    },
    "tooltip_select_to_delete": {
        "vi": "⚠️ Vui lòng chọn ít nhất một thẻ để xóa.",
        "en": "⚠️ Please select at least one card to delete.",
    },
    "tooltip_select_to_edit": {
        "vi": "⚠️ Vui lòng chọn một thẻ để sửa.",
        "en": "⚠️ Please select a card to edit.",
    },
    "tooltip_select_to_regen": {
        "vi": "⚠️ Vui lòng chọn ít nhất một thẻ để tái tạo.",
        "en": "⚠️ Please select at least one card to regenerate.",
    },
    "tooltip_no_source_text": {
        "vi": "⚠️ Không tìm thấy văn bản gốc để tái tạo.",
        "en": "⚠️ No source text found to regenerate.",
    },
    "tooltip_deleted": {
        "vi": "✅ Đã xóa {count} thẻ.",
        "en": "✅ Deleted {count} cards.",
    },
    "edit_dlg_title": {
        "vi": "✏️ Sửa Thẻ #{row}",
        "en": "✏️ Edit Card #{row}",
    },
    "btn_cancel_short": {
        "vi": "❌ Hủy",
        "en": "❌ Cancel",
    },
    "btn_save": {
        "vi": "💾 Lưu",
        "en": "💾 Save",
    },
    "btn_set_ai_default": {
        "vi": "⭐ Đặt Provider + Model Mặc Định",
        "en": "⭐ Set Provider + Model Default",
    },
    "btn_set_ai_default_tip": {
        "vi": "Lưu provider và model đang chọn làm mặc định cho lần mở Anki tiếp theo.",
        "en": "Save the selected provider and model as the default for the next Anki launch.",
    },
    "tooltip_updated_card": {
        "vi": "✅ Đã cập nhật thẻ #{row}",
        "en": "✅ Updated card #{row}",
    },
    "regen_instr_grammar": {
        "vi": "CHỈ tái tạo các CẤU TRÚC NGỮ PHÁP sau (giữ nguyên pattern, cải thiện nghĩa + cách dùng + ví dụ):\n",
        "en": "ONLY regenerate the following GRAMMAR PATTERNS (keep pattern, improve meaning + usage + examples):\n",
    },
    "regen_instr_vocab": {
        "vi": "CHỈ tái tạo các từ sau đây (giữ nguyên mặt chữ, cải thiện nghĩa + ví dụ):\n",
        "en": "ONLY regenerate the following words (keep spelling, improve meaning + examples):\n",
    },
    "status_regen_done": {
        "vi": "✅ Đã tái tạo {count} thẻ!",
        "en": "✅ Regenerated {count} cards!",
    },
    "tooltip_regen_done": {
        "vi": "✅ Đã tái tạo {count} thẻ thành công!",
        "en": "✅ Successfully regenerated {count} cards!",
    },
    "tooltip_regen_fail": {
        "vi": "⚠️ AI không trả về kết quả tái tạo.",
        "en": "⚠️ AI didn't return regeneration results.",
    },
    "tooltip_regen_error": {
        "vi": "❌ Lỗi tái tạo: {error}",
        "en": "❌ Regeneration error: {error}",
    },
    "regen_all_confirm_title": {
        "vi": "🔁 Xác Nhận Tái Tạo Tất Cả",
        "en": "🔁 Confirm Regenerate All",
    },
    "regen_all_confirm_msg": {
        "vi": "Điều này sẽ gọi lại AI để trích xuất lại toàn bộ {item}.\nTất cả chỉnh sửa hiện tại sẽ bị mất.\n\nBạn có chắc chắn muốn tiếp tục?",
        "en": "This will call AI again to re-extract all {item}.\nAll current edits will be lost.\n\nAre you sure you want to continue?",
    },
    "tooltip_no_source_text2": {
        "vi": "⚠️ Không tìm thấy văn bản gốc.",
        "en": "⚠️ No source text found.",
    },
    "status_regen_all": {
        "vi": "✅ Tái tạo: {count} {item}!",
        "en": "✅ Regenerated: {count} {item}!",
    },
    "tooltip_regen_all": {
        "vi": "✅ Đã tái tạo toàn bộ: {count} {item}!",
        "en": "✅ Regenerated all: {count} {item}!",
    },
    "tooltip_regen_no_result": {
        "vi": "⚠️ AI không trả về kết quả.",
        "en": "⚠️ AI returned no results.",
    },
    "tooltip_regen_all_error": {
        "vi": "❌ Lỗi: {error}",
        "en": "❌ Error: {error}",
    },
    "tooltip_no_grammar_after": {
        "vi": "⚠️ Không có cấu trúc ngữ pháp nào sau khi chỉnh sửa.",
        "en": "⚠️ No grammar patterns after editing.",
    },
    "tooltip_no_vocab_after": {
        "vi": "⚠️ Không có từ vựng nào sau khi chỉnh sửa.",
        "en": "⚠️ No vocabulary after editing.",
    },

    # ── Supervised large-scale production ────────────────
    "supervised_title_vocab": {
        "vi": "Kho từ quy mô lớn có giám sát",
        "en": "Supervised Large-Scale Vocabulary",
    },
    "supervised_title_grammar": {
        "vi": "Kho ngữ pháp quy mô lớn có giám sát",
        "en": "Supervised Large-Scale Grammar",
    },
    "supervised_header_vocab": {
        "vi": "📦 Kho từ có giám sát — {language}",
        "en": "📦 Supervised vocabulary inventory — {language}",
    },
    "supervised_header_grammar": {
        "vi": "📦 Kho ngữ pháp có giám sát — {language}",
        "en": "📦 Supervised grammar inventory — {language}",
    },
    "supervised_desc": {
        "vi": "Đọc nguồn thành kho chờ, cho bạn chọn chủ đề, cấp độ và số lượng trước mỗi lượt. Không tự đẩy toàn bộ tài liệu vào AI.",
        "en": "Turn the source into a pending inventory, then choose topic, level, and quantity for each run. The full source is never sent blindly.",
    },
    "supervised_source_group": {"vi": "1. Nguồn kho", "en": "1. Inventory source"},
    "supervised_take_workshop": {
        "vi": "⬇ Lấy tài liệu từ Forge Workshop",
        "en": "⬇ Use Forge Workshop source",
    },
    "supervised_take_workshop_tip": {
        "vi": "Chụp nội dung hiện có trong ô Nguồn học liệu của Forge Workshop để AI lập kho có kiểm chứng nguồn.",
        "en": "Snapshot the current Forge Workshop source for source-verified AI inventory scanning.",
    },
    "supervised_open_file": {"vi": "📊 Mở Excel / file", "en": "📊 Open Excel / file"},
    "supervised_open_file_title": {
        "vi": "Chọn tài liệu từ vựng",
        "en": "Choose a vocabulary source",
    },
    "supervised_open_file_filter": {
        "vi": "Bảng tính và tài liệu (*.xlsx *.xls *.csv *.tsv *.txt *.md *.pdf *.docx);;Tất cả file (*)",
        "en": "Spreadsheets and documents (*.xlsx *.xls *.csv *.tsv *.txt *.md *.pdf *.docx);;All files (*)",
    },
    "supervised_analyze": {"vi": "🤖 AI quét & lập kho", "en": "🤖 AI scan & build inventory"},
    "supervised_scan_details": {"vi": "Xem mục đã loại", "en": "Review exclusions"},
    "supervised_scan_details_title": {
        "vi": "Các dòng Cần xem / Bỏ qua",
        "en": "Review / skipped source rows",
    },
    "supervised_no_scan_details": {
        "vi": "AI không đánh dấu dòng nào là Cần xem hoặc Bỏ qua.",
        "en": "AI did not mark any rows for review or skipping.",
    },
    "supervised_scan_detail_row": {
        "vi": "[{decision}]\nỨng viên: {surface}\nLý do: {reason}\nDòng nguồn: {source}",
        "en": "[{decision}]\nCandidate: {surface}\nReason: {reason}\nSource row: {source}",
    },
    "supervised_restore_selected": {
        "vi": "Đưa mục đã chọn sang Cần xem",
        "en": "Move selected items to Review",
    },
    "supervised_restore_empty": {
        "vi": "Chỉ các mục Bỏ qua có ứng viên nguồn mới có thể khôi phục.",
        "en": "Only skipped rows with a source candidate can be restored.",
    },
    "supervised_restored_reason": {
        "vi": "Người dùng khôi phục từ kết quả AI loại.",
        "en": "Restored by the user from AI exclusions.",
    },
    "supervised_restored": {
        "vi": "Đã đưa {count} mục sang Cần xem; hãy chọn bộ lọc Cần xem để kiểm định/sản xuất.",
        "en": "Moved {count} items to Review; choose the Review filter to inspect or produce them.",
    },
    "supervised_none": {"vi": "—", "en": "—"},
    "supervised_source_placeholder": {
        "vi": "Dán danh sách có cột từ/nghĩa/cấp độ/chủ đề, hoặc dùng heading Chủ đề → Cấp độ rồi mỗi dòng một từ…",
        "en": "Paste a list with word/meaning/level/topic columns, or use Topic → Level headings followed by one item per line…",
    },
    "supervised_filter_group": {"vi": "2. Chọn lượt sản xuất", "en": "2. Choose a production run"},
    "supervised_topic": {"vi": "Chủ đề:", "en": "Topic:"},
    "supervised_topic_catalog_pending": {
        "vi": "Danh mục chủ đề chưa khóa. Nút Sản xuất chỉ mở sau khi hệ thống gộp chủ đề trùng, đếm và gán xong từng mục.",
        "en": "The topic catalog is not locked yet. Production unlocks only after duplicate labels are merged, counted, and assigned.",
    },
    "supervised_topic_catalog_ready": {
        "vi": "✓ Đã khóa {topics} chủ đề: {preview}{more}",
        "en": "✓ Locked {topics} topics: {preview}{more}",
    },
    "supervised_topic_catalog_more": {
        "vi": " · và {count} chủ đề khác",
        "en": " · and {count} more",
    },
    "supervised_level": {"vi": "Cấp độ:", "en": "Level:"},
    "supervised_decision": {"vi": "Trạng thái AI:", "en": "AI decision:"},
    "supervised_decision_keep": {"vi": "Giữ", "en": "Keep"},
    "supervised_decision_skip": {"vi": "Bỏ qua", "en": "Skip"},
    "supervised_decision_review": {"vi": "Cần xem", "en": "Review"},
    "supervised_decision_actionable": {
        "vi": "Giữ + Cần xem",
        "en": "Keep + Review",
    },
    "supervised_quantity": {"vi": "Số lượng:", "en": "Quantity:"},
    "supervised_all_topics": {"vi": "Tất cả chủ đề", "en": "All topics"},
    "supervised_all_levels": {"vi": "Tất cả cấp độ", "en": "All levels"},
    "supervised_unclassified": {"vi": "Chưa phân loại", "en": "Unclassified"},
    "supervised_recommended_empty": {
        "vi": "Chưa có mục phù hợp để khuyến nghị.",
        "en": "No matching items to recommend yet.",
    },
    "supervised_recommended": {
        "vi": "Khuyến nghị {count} mục/lượt để dễ kiểm định; hệ thống vẫn chia ngầm {api_size} mục/request AI.",
        "en": "Recommended: {count} items per reviewable run; the system still uses {api_size} items per AI request internally.",
    },
    "supervised_inventory_empty": {
        "vi": "Chưa lập kho. Hãy lấy nguồn Workshop hoặc dán danh sách rồi bấm Lập kho.",
        "en": "No inventory yet. Use the Workshop source or paste a list, then build the inventory.",
    },
    "supervised_inventory_summary": {
        "vi": "Tổng {total} · Đã sản xuất/có sẵn {completed} · Còn {remaining} · Khớp bộ lọc {filtered} · Thiếu chủ đề {unknown_topics} · Thiếu cấp độ {unknown_levels}",
        "en": "Total {total} · Produced/existing {completed} · Remaining {remaining} · Filter match {filtered} · Missing topic {unknown_topics} · Missing level {unknown_levels}",
    },
    "supervised_inventory_summary_ai": {
        "vi": "Nguồn {source_rows} dòng · AI giữ {keep} · Cần xem {review} · Bỏ qua {skip} · Đã sản xuất/có sẵn {completed} · Khớp bộ lọc {filtered}",
        "en": "Source {source_rows} rows · AI kept {keep} · Review {review} · Skipped {skip} · Produced/existing {completed} · Filter match {filtered}",
    },
    "supervised_preview_empty": {
        "vi": "Các mục của lượt sắp sản xuất sẽ hiện ở đây.",
        "en": "Items in the next production run will appear here.",
    },
    "supervised_preview_more": {"vi": "… và {count} mục nữa", "en": "… and {count} more"},
    "supervised_settings_group": {"vi": "3. Thiết lập sản xuất", "en": "3. Production settings"},
    "supervised_turbo_scan": {
        "vi": "⚡ Quét nhanh 1.5×",
        "en": "⚡ 1.5× fast scan",
    },
    "supervised_turbo_scan_tip": {
        "vi": "Tăng số dòng mỗi request 1,5 lần và dùng JSON compact. Bảng Excel có header rõ được đọc cục bộ, không tốn token quét.",
        "en": "Scan 1.5× more rows per request with compact JSON. Header-based Excel tables are read locally with zero scan tokens.",
    },
    "supervised_estimate_empty": {
        "vi": "Chọn một nhóm để xem ước tính lượt sản xuất.",
        "en": "Choose a group to see the production estimate.",
    },
    "supervised_estimate": {
        "vi": "Lượt này: {count} mục → {batches} request AI · khoảng ${cost:.4f} · khoảng {seconds}s",
        "en": "This run: {count} items → {batches} AI requests · about ${cost:.4f} · about {seconds}s",
    },
    "supervised_produce": {"vi": "⚙ Sản xuất lượt đã chọn", "en": "⚙ Produce selected run"},
    "supervised_use_results": {
        "vi": "Đưa {count} kết quả vào Xưởng",
        "en": "Send {count} results to Workshop",
    },
    "supervised_workshop_empty": {
        "vi": "Forge Workshop chưa có tài liệu nguồn.",
        "en": "Forge Workshop has no source document.",
    },
    "supervised_source_required": {
        "vi": "Hãy lấy nguồn từ Workshop hoặc dán danh sách trước.",
        "en": "Use the Workshop source or paste a list first.",
    },
    "supervised_file_loaded": {
        "vi": "Đã mở {name}: {count} dòng có dữ liệu. Đang chuẩn bị quét AI…",
        "en": "Opened {name}: {count} non-empty rows. Preparing AI scan…",
    },
    "supervised_file_error": {
        "vi": "Không thể mở file: {error}",
        "en": "Could not open file: {error}",
    },
    "supervised_no_source_rows": {
        "vi": "File không có dòng dữ liệu để quét.",
        "en": "The file has no data rows to scan.",
    },
    "supervised_no_inventory": {
        "vi": "Không tìm thấy mục hợp lệ. Nguồn nên có mỗi dòng một mục hoặc bảng có cột từ/pattern.",
        "en": "No valid items found. Use one item per line or a table with a word/pattern column.",
    },
    "supervised_analyzed": {
        "vi": "Đã lập kho {count} mục. Chưa gọi AI.",
        "en": "Built an inventory of {count} items. AI has not been called.",
    },
    "supervised_analyzed_ai": {
        "vi": "AI đã lập kho {count} ứng viên: giữ {keep}, cần xem {review}, bỏ qua {skip}. Mặc định chỉ sản xuất mục Giữ.",
        "en": "AI built {count} candidates: kept {keep}, review {review}, skipped {skip}. Only Keep items are produced by default.",
    },
    "supervised_analyzed_local": {
        "vi": "Đã đọc cục bộ {count} mục từ các cột Excel: giữ {keep}, cần xem {review}, bỏ qua {skip}. Quét kho dùng 0 request và 0 token AI.",
        "en": "Read {count} items locally from Excel columns: kept {keep}, review {review}, skipped {skip}. Inventory scan used 0 AI requests and 0 tokens.",
    },
    "supervised_scan_usage": {
        "vi": "Chi phí quét: {requests} request · input {input_tokens} · output {output_tokens} token · ${cost:.4f}.",
        "en": "Scan usage: {requests} requests · {input_tokens} input · {output_tokens} output tokens · ${cost:.4f}.",
    },
    "inventory_ai_empty_source": {
        "vi": "Nguồn không có dòng dữ liệu để AI quét.",
        "en": "The source has no rows for AI scanning.",
    },
    "inventory_ai_malformed_json": {
        "vi": "AI trả về dữ liệu quét không đúng định dạng. Hãy quét lại; hệ thống không dùng kết quả lỗi này.",
        "en": "AI returned malformed scan data. Scan again; the invalid result was not used.",
    },
    "inventory_ai_invalid_shape": {
        "vi": "AI trả về dữ liệu quét thiếu danh sách kết quả. Hãy quét lại; hệ thống không dùng kết quả này.",
        "en": "AI returned scan data without a result list. Scan again; this result was not used.",
    },
    "inventory_ai_invalid_api_response": {
        "vi": "Dịch vụ AI trả về phản hồi API không hợp lệ. Hãy kiểm tra cấu hình endpoint/model rồi thử lại.",
        "en": "The AI service returned an invalid API response. Check the endpoint/model configuration and try again.",
    },
    "inventory_ai_starting": {
        "vi": "Đang khởi động AI Inventory Scanner…",
        "en": "Starting AI Inventory Scanner…",
    },
    "worker_progress_topic_inventory": {
        "vi": "Đang chuẩn hóa chủ đề và lập kho tiền sản xuất…",
        "en": "Normalizing topics and building the pre-production inventory…",
    },
    "worker_progress_topic_inventory_done": {
        "vi": "Đã khóa {topics} chủ đề và duyệt {count} mục; bắt đầu tạo nội dung thẻ…",
        "en": "Locked {topics} topics and approved {count} items; starting card generation…",
    },
    "empty_preproduction_inventory": {
        "vi": "Kho tiền sản xuất không có mục đã được gán chủ đề và duyệt. Hãy dùng Sản xuất có giám sát để xem các mục Cần xem.",
        "en": "The pre-production inventory has no approved topic-assigned items. Use supervised production to review ambiguous items.",
    },
    "inventory_ai_cache_hit": {
        "vi": "Đã dùng kết quả quét đã kiểm chứng trong bộ nhớ đệm ({count} ứng viên).",
        "en": "Used the verified cached scan ({count} candidates).",
    },
    "inventory_ai_scanning": {
        "vi": "AI đang quét phần {current}/{total}…",
        "en": "AI is scanning chunk {current}/{total}…",
    },
    "inventory_ai_complete": {
        "vi": "AI đã quét xong {count} ứng viên có neo nguồn.",
        "en": "AI finished scanning {count} source-anchored candidates.",
    },
    "inventory_local_complete": {
        "vi": "Đã đọc cục bộ {count} mục từ bảng có cấu trúc; không gọi AI.",
        "en": "Read {count} items locally from structured tables; AI was not called.",
    },
    "supervised_nothing_selected": {
        "vi": "Không còn mục nào trong bộ lọc hiện tại.",
        "en": "No items remain in the current filter.",
    },
    "supervised_run_done": {
        "vi": "Đã sản xuất {produced} mục hợp lệ; bộ lọc hiện còn {remaining} mục.",
        "en": "Produced {produced} valid items; {remaining} remain in the current filter.",
    },

    # ── Legacy Batch Dialog strings ──────────────────────
    "batch_title_vocab": {
        "vi": "🚀 Xử Lý Danh Sách Từ Vựng Lớn — Batch AI",
        "en": "🚀 Large Vocabulary Processing — Batch AI",
    },
    "batch_title_grammar": {
        "vi": "🚀 Xử Lý Danh Sách Cấu Trúc Ngữ Pháp Lớn — Batch AI",
        "en": "🚀 Large Grammar Pattern Processing — Batch AI",
    },
    "batch_header_vocab": {
        "vi": "🚀 Xử Lý Danh Sách Từ Vựng Lớn ({language})",
        "en": "🚀 Large Vocabulary Processing ({language})",
    },
    "batch_header_grammar": {
        "vi": "🚀 Xử Lý Danh Sách Cấu Trúc Ngữ Pháp Lớn ({language})",
        "en": "🚀 Large Grammar Pattern Processing ({language})",
    },
    "batch_desc_vocab": {
        "vi": "Paste danh sách từ cần xử lý. AI sẽ làm giàu từng từ với đầy đủ nghĩa, phát âm, ví dụ, chủ đề.",
        "en": "Paste the word list to process. AI enriches each word with full meaning, reading, examples, topic.",
    },
    "batch_desc_grammar": {
        "vi": "Paste danh sách cấu trúc ngữ pháp cần xử lý. AI sẽ làm giàu từng cấu trúc với nghĩa, công thức, cách dùng, ví dụ.",
        "en": "Paste the grammar pattern list to process. AI enriches each pattern with meaning, formula, usage, examples.",
    },
    "batch_format_vocab": {
        "vi": "<b>📋 Format hỗ trợ (mỗi dòng 1 từ):</b><br>• <code>食べる</code> — chỉ từ<br>• <code>食べる : ăn</code> — từ + nghĩa<br>• <code>食べる : ăn : N5</code> — từ + nghĩa + cấp độ<br>• <code>食べる, たべる, ăn, N5</code> — CSV<br>• JSON array: <code>[{{\"front\":\"食べる\",\"meaning\":\"ăn\"}},...]</code><br><b>💡 Tip:</b> Bạn có thể paste hàng trăm, thậm chí hàng nghìn từ. AI sẽ tự động chia batch và xử lý tuần tự.",
        "en": "<b>📋 Supported formats (one word per line):</b><br>• <code>食べる</code> — word only<br>• <code>食べる : eat</code> — word + meaning<br>• <code>食べる : eat : N5</code> — word + meaning + level<br>• <code>食べる, たべる, eat, N5</code> — CSV<br>• JSON array: <code>[{{\"front\":\"食べる\",\"meaning\":\"eat\"}},...]</code><br><b>💡 Tip:</b> You can paste hundreds or even thousands of words. AI auto-splits into batches and processes sequentially.",
    },
    "batch_format_grammar": {
        "vi": "<b>📋 Format hỗ trợ (mỗi dòng 1 cấu trúc):</b><br>• <code>〜てもいい</code> — chỉ cấu trúc<br>• <code>〜てもいい : được phép</code> — cấu trúc + nghĩa<br>• <code>〜てもいい : được phép : N5</code> — + cấp độ<br>• JSON array: <code>[{{\"pattern\":\"〜てもいい\",\"meaning\":\"được phép\"}},...]</code><br><b>💡 Tip:</b> Bạn có thể paste hàng trăm cấu trúc. AI sẽ tự động chia batch và xử lý tuần tự.",
        "en": "<b>📋 Supported formats (one pattern per line):</b><br>• <code>〜てもいい</code> — pattern only<br>• <code>〜てもいい : allowed</code> — pattern + meaning<br>• <code>〜てもいい : allowed : N5</code> — + level<br>• JSON array: <code>[{{\"pattern\":\"〜てもいい\",\"meaning\":\"allowed\"}},...]</code><br><b>💡 Tip:</b> You can paste hundreds of patterns. AI auto-splits into batches and processes sequentially.",
    },
    "batch_list_label_grammar": {
        "vi": "<b>📝 Danh sách cấu trúc ngữ pháp:</b>",
        "en": "<b>📝 Grammar pattern list:</b>",
    },
    "batch_list_label_vocab": {
        "vi": "<b>📝 Danh sách từ vựng:</b>",
        "en": "<b>📝 Vocabulary list:</b>",
    },
    "batch_placeholder_grammar": {
        "vi": "Paste danh sách cấu trúc ngữ pháp vào đây...\n\nVí dụ:\n〜てもいい : được phép : N5\n〜そうです : nghe nói / có vẻ : N4\n〜ことにする : quyết định : N4\n...\n",
        "en": "Paste the grammar pattern list here...\n\nExample:\n〜てもいい : allowed : N5\n〜そうです : hearsay / seems : N4\n〜ことにする : decide : N4\n...\n",
    },
    "batch_placeholder_vocab": {
        "vi": "Paste danh sách từ vựng vào đây...\n\nVí dụ:\n食べる : ăn : N5\n飲む : uống : N5\n勉強する : học : N5\n...\n",
        "en": "Paste the vocabulary list here...\n\nExample:\n食べる : eat : N5\n飲む : drink : N5\n勉強する : study : N5\n...\n",
    },
    "batch_settings_grp": {
        "vi": "⚙️ Cấu hình xử lý",
        "en": "⚙️ Processing settings",
    },
    "batch_batch_size_label": {
        "vi": "Số từ/batch:",
        "en": "Words/batch:",
    },
    "batch_batch_size_tip": {
        "vi": "Số từ mỗi lần gửi AI. Nhỏ hơn = chất lượng cao hơn nhưng chậm hơn.",
        "en": "Number of words sent to AI each time. Smaller = higher quality but slower.",
    },
    "batch_instruction_label": {
        "vi": "Yêu cầu thêm:",
        "en": "Extra instruction:",
    },
    "batch_instruction_placeholder": {
        "vi": "VD: Chỉ lấy từ N3 trở lên, tập trung vào chủ đề kinh doanh...",
        "en": "e.g.: Only N3+ words, focus on business topics...",
    },
    "batch_deck_grp": {
        "vi": "📦 Tổ chức Deck (tự động)",
        "en": "📦 Deck Organization (auto)",
    },
    "batch_chk_auto_deck": {
        "vi": "🤖 AI tự đề xuất & tạo Parent/Sub Deck",
        "en": "🤖 AI auto-suggests & creates Parent/Sub Decks",
    },
    "batch_chk_auto_deck_tip": {
        "vi": "Sau khi xử lý từ vựng, AI sẽ phân tích tất cả từ và đề xuất cấu trúc deck (parent deck + sub decks) theo chủ đề, cấp độ.",
        "en": "After processing vocabulary, AI analyzes all words and suggests a deck structure (parent deck + sub decks) by topic, level.",
    },
    "batch_chk_create_decks": {
        "vi": "📁 Tự động tạo deck trong Anki",
        "en": "📁 Auto-create decks in Anki",
    },
    "batch_chk_create_decks_tip": {
        "vi": "Tự động tạo các deck được đề xuất trong Anki.",
        "en": "Auto-create the suggested decks in Anki.",
    },
    "batch_openrouter_grp": {
        "vi": "🐢 Chế độ OpenRouter Free",
        "en": "🐢 OpenRouter Free Mode",
    },
    "batch_chk_slow_mode": {
        "vi": "Chế độ chậm & ổn định (tránh rate limit 20 req/phút)",
        "en": "Slow & stable mode (avoid 20 req/min rate limit)",
    },
    "batch_chk_slow_mode_tip": {
        "vi": "OpenRouter free giới hạn ~20 request/phút.\nBật: tự đặt delay 3.2s/batch + retry mạnh khi gặp 429.\nTắt: nhanh hơn nhưng dễ bị rate limit.",
        "en": "OpenRouter free limits ~20 requests/minute.\nOn: auto delay 3.2s/batch + strong retry on 429.\nOff: faster but prone to rate limiting.",
    },
    "batch_estimate_hint": {
        "vi": "📊 <b>Ước tính:</b> Nhập danh sách từ ở trên để xem ước tính.",
        "en": "📊 <b>Estimate:</b> Enter the word list above to see an estimate.",
    },
    "batch_estimate_line": {
        "vi": "📊 <b>Ước tính:</b> {total} từ → ~{batches} batch ({size} từ/batch) | ~${cost:.4f} USD | ⏱ ~{seconds}s",
        "en": "📊 <b>Estimate:</b> {total} words → ~{batches} batches ({size} words/batch) | ~${cost:.4f} USD | ⏱ ~{seconds}s",
    },
    "batch_estimate_line_slow": {
        "vi": "⏱ ~{seconds}s ({batches} batch × ~{sec} — chế độ chậm OpenRouter)",
        "en": "⏱ ~{seconds}s ({batches} batches × ~{sec} — OpenRouter slow mode)",
    },
    "btn_close": {
        "vi": "❌ Đóng",
        "en": "❌ Close",
    },
    "btn_stop": {
        "vi": "⏹ Dừng",
        "en": "⏹ Stop",
    },
    "btn_process_ai": {
        "vi": "🚀 Xử Lý Với AI",
        "en": "🚀 Process With AI",
    },
    "batch_status_estimate": {
        "vi": "📊 <b>Ước tính:</b> Nhập danh sách từ ở trên để xem ước tính.",
        "en": "📊 <b>Estimate:</b> Enter the word list above to see an estimate.",
    },
    "tooltip_enter_vocab_list": {
        "vi": "⚠️ Vui lòng nhập danh sách từ vựng.",
        "en": "⚠️ Please enter the vocabulary list.",
    },
    "batch_status_preparing": {
        "vi": "⏳ Đang chuẩn bị...",
        "en": "⏳ Preparing...",
    },
    "batch_status_finished": {
        "vi": "✅ Hoàn tất! {count} {label} đã được AI xử lý.",
        "en": "✅ Done! {count} {label} processed by AI.",
    },
    "batch_status_organizing": {
        "vi": "🧠 AI đang phân tích và tổ chức deck...",
        "en": "🧠 AI is analyzing and organizing decks...",
    },
    "batch_status_organized": {
        "vi": "✅ Đã phân tích xong! {parents} parent deck, {subs} sub deck.",
        "en": "✅ Analysis done! {parents} parent decks, {subs} sub decks.",
    },
    "batch_status_decks_created": {
        "vi": "✅ Đã tạo {count} deck trong Anki!\n{names}",
        "en": "✅ Created {count} decks in Anki!\n{names}",
    },
    "tooltip_decks_created": {
        "vi": "✅ Đã tạo {count} deck!",
        "en": "✅ Created {count} decks!",
    },
    "batch_status_error": {
        "vi": "❌ Lỗi: {error}",
        "en": "❌ Error: {error}",
    },
    "batch_status_stopped": {
        "vi": "⏹️ Đã dừng xử lý.",
        "en": "⏹️ Processing stopped.",
    },
    "batch_done_button": {
        "vi": "✅ Hoàn tất ({count} {label}) — Xem Kết Quả",
        "en": "✅ Done ({count} {label}) — View Results",
    },

    # ── History Dialog ───────────────────────────────────
    "history_title": {
        "vi": "📚 Lịch Sử AI — Từ Vựng Đã Lưu",
        "en": "📚 AI History — Saved Vocabulary",
    },
    "history_header": {
        "vi": "📚 Lịch Sử Từ Vựng Đã Lưu (AI / Import)",
        "en": "📚 Saved Vocabulary History (AI / Import)",
    },
    "history_desc": {
        "vi": "Xem lại các từ đã được AI trích xuất hoặc import. Tích chọn rồi bấm <b>📥 Đưa Vào Xưởng</b> để đưa vào xưởng, sau đó bấm <b>Kiểm Định</b> và <b>XUẤT XƯỞNG</b> lại.",
        "en": "Review words extracted by AI or imported. Check the ones you want, click <b>📥 Pull Into Factory</b> to bring them into the factory, then click <b>Verify</b> and <b>EXPORT</b> again.",
    },
    "history_kind_all": {
        "vi": "📚 Tất cả",
        "en": "📚 All",
    },
    "history_kind_vocab": {
        "vi": "📖 Từ vựng",
        "en": "📖 Vocabulary",
    },
    "history_kind_grammar": {
        "vi": "📘 Ngữ pháp",
        "en": "📘 Grammar",
    },
    "history_search_placeholder": {
        "vi": "🔍 Tìm theo từ / nghĩa / cấp độ...",
        "en": "🔍 Search by word / meaning / level...",
    },
    "history_lang_all": {
        "vi": "📂 Tất cả",
        "en": "📂 All",
    },
    "history_lang_tip": {
        "vi": "Lọc lịch sử theo ngôn ngữ",
        "en": "Filter history by language",
    },
    "history_list_tip": {
        "vi": "Tích chọn các từ muốn đưa vào xưởng",
        "en": "Check the words you want to pull into the factory",
    },
    "btn_select_all2": {
        "vi": "✅ Chọn Tất Cả",
        "en": "✅ Select All",
    },
    "btn_select_none2": {
        "vi": "☐ Bỏ Chọn",
        "en": "☐ Select None",
    },
    "btn_pull_into_factory": {
        "vi": "📥 Đưa Vào Xưởng",
        "en": "📥 Pull Into Factory",
    },
    "btn_pull_into_factory_tip": {
        "vi": "Đưa các từ đã chọn vào xưởng để Kiểm Định & xuất xưởng lại",
        "en": "Pull selected words into the factory to Verify & export again",
    },
    "history_count_visible": {
        "vi": "📚 {count} từ đang hiển thị",
        "en": "📚 {count} words visible",
    },
    "tooltip_no_selection": {
        "vi": "⚠️ Chưa chọn từ nào. Hãy tích chọn các từ cần đưa vào xưởng.",
        "en": "⚠️ No words selected. Check the words you want to pull into the factory.",
    },

    # ── AI Settings Dialog ───────────────────────────────
    "ai_set_api_key_placeholder": {
        "vi": "sk-... (DeepSeek: vào platform.deepseek.com/api_keys để lấy)",
        "en": "sk-... (DeepSeek: get it at platform.deepseek.com/api_keys)",
    },
    "ai_set_secret_store_ready": {
        "vi": "🔒 API key được lưu trong kho thông tin xác thực của hệ điều hành.",
        "en": "🔒 API keys are stored in the operating system credential store.",
    },
    "ai_set_secret_store_unavailable": {
        "vi": "⚠️ Không có kho thông tin xác thực an toàn. API key sẽ không được lưu. Cài thủ công: {command}",
        "en": "⚠️ No secure credential store is available. The API key will not be saved. Install manually: {command}",
    },
    "ai_set_secret_store_save_failed": {
        "vi": "⚠️ Không thể lưu API key an toàn; key không được ghi vào cấu hình.",
        "en": "⚠️ The API key could not be stored securely and was not written to configuration.",
    },
    "ai_set_base_placeholder": {
        "vi": "https://api.deepseek.com/v1 (DeepSeek) hoặc https://api.openai.com/v1",
        "en": "https://api.deepseek.com/v1 (DeepSeek) or https://api.openai.com/v1",
    },
    "btn_clear_ai_cache": {
        "vi": "🗑 Xóa Cache AI",
        "en": "🗑 Clear AI Cache",
    },
    "btn_clear_history": {
        "vi": "🗑 Xóa Lịch Sử",
        "en": "🗑 Clear History",
    },
    "btn_edit_prompts": {
        "vi": "✏️ Sửa Prompt / Schema AI",
        "en": "✏️ Edit AI Prompt / Schema",
    },
    "btn_edit_prompts_tip": {
        "vi": "Sửa System Prompt / JSON Schema cho từng ngôn ngữ và chế độ (từ vựng / ngữ pháp).",
        "en": "Edit System Prompt / JSON Schema per language and mode (vocabulary / grammar).",
    },
    "btn_test_connection": {
        "vi": "🧪 Test Kết Nối",
        "en": "🧪 Test Connection",
    },
    "ai_test_success": {
        "vi": "✅ Kết nối thành công!\n\nModel: {model}\nPhản hồi: {reply}",
        "en": "✅ Connection successful!\n\nModel: {model}\nReply: {reply}",
    },
    "ai_test_error_timeout": {
        "vi": (
            "❌ Lỗi kết nối: Máy chủ phản hồi quá chậm (timeout sau {timeout}s).\n\n"
            "Nguyên nhân thường gặp:\n"
            "• Model đang chọn quá chậm (vd model reasoner suy nghĩ lâu)\n"
            "• Đường truyền mạng chậm hoặc bị chặn\n"
            "• API Base URL sai hoặc không truy cập được\n\n"
            "💡 Gợi ý: thử chọn model nhanh hơn, kiểm tra API Base URL, "
            "hoặc tăng thời gian chờ ở phần Cài Đặt Nâng Cao."
        ),
        "en": (
            "❌ Connection error: Server response timed out (after {timeout}s).\n\n"
            "Common causes:\n"
            "• Selected model is too slow (e.g. reasoner models think longer)\n"
            "• Slow or blocked network connection\n"
            "• Wrong or unreachable API Base URL\n\n"
            "💡 Tip: try a faster model, check the API Base URL, "
            "or increase the timeout in Advanced Settings."
        ),
    },
    "ai_test_error_conn": {
        "vi": (
            "❌ Không thể kết nối: {error}\n\n"
            "Nguyên nhân thường gặp:\n"
            "• Sai API Base URL hoặc thiếu /v1 ở cuối\n"
            "• Không có internet hoặc tường lửa/Proxy chặn\n"
            "• API Key sai hoặc hết hạn\n\n"
            "💡 Gợi ý: kiểm tra lại Base URL và Key trong mục Provider."
        ),
        "en": (
            "❌ Cannot connect: {error}\n\n"
            "Common causes:\n"
            "• Wrong API Base URL or missing /v1 at the end\n"
            "• No internet, or blocked by firewall/Proxy\n"
            "• Invalid or expired API Key\n\n"
            "💡 Tip: double-check the Base URL and Key in the Provider section."
        ),
    },

    # ── Verify Dialog ────────────────────────────────────
    "verify_new_box": {
        "vi": "📥 TỪ MỚI (đang nhập)",
        "en": "📥 NEW WORD (entering)",
    },
    "verify_old_box": {
        "vi": "📚 TỪ ĐÃ CÓ (trong Anki)",
        "en": "📚 EXISTING WORD (in Anki)",
    },

    # ── Prompt Editor ────────────────────────────────────
    "prompt_placeholder": {
        "vi": "Bạn là chuyên gia…",
        "en": "You are an expert…",
    },
    "btn_reset_defaults": {
        "vi": "♻️ Reset Mặc Định",
        "en": "♻️ Reset Defaults",
    },
    "btn_save_all": {
        "vi": "💾 Lưu Tất Cả",
        "en": "💾 Save All",
    },

    # ── Deck Manager extras ──────────────────────────────
    "deck_manage_header": {
        "vi": "🗂️ Deck Center",
        "en": "🗂️ Deck Center",
    },

    # ── Theme Dialog ─────────────────────────────────────
    "theme_title": {
        "vi": "🎨 Tùy chỉnh giao diện",
        "en": "🎨 Customize theme",
    },
    "theme_header": {
        "vi": "🧊 Glassmorphism — Tùy chỉnh giao diện",
        "en": "🧊 Glassmorphism — Customize theme",
    },
    "theme_live_hint": {
        "vi": "Thay đổi áp dụng ngay (live). Nhấn “Áp dụng & Lưu” để lưu.",
        "en": "Changes apply immediately (live). Click “Apply & Save” to save.",
    },
    "theme_preset_label": {
        "vi": "🎚 Chủ đề:",
        "en": "🎚 Theme:",
    },
    "theme_accent_label": {
        "vi": "🎨 Màu nhấn:",
        "en": "🎨 Accent color:",
    },
    "theme_alpha_label": {
        "vi": "💎 Độ trong của kính:",
        "en": "💎 Glass level:",
    },
    "theme_font_label": {
        "vi": "🔠 Cỡ chữ:",
        "en": "🔠 Font size:",
    },
    "theme_radius_label": {
        "vi": "◻️ Bo góc:",
        "en": "◻️ Corner radius:",
    },
    "theme_preview_grp": {
        "vi": "👁 Xem trước",
        "en": "👁 Preview",
    },
    "btn_button_sample": {
        "vi": "Nút nhấn",
        "en": "Button",
    },
    "btn_success_sample": {
        "vi": "Thành công",
        "en": "Success",
    },
    "btn_ghost_sample": {
        "vi": "Phụ",
        "en": "Ghost",
    },
    "theme_combo_sample": {
        "vi": "Từ vựng",
        "en": "Vocabulary",
    },
    "theme_apply_save": {
        "vi": "✅ Áp dụng & Lưu",
        "en": "✅ Apply & Save",
    },
    "theme_cancel": {
        "vi": "Hủy",
        "en": "Cancel",
    },
    "theme_color_dialog_title": {
        "vi": "Chọn màu nhấn",
        "en": "Choose accent color",
    },
    "theme_applied_tip": {
        "vi": "🎨 Đã áp dụng giao diện mới",
        "en": "🎨 New theme applied",
    },

    # ── Main Window extras ───────────────────────────────
    "spin_speed_tip": {
        "vi": "Tốc độ phát audio mặc định cho thẻ học\n(0.25× = chậm nhất, 4.0× = nhanh nhất)",
        "en": "Default audio playback speed for study cards\n(0.25× = slowest, 4.0× = fastest)",
    },
    "search_placeholder": {
        "vi": "🔍 Tìm từ / nghĩa / cấp độ / chủ đề...",
        "en": "🔍 Search word / meaning / level / topic...",
    },
    "sample_json_title": {
        "vi": "💡 Mẫu JSON — {label}",
        "en": "💡 JSON Sample — {label}",
    },
    "choose_type_label": {
        "vi": "Chọn loại:",
        "en": "Choose type:",
    },
    "btn_copy_close": {
        "vi": "📋 Copy & Đóng",
        "en": "📋 Copy & Close",
    },
    "file_dialog_title": {
        "vi": "Chọn file dữ liệu",
        "en": "Choose data file",
    },
    "file_dialog_filter": {
        "vi": "Dữ liệu (*.json *.txt)",
        "en": "Data (*.json *.txt)",
    },
    "preview_suffix_dup_diff": {
        "vi": "  [🔍 Nghĩa khác: mới='{new}' ← cũ='{old}']",
        "en": "  [🔍 Diff meaning: new='{new}' ← old='{old}']",
    },
    "preview_suffix_update": {
        "vi": "  [Cập nhật: {fields}]",
        "en": "  [Update: {fields}]",
    },
    "preview_suffix_partial": {
        "vi": "  [Trùng mờ — vẫn thêm]",
        "en": "  [Partial match — still adding]",
    },
    "tooltip_audio_preview_fail": {
        "vi": "Không thể phát audio preview.",
        "en": "Cannot play audio preview.",
    },
    "tooltip_audio_gen_fail": {
        "vi": "⚠️ Không thể tạo audio. Kiểm tra kết nối internet và edge-tts.",
        "en": "⚠️ Cannot generate audio. Check internet connection and edge-tts.",
    },
    "tooltip_no_cards_ready": {
        "vi": "⚠️ Chưa có thẻ nào sẵn sàng trong xưởng.",
        "en": "⚠️ No cards ready in the factory.",
    },
    "status_cleared_selected": {
        "vi": "🧹 Đã xóa {count} thẻ đã chọn khỏi xưởng.",
        "en": "🧹 Removed {count} selected cards from the factory.",
    },
    "msg_chat_poured": {
        "vi": "🤖 AI Chat Hoàn Tất!\n\n📊 Đã đổ {count} từ vựng vào khung JSON.\n👉 Nhấn <b>'Kiểm Định Lô Hàng'</b> để kiểm tra và import.",
        "en": "🤖 AI Chat Complete!\n\n📊 Poured {count} vocabulary into the JSON box.\n👉 Click <b>'Verify Batch'</b> to check and import.",
    },
    "msg_chat_poured_grammar": {
        "vi": "🤖 AI Chat Hoàn Tất!\n\n📊 Đã đưa {count} thẻ ngữ pháp RAW vào khung JSON.\n👉 Nhấn <b>'Kiểm Định Lô Hàng'</b> để kiểm tra và import.",
        "en": "🤖 AI Chat Complete!\n\n📊 Sent {count} RAW grammar cards to the JSON box.\n👉 Click <b>'Verify Batch'</b> to check and import.",
    },
    "msg_extract_poured": {
        "vi": "🤖 AI Trích Xuất Hoàn Tất!\n\n📊 Đã đổ {count} từ vựng vào khung JSON.\n👉 Nhấn <b>'Kiểm Định Lô Hàng'</b> để kiểm tra và import.",
        "en": "🤖 AI Extraction Complete!\n\n📊 Poured {count} vocabulary into the JSON box.\n👉 Click <b>'Verify Batch'</b> to check and import.",
    },
    "dlg_preview_edit": {
        "vi": "🔍 Xem Trước & Chỉnh Sửa — {count} {item}",
        "en": "🔍 Preview & Edit — {count} {item}",
    },
    "btn_select_all_check": {
        "vi": "☑️ Chọn Tất Cả",
        "en": "☑️ Select All",
    },
    "btn_accept_pour": {
        "vi": "✅ CHẤP NHẬN & ĐỔ VÀO XƯỞNG",
        "en": "✅ ACCEPT & POUR INTO FACTORY",
    },

    # ── AI Settings Dialog ───────────────────────────────
    "ai_set_header_title": {
        "vi": "🤖 Cấu hình OpenAI-compatible API",
        "en": "🤖 Configure OpenAI-compatible API",
    },
    "ai_set_header_sub": {
        "vi": "Hỗ trợ: OpenAI, DeepSeek, Ollama, LM Studio, Claude (qua proxy), OpenRouter, v.v.",
        "en": "Supports: OpenAI, DeepSeek, Ollama, LM Studio, Claude (via proxy), OpenRouter, etc.",
    },
    "ai_set_header_tip": {
        "vi": "💡 Mẹo: Bấm nút <b>DeepSeek</b> bên dưới để tự điền Base URL + Model, sau đó chỉ cần nhập API Key từ <a href='https://platform.deepseek.com/api_keys'>platform.deepseek.com/api_keys</a>",
        "en": "💡 Tip: Click the <b>DeepSeek</b> button below to auto-fill Base URL + Model, then just enter the API Key from <a href='https://platform.deepseek.com/api_keys'>platform.deepseek.com/api_keys</a>",
    },
    "ai_set_api_key_label": {
        "vi": "🔑 API Key:",
        "en": "🔑 API Key:",
    },
    "ai_set_provider_key_note": {
        "vi": "Mỗi nhà cung cấp/endpoint tùy chỉnh có API Key riêng; đổi provider sẽ tự nạp key đã lưu của provider đó.",
        "en": "Each provider/custom endpoint has its own API key; switching provider automatically loads that provider's saved key.",
    },
    "ai_set_show_key": {
        "vi": "👁 Hiện API Key",
        "en": "👁 Show API Key",
    },
    "ai_set_base_label": {
        "vi": "🌐 API Base URL:",
        "en": "🌐 API Base URL:",
    },
    "ai_set_model_label": {
        "vi": "🧠 Model:",
        "en": "🧠 Model:",
    },
    "ai_set_temp_label": {
        "vi": "🌡 Temperature (0-2):",
        "en": "🌡 Temperature (0-2):",
    },
    "ai_set_effort_label": {
        "vi": "🧠 Mức độ suy nghĩ (reasoning_effort):",
        "en": "🧠 Reasoning effort:",
    },
    "ai_set_effort_auto": {
        "vi": "Tự động (không gửi tham số)",
        "en": "Auto (no parameter sent)",
    },
    "ai_set_effort_low": {
        "vi": "Thấp — nhanh, rẻ, ít token",
        "en": "Low — fast, cheap, fewer tokens",
    },
    "ai_set_effort_medium": {
        "vi": "Trung bình",
        "en": "Medium",
    },
    "ai_set_effort_high": {
        "vi": "Cao — sâu, chất lượng tốt, tốn token",
        "en": "High — deep, better quality, more tokens",
    },
    "ai_set_chunk_label": {
        "vi": "📏 Độ dài xử lý mỗi lần gọi (ký tự):",
        "en": "📏 Chars processed per call:",
    },
    "ai_set_preset_grp": {
        "vi": "⚡ Presets",
        "en": "⚡ Presets",
    },
    "ai_set_preset_ollama": {
        "vi": "Ollama (local)",
        "en": "Ollama (local)",
    },
    "ai_set_preset_lm": {
        "vi": "LM Studio (local)",
        "en": "LM Studio (local)",
    },
    "ai_set_provider_label": {
        "vi": "🏭 Nhà cung cấp AI (Preset):",
        "en": "🏭 AI Provider (Preset):",
    },
    "ai_set_provider_tip": {
        "vi": "Chọn nhà cung cấp AI. Model sẽ tự động hiển thị đúng theo nhà cung cấp.",
        "en": "Choose an AI provider. Models auto-match the selected provider.",
    },
    "ai_set_provider_custom": {
        "vi": "Tùy chỉnh (Custom)",
        "en": "Custom",
    },
    "ai_set_provider_custom_note": {
        "vi": "Bạn tự nhập API Base URL + Model tương thích OpenAI (VD: proxy/private gateway).",
        "en": "Enter an API Base URL + model compatible with OpenAI (e.g. proxy/private gateway).",
    },
    "ai_set_glow_tip": {
        "vi": "✨ Hover vào dropdown (hoặc đổi nhà cung cấp) để xem viền phát sáng chạy quanh 5 giây!",
        "en": "✨ Hover the dropdown (or switch provider) to see a glow border sweep for 5 seconds!",
    },
    "ai_set_effort_tip": {
        "vi": "Mức độ nỗ lực suy nghĩ của model.\n"
             "Chỉ áp dụng với model hỗ trợ (OpenAI o1/o3/o4...).\n"
             "DeepSeek: deepseek-v4-flash = nhanh/tiết kiệm; deepseek-v4-pro = chất lượng cao hơn.\n"
             "Mức càng cao → chất lượng tốt hơn nhưng tốn NHIỀU token output.",
        "en": "Model reasoning effort level.\n"
              "Only applies to supporting models (OpenAI o1/o3/o4...).\n"
              "DeepSeek: deepseek-v4-flash = fast/economical; deepseek-v4-pro = higher quality.\n"
              "Higher level → better quality but uses MANY more output tokens.",
    },
    "ai_set_chunk_tip": {
        "vi": "Số ký tự tối đa gửi trong 1 request AI (càng nhỏ càng mịn, chất lượng cao hơn).\n"
             "Văn bản DÀI HƠN vẫn được xử lý hết (tự chia đoạn) — con số này chỉ là kích thước mỗi lần gọi.\n"
             "⚠️ ĐỪNG để quá lớn: DeepSeek giới hạn OUTPUT ~8192 token/lần, "
             "chunk lớn → JSON dễ bị CẮT giữa chừng. Khuyên 6k-8k.",
        "en": "Max characters sent per AI request (smaller = finer, higher quality).\n"
              "LONGER text is still fully handled (auto-chunked) — this is just the per-call size.\n"
              "⚠️ Do NOT set too large: DeepSeek caps OUTPUT at ~8192 tokens/call; "
              "large chunks → JSON may get CUT. Recommended 6k-8k.",
    },
    "ai_set_conn_grp": {
        "vi": "🔌 Kết nối API",
        "en": "🔌 API Connection",
    },
    "ai_set_gen_grp": {
        "vi": "⚙️ Tham số sinh",
        "en": "⚙️ Generation",
    },
    "ai_set_session_grp": {
        "vi": "📊 Chính sách phiên",
        "en": "📊 Session policy",
    },
    "ai_set_cache_grp": {
        "vi": "🧹 Bộ nhớ đệm",
        "en": "🧹 Cache",
    },
    "tooltip_cache_cleared": {
        "vi": "✅ Đã xóa toàn bộ cache AI!",
        "en": "✅ All AI cache cleared!",
    },
    "tooltip_history_cleared": {
        "vi": "✅ Đã xóa lịch sử từ vựng!",
        "en": "✅ Vocabulary history cleared!",
    },
    "tooltip_history_clear_fail": {
        "vi": "⚠️ Không thể xóa lịch sử.",
        "en": "⚠️ Could not clear history.",
    },
    "tooltip_saved_config": {
        "vi": "✅ Đã lưu cấu hình AI!",
        "en": "✅ AI config saved!",
    },
    "tooltip_saved_ai_default": {
        "vi": "⭐ Đã lưu Provider + Model mặc định!",
        "en": "⭐ Default provider and model saved!",
    },

    # ── Verify Dialog ────────────────────────────────────
    "verify_edit_label": {
        "vi": "✏️ Chỉnh sửa nhanh (tùy chọn):",
        "en": "✏️ Quick edit (optional):",
    },

    # ── Prompt Editor extras ─────────────────────────────
    "prompt_field_map_tab": {
        "vi": "🗂 Field Map",
        "en": "🗂 Field Map",
    },
    "prompt_system_tab": {
        "vi": "System Prompt",
        "en": "System Prompt",
    },
    "prompt_json_tab": {
        "vi": "JSON Template",
        "en": "JSON Template",
    },

    # ── Verify Dialog ────────────────────────────────────
    "tooltip_no_diff_meaning": {
        "vi": "Không có từ vựng nào thuộc diện 'nghĩa khác' để báo cáo.",
        "en": "No vocabulary falls under 'diff meaning' to report.",
    },
    "verify_title_html": {
        "vi": "🔍 Phát hiện <span style='color:#e67e22;'>{count} từ vựng</span> có cùng mặt chữ nhưng <b>nghĩa khác</b> với từ đã có.",
        "en": "🔍 Found <span style='color:#e67e22;'>{count} vocabulary</span> with the same spelling but <b>different meaning</b> from existing words.",
    },
    "verify_sub_html": {
        "vi": "Chọn những từ bạn muốn <b>cho phép thêm</b> dù trùng mặt chữ. Các từ không chọn sẽ bị loại bỏ.",
        "en": "Select the words you want to <b>allow adding</b> despite duplicate spelling. Unselected words will be removed.",
    },
    "verify_field_spelling": {
        "vi": "Mặt chữ:",
        "en": "Spelling:",
    },
    "verify_field_meaning": {
        "vi": "Nghĩa:",
        "en": "Meaning:",
    },
    "verify_field_level": {
        "vi": "Cấp độ:",
        "en": "Level:",
    },
    "verify_checkbox_label": {
        "vi": "✅ Cho phép thêm từ mới \"{front}\" với nghĩa \"{meaning}\"",
        "en": "✅ Allow adding new word \"{front}\" with meaning \"{meaning}\"",
    },
    "btn_select_all_lower": {
        "vi": "☑️ Chọn tất cả",
        "en": "☑️ Select all",
    },
    "btn_deselect_all_lower": {
        "vi": "☐ Bỏ chọn tất cả",
        "en": "☐ Deselect all",
    },
    "btn_confirm_allow": {
        "vi": "🚀 XÁC NHẬN & CHO QUA",
        "en": "🚀 CONFIRM & ALLOW",
    },

    # ── Prompt Editor ────────────────────────────────────
    "prompt_editor_title": {
        "vi": "✏️ Sửa Prompt, Schema & Field Map AI",
        "en": "✏️ Edit AI Prompt, Schema & Field Map",
    },
    "prompt_editor_header": {
        "vi": "✏️ Prompt, Schema & Field Map AI",
        "en": "✏️ Prompt, Schema & Field Map AI",
    },
    "prompt_editor_sub": {
        "vi": "Chỉnh <b>System Prompt</b>, <b>mẫu JSON</b> và <b>map key → Field Anki</b> cho từng ngôn ngữ. <b>Không cần sửa code.</b>",
        "en": "Edit <b>System Prompt</b>, <b>JSON template</b> and <b>key → Anki Field map</b> per language. <b>No coding needed.</b>",
    },
    "prompt_lang_label": {
        "vi": "🌏 Ngôn ngữ:",
        "en": "🌏 Language:",
    },
    "prompt_json_label": {
        "vi": "📋 Mẫu JSON (schema AI phải tuân theo):",
        "en": "📋 JSON template (schema AI must follow):",
    },
    "prompt_system_label": {
        "vi": "🧠 System Prompt",
        "en": "🧠 System Prompt",
    },
    "prompt_kind_label": {
        "vi": "📦 Loại:",
        "en": "📦 Type:",
    },
    "btn_preview_prompt": {
        "vi": "👁 Xem Prompt Đầy Đủ",
        "en": "👁 View Full Prompt",
    },
    "prompt_fm_key": {
        "vi": "Key JSON (từ template)",
        "en": "JSON Key (from template)",
    },
    "prompt_fm_field": {
        "vi": "Field Anki",
        "en": "Anki Field",
    },
    "prompt_fm_show": {
        "vi": "Hiển thị",
        "en": "Show",
    },

    # ── Worker progress messages ─────────────────────────
    "worker_progress_grammar": {
        "vi": "🤖 Đang gọi AI trích xuất NGỮ PHÁP...",
        "en": "🤖 Calling AI to extract GRAMMAR...",
    },
    "worker_progress_vocab": {
        "vi": "🤖 Đang gọi AI trích xuất từ vựng...",
        "en": "🤖 Calling AI to extract vocabulary...",
    },
    "worker_progress_context": {
        "vi": "🔍 Đang thu thập ngữ cảnh Anki...",
        "en": "🔍 Collecting Anki context...",
    },
    "worker_progress_organize": {
        "vi": "🧠 Đang phân tích từ vựng để tổ chức deck...",
        "en": "🧠 Analyzing vocabulary to organize decks...",
    },
    "worker_progress_create_decks": {
        "vi": "📁 Đang tạo deck trong Anki...",
        "en": "📁 Creating decks in Anki...",
    },
    "worker_progress_empty_deck": {
        "vi": "📚 Deck trống — sẵn sàng gọi AI",
        "en": "📚 Deck empty — ready to call AI",
    },
    "worker_error_no_deck": {
        "vi": "⚠️ AI không đề xuất được cấu trúc deck.",
        "en": "⚠️ AI could not suggest a deck structure.",
    },
    "status_deck_avoid": {
        "vi": "📚 Tránh {count} {label} trong deck...",
        "en": "📚 Avoiding {count} {label} in deck...",
    },
    "empty_grammar": {
        "vi": "⚠️ AI không trích xuất được cấu trúc ngữ pháp nào. Thử văn bản có nội dung rõ ràng hơn.",
        "en": "⚠️ AI could not extract any grammar patterns. Try clearer text.",
    },
    "empty_vocab": {
        "vi": "⚠️ AI không trích xuất được từ vựng nào. Thử văn bản có nội dung rõ ràng hơn.",
        "en": "⚠️ AI could not extract any vocabulary. Try clearer text.",
    },
    "worker_summary_deck": {
        "vi": "📋 Đề xuất: {parents} parent deck, {subs} sub deck",
        "en": "📋 Suggested: {parents} parent decks, {subs} sub decks",
    },

    # ── Study Mode labels (Mode combo + Overview selector) ─
    "lang_src_ja": {
        "vi": "Nhật",
        "en": "Japanese",
    },
    "lang_src_zh": {
        "vi": "中文",
        "en": "Chinese",
    },
    "lang_src_ko": {
        "vi": "한국어",
        "en": "Korean",
    },
    "lang_src_en": {
        "vi": "Anh",
        "en": "English",
    },
    "lang_tgt": {
        "vi": "Việt",
        "en": "English",
    },
    "mode_label_wb": {
        "vi": "Ghép chữ",
        "en": "Word Builder",
    },
    "mode_label_lg": {
        "vi": "Ẩn chữ cái",
        "en": "Letter Gap",
    },
    "mode_label_pron_ja": {
        "vi": "Furigana",
        "en": "Furigana",
    },
    "mode_label_pron_zh": {
        "vi": "Pinyin",
        "en": "Pinyin",
    },
    "mode_label_pron_ko": {
        "vi": "Romanization",
        "en": "Romanization",
    },
    "mode_label_pron_en": {
        "vi": "IPA",
        "en": "IPA",
    },
    "overview_mode_label": {
        "vi": "🎯 Chế độ học:",
        "en": "🎯 Study mode:",
    },

    # ── Complete VI/EN coverage: main workflow ───────────
    "app_title_language": {
        "vi": "Bento Forge — {language}",
        "en": "Bento Forge — {language}",
    },
    "lang_japanese_grammar": {
        "vi": "🇯🇵 Ngữ pháp Tiếng Nhật",
        "en": "🇯🇵 Japanese Grammar",
    },
    "lang_chinese_grammar": {
        "vi": "🇨🇳 Ngữ pháp Tiếng Trung",
        "en": "🇨🇳 Chinese Grammar",
    },
    "lang_korean_grammar": {
        "vi": "🇰🇷 Ngữ pháp Tiếng Hàn",
        "en": "🇰🇷 Korean Grammar",
    },
    "lang_english_grammar": {
        "vi": "🇬🇧 Ngữ pháp Tiếng Anh",
        "en": "🇬🇧 English Grammar",
    },
    "filter_all_levels": {
        "vi": "Tất cả",
        "en": "All",
    },
    "btn_reset_cost": {
        "vi": "↺ Đặt lại",
        "en": "↺ Reset",
    },
    "verify_error_title": {
        "vi": "❌ Lỗi Kiểm Định",
        "en": "❌ Validation Error",
    },
    "verify_error_message": {
        "vi": "Không thể kiểm định dữ liệu:\n\n{error}\n\n{details}",
        "en": "Could not validate the data:\n\n{error}\n\n{details}",
    },
    "verify_summary": {
        "vi": "✨ {new} mới   🔄 {update} cập nhật   ⚠️ {partial} trùng mờ   🔍 {different} nghĩa khác   ❌ {duplicate} bỏ qua",
        "en": "✨ {new} new   🔄 {update} updates   ⚠️ {partial} possible duplicates   🔍 {different} different meanings   ❌ {duplicate} skipped",
    },
    "factory_validation_blocked": {
        "vi": "â›” ÄÃ£ cháº·n {count} má»¥c lá»—i xÃ¡c Ä‘á»‹nh: {categories}.",
        "en": "â›” Blocked {count} deterministic validation failures: {categories}.",
    },
    "study_request_edit_blocked": {
        "vi": "YÃªu cáº§u nÃ y Ä‘ang xá»­ lÃ½; hÃ£y dá»«ng yÃªu cáº§u trÆ°á»›c khi sá»­a hoáº·c xÃ³a.",
        "en": "This request is in progress; stop it before editing or deleting its source turn.",
    },
    "study_latest_turn_other_workspace": {
        "vi": "Lượt mới nhất thuộc workspace còn lại; hãy mở đúng Study Coach hoặc Forge để sửa/xóa.",
        "en": "The latest turn belongs to the other workspace; open the matching Study Coach or Forge surface to edit or delete it.",
    },
    "study_language_required": {
        "vi": "Hãy chọn Ngôn ngữ AI trước khi tạo Study Session.",
        "en": "Choose the AI language before creating a Study Session.",
    },
    "cancel_order_empty": {
        "vi": "ℹ️ Xưởng trống — không có thẻ để hủy.",
        "en": "ℹ️ The factory is empty — there are no cards to discard.",
    },
    "cancel_order_title": {
        "vi": "🗑️ HỦY LÔ HÀNG",
        "en": "🗑️ DISCARD BATCH",
    },
    "cancel_order_message": {
        "vi": "Lô hàng hiện có {total} thẻ chờ xuất xưởng.\n\n☑️ Đã chọn: {selected} thẻ.\n\nChọn thao tác xóa — chỉ xóa khỏi XƯỞNG, không ảnh hưởng đến Anki:",
        "en": "The batch currently has {total} cards waiting to be exported.\n\n☑️ Selected: {selected} cards.\n\nChoose what to remove — this only removes cards from the FACTORY and does not affect Anki:",
    },
    "cancel_order_selected": {
        "vi": "🗑️ Xóa các thẻ đã chọn",
        "en": "🗑️ Remove selected cards",
    },
    "cancel_order_all": {
        "vi": "🧹 Xóa toàn bộ",
        "en": "🧹 Remove all",
    },
    "cancel_order_cancel": {
        "vi": "Hủy",
        "en": "Cancel",
    },
    "cancel_order_no_selection": {
        "vi": "⚠️ Chưa chọn thẻ nào. Hãy tích chọn thẻ hoặc chỉnh khoảng Từ–Đến.",
        "en": "⚠️ No cards selected. Select cards or adjust the From–To range.",
    },
    "import_no_selection": {
        "vi": "⚠️ Không có thẻ nào được chọn để xuất xưởng.",
        "en": "⚠️ No cards are selected for export.",
    },
    "status_generating_audio": {
        "vi": "🎤 Đang tạo {count} file audio...",
        "en": "🎤 Generating {count} audio files...",
    },
    "status_audio_progress": {
        "vi": "🎤 Audio: {current}/{total}",
        "en": "🎤 Audio: {current}/{total}",
    },
    "status_saving_notes": {
        "vi": "💾 Đang lưu ghi chú...",
        "en": "💾 Saving notes...",
    },
    "import_audio_failed": {
        "vi": "⚠️ Audio lỗi : {count} file\n",
        "en": "⚠️ Audio failed: {count} files\n",
    },
    "import_errors": {
        "vi": "\n⚠️ Lỗi: {count} thẻ\n",
        "en": "\n⚠️ Errors: {count} cards\n",
    },
    "import_error": {
        "vi": "Lỗi nhập thẻ: {error}",
        "en": "Import error: {error}",
    },
    "rollback_checkpoint": {
        "vi": "Bento Forge: hoàn tác lô thẻ vừa nhập",
        "en": "Bento Forge: roll back latest import batch",
    },
    "msg_no_api_key_title": {
        "vi": "⚠️ Chưa có API Key",
        "en": "⚠️ API Key Not Configured",
    },
    "err_ai_extract_title": {
        "vi": "❌ Lỗi AI Trích Xuất",
        "en": "❌ AI Extraction Error",
    },
    "err_ai_chat_title": {
        "vi": "❌ Lỗi AI Chat",
        "en": "❌ AI Chat Error",
    },
    "chat_default_message": {
        "vi": "Xin chào! Hãy phân tích hệ thống Anki của tôi và đưa ra gợi ý học tập.",
        "en": "Hello! Please analyze my Anki setup and suggest how I can study more effectively.",
    },
    "chat_truncated_warning": {
        "vi": "⚠️ Nội dung quá dài ({length:,} ký tự).\nChỉ gửi {limit:,} ký tự đầu để tránh vượt giới hạn ngữ cảnh.\n💡 Nên dùng 'AI Trích Xuất' cho file lớn để xử lý toàn bộ theo từng đoạn.",
        "en": "⚠️ The content is too long ({length:,} characters).\nOnly the first {limit:,} characters will be sent to stay within the context limit.\n💡 Use 'AI Extraction' for large files so the entire file can be processed in chunks.",
    },
    "chat_truncated_suffix": {
        "vi": "[⏳ ...(phần còn lại đã cắt do quá dài)]",
        "en": "[⏳ ...(the remaining content was truncated)]",
    },
    "file_attach_dialog_title": {
        "vi": "📎 Chọn file tài liệu tham khảo",
        "en": "📎 Select Reference Documents",
    },
    "file_attach_dialog_filter": {
        "vi": "Tài liệu (*.txt *.md *.csv *.docx *.doc *.pdf *.xlsx *.xls);;Tất cả file (*)",
        "en": "Documents (*.txt *.md *.csv *.docx *.doc *.pdf *.xlsx *.xls);;All files (*)",
    },
    "file_content_unreadable": {
        "vi": "không đọc được nội dung",
        "en": "could not read the content",
    },
    "tooltip_files_attached_partial": {
        "vi": "📎 Đã kẹp {count} file.\n⚠️ Không đọc được:\n{errors}",
        "en": "📎 Attached {count} files.\n⚠️ Could not read:\n{errors}",
    },
    "tooltip_files_attached": {
        "vi": "✅ Đã kẹp {count} file làm tài liệu tham khảo!",
        "en": "✅ Attached {count} reference files!",
    },
    "tooltip_files_cleared": {
        "vi": "🧹 Đã bỏ toàn bộ file đính kèm.",
        "en": "🧹 Removed all attached files.",
    },
    "status_attached_files": {
        "vi": "📎 {count} file · {chars:,} ký tự",
        "en": "📎 {count} files · {chars:,} characters",
    },

    # ── Prompt Editor ────────────────────────────────────
    "prompt_kind_vocab": {
        "vi": "Từ Vựng",
        "en": "Vocabulary",
    },
    "prompt_kind_grammar": {
        "vi": "Ngữ Pháp",
        "en": "Grammar",
    },
    "prompt_side_back": {
        "vi": "Chỉ mặt sau",
        "en": "Back only",
    },
    "prompt_side_both": {
        "vi": "Cả hai mặt",
        "en": "Both sides",
    },
    "prompt_side_front": {
        "vi": "Chỉ mặt trước",
        "en": "Front only",
    },
    "prompt_editor_help": {
        "vi": "Trong System Prompt, dùng <code>{{JSON_TEMPLATE}}</code> để chèn mẫu vào \"MẪU:\". Sửa xong → cache AI tự làm mới. Field mới trong Field Map sẽ được thêm vào Note Type khi Lưu.",
        "en": "Use <code>{{JSON_TEMPLATE}}</code> in the System Prompt to insert the template into \"TEMPLATE:\". The AI cache refreshes after edits. New Field Map fields are added to the Note Type when you save.",
    },
    "prompt_template_hint": {
        "vi": "(dùng <code>{placeholder}</code> để chèn mẫu)",
        "en": "(use <code>{placeholder}</code> to insert the template)",
    },
    "prompt_tab_title": {
        "vi": "Prompt {kind}",
        "en": "{kind} Prompt",
    },
    "prompt_modified_suffix": {
        "vi": " ✏️ (đã chỉnh)",
        "en": " ✏️ (modified)",
    },
    "prompt_schema_valid": {
        "vi": "<span style='color:#27ae60;font-weight:bold;'>✅ Schema hợp lệ — {count} trường:</span> <code>{fields}</code>{modified}",
        "en": "<span style='color:#27ae60;font-weight:bold;'>✅ Valid schema — {count} fields:</span> <code>{fields}</code>{modified}",
    },
    "prompt_field_map_invalid": {
        "vi": "<span style='color:#e74c3c;font-weight:bold;'>❌ Mẫu JSON chưa hợp lệ — sửa ở tab {tab} trước. {error}</span>",
        "en": "<span style='color:#e74c3c;font-weight:bold;'>❌ The JSON template is invalid — fix it in the {tab} tab first. {error}</span>",
    },
    "prompt_new_keys_note": {
        "vi": "<br><span style='color:#8e44ad;'>🆕 Key mới: {keys} — tự suy tên field, bạn có thể đổi.</span>",
        "en": "<br><span style='color:#8e44ad;'>🆕 New keys: {keys} — field names are inferred and can be changed.</span>",
    },
    "prompt_none": {
        "vi": "không có",
        "en": "none",
    },
    "prompt_field_map_summary": {
        "vi": "<span style='color:#27ae60;font-weight:bold;'>✅ {count} key JSON → Field Anki.</span> Field chưa có trong Note Type sẽ được <b>thêm tự động khi Lưu</b>, và field mới sẽ <b>tự hiện trên thẻ</b> (theo cột Hiển thị).{note}",
        "en": "<span style='color:#27ae60;font-weight:bold;'>✅ {count} JSON keys → Anki Fields.</span> Missing Note Type fields are <b>added automatically on save</b>, and new fields <b>appear on cards automatically</b> (according to the Show column).{note}",
    },
    "prompt_json_error_title": {
        "vi": "Lỗi JSON",
        "en": "JSON Error",
    },
    "prompt_json_error_message": {
        "vi": "Mẫu JSON không hợp lệ:\n{error}",
        "en": "Invalid JSON template:\n{error}",
    },
    "prompt_preview_title": {
        "vi": "👁 Prompt Đầy Đủ — {language} ({kind})",
        "en": "👁 Full Prompt — {language} ({kind})",
    },
    "prompt_preview_metrics": {
        "vi": "<b>Độ dài:</b> {chars} ký tự — <b>{lines}</b> dòng mẫu",
        "en": "<b>Length:</b> {chars} characters — <b>{lines}</b> template lines",
    },
    "prompt_save_success": {
        "vi": "✅ Đã lưu Prompt, Schema & Field Map! Cache AI đã tự làm mới.",
        "en": "✅ Prompt, Schema, and Field Map saved! The AI cache was refreshed.",
    },
    "prompt_fields_added": {
        "vi": "➕ Đã thêm {count} field mới vào Note Type.",
        "en": "➕ Added {count} new fields to the Note Type.",
    },
    "prompt_templates_synced": {
        "vi": "🃏 Đã đồng bộ template {count} Note Type — field mới sẽ hiện trên thẻ.",
        "en": "🃏 Synced templates for {count} Note Types — new fields will appear on cards.",
    },
    "prompt_save_error_title": {
        "vi": "Lỗi lưu",
        "en": "Save Error",
    },
    "prompt_save_error_message": {
        "vi": "Không thể lưu cấu hình prompt:\n{error}",
        "en": "Could not save the prompt configuration:\n{error}",
    },
    "prompt_reset_title": {
        "vi": "Đặt lại Prompt",
        "en": "Reset Prompts",
    },
    "prompt_reset_confirm": {
        "vi": "Trả toàn bộ Prompt, Schema & Field Map về mặc định ban đầu?\n(Mọi chỉnh sửa của bạn sẽ bị xóa.)",
        "en": "Reset all Prompts, Schemas, and Field Maps to their defaults?\n(All your changes will be removed.)",
    },
    "prompt_reset_done": {
        "vi": "♻️ Đã đặt lại về mặc định.",
        "en": "♻️ Restored the defaults.",
    },
    "prompt_validation_empty": {
        "vi": "Template rỗng.",
        "en": "The template is empty.",
    },
    "prompt_validation_invalid_json": {
        "vi": "JSON không hợp lệ: {error}",
        "en": "Invalid JSON: {error}",
    },
    "prompt_validation_not_object": {
        "vi": "Template phải là một object JSON duy nhất (không phải mảng).",
        "en": "The template must be a single JSON object (not an array).",
    },

    # ── Theme dialog & AI providers ──────────────────────
    "theme_preset_glass_dark": {"vi": "🌑 Kính Tối", "en": "🌑 Glass Dark"},
    "theme_preset_glass_light": {"vi": "🌕 Kính Sáng", "en": "🌕 Glass Light"},
    "theme_preset_midnight": {"vi": "🌌 Nửa Đêm", "en": "🌌 Midnight"},
    "theme_accent_blue": {"vi": "🔵 Xanh dương", "en": "🔵 Blue"},
    "theme_accent_purple": {"vi": "🟣 Tím", "en": "🟣 Purple"},
    "theme_accent_green": {"vi": "🟢 Xanh lá", "en": "🟢 Green"},
    "theme_accent_orange": {"vi": "🟠 Cam", "en": "🟠 Orange"},
    "theme_accent_pink": {"vi": "🌸 Hồng", "en": "🌸 Pink"},
    "theme_accent_red": {"vi": "🔴 Đỏ", "en": "🔴 Red"},
    "theme_accent_cyan": {"vi": "🩵 Cyan", "en": "🩵 Cyan"},
    "theme_accent_custom": {"vi": "🌈 Tùy chỉnh...", "en": "🌈 Custom..."},
    "theme_topic_a": {"vi": "Chủ đề A", "en": "Topic A"},
    "theme_topic_b": {"vi": "Chủ đề B", "en": "Topic B"},
    "history_kind_tip": {
        "vi": "Lọc riêng Từ vựng hoặc Ngữ pháp",
        "en": "Filter Vocabulary or Grammar items",
    },
    "deck_create_failed": {
        "vi": "Không thể tạo deck. Hãy kiểm tra tên deck và thử lại.",
        "en": "Could not create the deck. Check the deck name and try again.",
    },
    "deck_rename_failed": {
        "vi": "Không thể đổi tên deck. Hãy kiểm tra tên mới và thử lại.",
        "en": "Could not rename the deck. Check the new name and try again.",
    },
    "deck_delete_failed": {
        "vi": "Không thể xóa deck. Hãy thử lại sau.",
        "en": "Could not delete the deck. Please try again.",
    },
    "ai_provider_deepseek_note": {
        "vi": "DeepSeek V4 Flash = nhanh/tiết kiệm; V4 Pro = chất lượng cao hơn. Alias cũ vẫn có để tương thích cấu hình đã lưu.",
        "en": "DeepSeek V4 Flash is fast and economical; V4 Pro targets higher quality. Legacy aliases remain for saved configurations.",
    },
    "ai_provider_openai_note": {
        "vi": "Các model GPT và o-series chính thức của OpenAI.",
        "en": "Official OpenAI GPT and o-series models.",
    },
    "ai_provider_gemini_note": {
        "vi": "Gemini API dùng endpoint OpenAI-compatible chính thức của Google. Lấy API key tại https://aistudio.google.com/apikey (bắt đầu bằng AIza...).",
        "en": "Gemini API uses Google's official OpenAI-compatible endpoint. Get an API key at https://aistudio.google.com/apikey (it starts with AIza...).",
    },
    "ai_provider_anthropic_note": {
        "vi": "Bento Forge gọi API kiểu OpenAI-compatible; với Anthropic, hãy dùng proxy tương thích (ví dụ LiteLLM / 1Backend) hoặc đặt API Base URL thành proxy của bạn.",
        "en": "Bento Forge uses an OpenAI-compatible API. For Anthropic, use a compatible proxy (such as LiteLLM / 1Backend) or set the API Base URL to your proxy.",
    },
    "ai_provider_openrouter_note": {
        "vi": "Một key dùng được model từ nhiều hãng. `~openai/gpt-latest` tự theo flagship OpenAI mới nhất; model khác dùng vendor/model-name.",
        "en": "One key provides models from many vendors. `~openai/gpt-latest` tracks the newest OpenAI flagship; other models use vendor/model-name.",
    },
    "ai_provider_ollama_note": {
        "vi": "Chạy hoàn toàn trên máy — không cần API Key. Cài model bằng `ollama pull qwen3.5`.",
        "en": "Runs entirely on your computer — no API Key required. Install a model with `ollama pull qwen3.5`.",
    },
    "ai_provider_lmstudio_note": {
        "vi": "Mở LM Studio → Start Server. Bạn có thể đổi tên model trong ô Model thành model đã tải.",
        "en": "Open LM Studio → Start Server. You can replace the Model value with the model you downloaded.",
    },
    "ai_provider_local_key_hint": {
        "vi": "(không cần — chạy trên máy)",
        "en": "(not required — runs locally)",
    },
    "ai_test_missing_base": {
        "vi": "⚠️ Vui lòng nhập API Base URL.",
        "en": "⚠️ Enter an API Base URL.",
    },
    "ai_test_http_error": {
        "vi": "❌ Lỗi HTTP {code}: {reason}\n\n{details}",
        "en": "❌ HTTP error {code}: {reason}\n\n{details}",
    },
    "ai_test_error": {
        "vi": "❌ Lỗi: {error}",
        "en": "❌ Error: {error}",
    },

    # ── Network, AI extraction & batch progress ──────────
    "error_cancelled_by_user": {
        "vi": "⏹ Đã hủy bởi người dùng",
        "en": "⏹ Cancelled by the user",
    },
    "error_ai_total_timeout": {
        "vi": "⏱ Đã hết tổng thời gian chờ cho yêu cầu AI",
        "en": "⏱ The AI request exceeded its total timeout",
    },
    "status_rate_limit_wait": {
        "vi": "⏳ Đang chờ {seconds:.1f}s để tránh giới hạn tốc độ...",
        "en": "⏳ Waiting {seconds:.1f}s to avoid the rate limit...",
    },
    "status_rate_limited": {
        "vi": "⚠️ Giới hạn tốc độ (429) — chờ {seconds:.0f}s rồi thử lại...\n💡 Gói OpenRouter miễn phí giới hạn khoảng 20 yêu cầu/phút. Hệ thống đang tự giảm tốc.",
        "en": "⚠️ Rate limited (429) — waiting {seconds:.0f}s before retrying...\n💡 OpenRouter's free tier allows about 20 requests/minute. The request rate is being reduced automatically.",
    },
    "status_receiving_data": {
        "vi": "⏳ Đang nhận dữ liệu... {percent}%",
        "en": "⏳ Receiving data... {percent}%",
    },
    "status_retrying": {
        "vi": "🔄 Thử lại {attempt}/{maximum} sau {seconds:.0f}s...",
        "en": "🔄 Retry {attempt}/{maximum} in {seconds:.0f}s...",
    },
    "error_connection_retries": {
        "vi": "❌ Lỗi kết nối sau {attempts} lần thử: {error}",
        "en": "❌ Connection failed after {attempts} attempts: {error}",
    },
    "error_connection": {
        "vi": "❌ Không thể kết nối: {error}",
        "en": "❌ Could not connect: {error}",
    },
    "error_ai_json_parse": {
        "vi": "⚠️ Không phân tích được JSON — thường do kết quả bị cắt vì vượt giới hạn token đầu ra.\n💡 Vào Cài Đặt AI → giảm 'Độ dài xử lý mỗi lần gọi' xuống 8k–12k rồi thử lại. Văn bản dài vẫn được xử lý hết theo từng đoạn.\nNội dung nhận được:\n{content}",
        "en": "⚠️ Could not parse the JSON — this usually means the response was truncated by the output-token limit.\n💡 Open AI Settings → reduce 'Chunk size per request' to 8k–12k, then try again. Long text will still be processed completely in chunks.\nReceived content:\n{content}",
    },
    "warning_output_truncated": {
        "vi": "⚠️ Kết quả bị cắt do giới hạn token đầu ra (max_tokens).\n💡 Giảm 'Độ dài xử lý mỗi lần gọi' trong Cài Đặt AI (ví dụ 6k–10k) hoặc chia nhỏ văn bản.",
        "en": "⚠️ The result was truncated by the output-token limit (max_tokens).\n💡 Reduce 'Chunk size per request' in AI Settings (for example, 6k–10k) or split the text.",
    },
    "status_ai_invalid_ignored": {
        "vi": "⚠️ Giữ {valid} thẻ hợp lệ; bỏ {invalid} mục sai schema hoặc thiếu dữ liệu tối thiểu.",
        "en": "⚠️ Kept {valid} valid cards; ignored {invalid} items with a schema or minimum-data error.",
    },
    "status_ai_recovery_split": {
        "vi": "🔄 Output lỗi ({reason}); tự chia nguồn thành {first} + {second} ký tự để thử lại.",
        "en": "🔄 Output failed ({reason}); retrying the source as {first} + {second} characters.",
    },
    "status_ai_partial_spans": {
        "vi": "⚠️ Đã giữ {valid} thẻ hợp lệ; còn {unresolved} đoạn nguồn chưa hoàn thành sau retry.",
        "en": "⚠️ Kept {valid} valid cards; {unresolved} source spans remain unresolved after retry.",
    },
    "status_cache_vocab": {
        "vi": "📦 Cache: {count} từ vựng!",
        "en": "📦 Cache: {count} vocabulary items!",
    },
    "status_cache_grammar": {
        "vi": "📦 Cache: {count} cấu trúc ngữ pháp!",
        "en": "📦 Cache: {count} grammar patterns!",
    },
    "error_api_key_missing": {
        "vi": "⚠️ Chưa cấu hình API Key. Vào Cài Đặt AI để nhập key.",
        "en": "⚠️ No API Key configured. Open AI Settings to enter a key.",
    },
    "status_text_truncated": {
        "vi": "📝 Văn bản {length} ký tự → cắt còn {limit}",
        "en": "📝 Text has {length} characters → truncated to {limit}",
    },
    "status_calling_model": {
        "vi": "🤖 Đang gọi {model}...",
        "en": "🤖 Calling {model}...",
    },
    "status_waiting_ai": {
        "vi": "⏳ Đang chờ AI phản hồi...",
        "en": "⏳ Waiting for the AI response...",
    },
    "error_api_no_result": {
        "vi": "❌ API không trả về kết quả.\n{details}",
        "en": "❌ The API returned no result.\n{details}",
    },
    "status_reasoning_fallback": {
        "vi": "⚠️ Đang dùng reasoning_content vì model không có content...",
        "en": "⚠️ Using reasoning_content because the model returned no content...",
    },
    "error_model_empty": {
        "vi": "❌ Model không trả về nội dung (content rỗng).",
        "en": "❌ The model returned no content.",
    },
    "error_model_final_empty": {
        "vi": "❌ Model chỉ trả về phần suy luận, không có câu trả lời cuối cùng để tạo thẻ. Hãy dùng model chat hoặc giảm số mục mỗi lượt.",
        "en": "❌ The model returned reasoning only, without a final answer to create cards. Use a chat model or reduce the items per request.",
    },
    "error_model_output_truncated": {
        "vi": "❌ Model đã chạm giới hạn token đầu ra; JSON chưa hoàn chỉnh. Hãy giảm số mục hoặc độ dài xử lý mỗi lượt rồi thử lại.",
        "en": "❌ The model hit its output-token limit, so the JSON is incomplete. Reduce the items or chunk size per request and try again.",
    },
    "status_parsing_json": {
        "vi": "🔍 Đang phân tích JSON...",
        "en": "🔍 Parsing JSON...",
    },
    "status_filtered_vocab": {
        "vi": "🔍 Đã lọc {count} từ trùng deck",
        "en": "🔍 Filtered {count} words already in the deck",
    },
    "status_filtered_grammar": {
        "vi": "🔍 Đã lọc {count} cấu trúc trùng deck",
        "en": "🔍 Filtered {count} grammar patterns already in the deck",
    },
    "status_new_vocab": {
        "vi": "✅ {count} từ vựng mới!",
        "en": "✅ {count} new vocabulary items!",
    },
    "status_new_grammar": {
        "vi": "✅ {count} cấu trúc ngữ pháp mới!",
        "en": "✅ {count} new grammar patterns!",
    },
    "status_reasoning_only": {
        "vi": "⚠️ Model chỉ trả về phần suy luận, không có kết quả cuối cùng.",
        "en": "⚠️ The model returned reasoning only, with no final answer.",
    },
    "chat_reasoning_only": {
        "vi": "[Phần suy luận của model]\n{reasoning}\n\n⚠️ Model không trả về kết quả cuối cùng.",
        "en": "[Model reasoning]\n{reasoning}\n\n⚠️ The model did not return a final answer.",
    },
    "status_complete": {
        "vi": "✅ Hoàn tất!",
        "en": "✅ Complete!",
    },
    "status_chunks_vocab": {
        "vi": "📦 {count} đoạn, đang xử lý...",
        "en": "📦 Processing {count} chunks...",
    },
    "status_chunks_grammar": {
        "vi": "📦 {count} đoạn, đang xử lý ngữ pháp...",
        "en": "📦 Processing {count} grammar chunks...",
    },
    "status_chunk": {
        "vi": "🔄 Đoạn {current}/{total}...",
        "en": "🔄 Chunk {current}/{total}...",
    },
    "status_chunk_error": {
        "vi": "⚠️ Lỗi đoạn {current}: {error}",
        "en": "⚠️ Chunk {current} failed: {error}",
    },
    "status_total_vocab": {
        "vi": "✅ Tổng: {count} từ mới",
        "en": "✅ Total: {count} new words",
    },
    "status_total_grammar": {
        "vi": "✅ Tổng: {count} cấu trúc ngữ pháp mới",
        "en": "✅ Total: {count} new grammar patterns",
    },
    "status_total_with_tokens": {
        "vi": "{summary} | 🔢 {tokens:,} tokens (vào {input_tokens:,} + ra {output_tokens:,}) | 💰 ${cost:.6f}",
        "en": "{summary} | 🔢 {tokens:,} tokens (in {input_tokens:,} + out {output_tokens:,}) | 💰 ${cost:.6f}",
    },
    "token_report": {
        "vi": "🔢 Token: {input_tokens:,} vào + {output_tokens:,} ra = {total_tokens:,} tổng | 💰 ${total_cost:.6f} (vào: ${input_cost:.6f} / ra: ${output_cost:.6f})",
        "en": "🔢 Tokens: {input_tokens:,} in + {output_tokens:,} out = {total_tokens:,} total | 💰 ${total_cost:.6f} (in: ${input_cost:.6f} / out: ${output_cost:.6f})",
    },
    "error_ai_input_limit": {
        "vi": "Nội dung đầu vào vượt giới hạn phiên AI đã cấu hình",
        "en": "AI input exceeds the configured session input limit",
    },
    "error_ai_budget_exceeded": {
        "vi": "Đã vượt ngân sách phiên AI: {reason}",
        "en": "AI session budget exceeded: {reason}",
    },
    "ai_budget_reason_estimate": {
        "vi": "ước tính token vượt giới hạn của phiên",
        "en": "estimated token use exceeds the session token limit",
    },
    "ai_budget_reason_tokens": {
        "vi": "ngân sách token còn lại của phiên không đủ",
        "en": "remaining session token budget is too small",
    },
    "ai_budget_reason_cost": {
        "vi": "ngân sách chi phí còn lại của phiên không đủ",
        "en": "remaining session cost budget is too small",
    },

    # ── Batch processing & deck organization ─────────────
    "batch_item_word": {"vi": "từ", "en": "word"},
    "batch_item_pattern": {"vi": "cấu trúc ngữ pháp", "en": "grammar pattern"},
    "batch_item_word_short": {"vi": "từ", "en": "word"},
    "batch_item_pattern_short": {"vi": "cấu trúc", "en": "pattern"},
    "batch_worker_estimate": {
        "vi": "📊 Ước tính: ~{batches} batch, ~${cost:.4f} USD, ~{seconds}s",
        "en": "📊 Estimate: ~{batches} batches, ~${cost:.4f} USD, ~{seconds}s",
    },
    "batch_worker_empty": {
        "vi": "⚠️ AI không trích xuất được {label} nào.",
        "en": "⚠️ The AI did not extract any {label}.",
    },
    "batch_worker_done": {
        "vi": "✅ Hoàn tất! Đã xử lý {count} {label}.",
        "en": "✅ Complete! Processed {count} {label}.",
    },
    "batch_status_parsing": {
        "vi": "🔍 Đang phân tích danh sách {label}...",
        "en": "🔍 Parsing the {label} list...",
    },
    "batch_error_no_items": {
        "vi": "⚠️ Không tìm thấy {label} nào trong danh sách. Hãy kiểm tra định dạng.",
        "en": "⚠️ No {label} found in the list. Check the format.",
    },
    "batch_status_parsed": {
        "vi": "📋 Đã phân tích {count} {label}",
        "en": "📋 Parsed {count} {label}",
    },
    "batch_status_filtered": {
        "vi": "🔍 Đã lọc {count} {label} trùng với deck hiện có",
        "en": "🔍 Filtered {count} {label} already in the deck",
    },
    "batch_error_all_existing": {
        "vi": "⚠️ Tất cả {label} đều đã có trong deck. Không còn mục mới để xử lý.",
        "en": "⚠️ Every {label} is already in the deck. There are no new items to process.",
    },
    "batch_status_remaining": {
        "vi": "📝 Còn {count} {label} mới cần xử lý",
        "en": "📝 {count} new {label} remain to process",
    },
    "batch_status_groups": {
        "vi": "📦 Chia thành {batches} batch (~{size} {label}/batch)",
        "en": "📦 Split into {batches} batches (~{size} {label}/batch)",
    },
    "batch_openrouter_safe": {
        "vi": "⚠️ Gói OpenRouter miễn phí giới hạn khoảng 20 yêu cầu/phút → tự đặt độ trễ {delay:.1f}s/batch (~{rate} yêu cầu/phút, an toàn).",
        "en": "⚠️ OpenRouter's free tier allows about 20 requests/minute → using a {delay:.1f}s batch delay (~{rate} requests/minute, safe).",
    },
    "batch_openrouter_fast": {
        "vi": "⚠️ Đã tắt chế độ chậm OpenRouter — giữ độ trễ {delay:.1f}s/batch. Có thể gặp giới hạn 429 (hệ thống sẽ tự thử lại và chờ).",
        "en": "⚠️ OpenRouter slow mode is off — keeping a {delay:.1f}s batch delay. A 429 rate limit may occur (the system will retry and wait automatically).",
    },
    "batch_status_cancelled": {
        "vi": "⏹️ Đã hủy sau {current}/{total} batch",
        "en": "⏹️ Cancelled after {current}/{total} batches",
    },
    "batch_status_cache_hit": {
        "vi": "  📦 Cache hit: {count} {label}",
        "en": "  📦 Cache hit: {count} {label}",
    },
    "batch_status_added": {
        "vi": "  ✅ +{count} {label} mới (tổng: {total})",
        "en": "  ✅ +{count} new {label} (total: {total})",
    },
    "batch_progress_error": {
        "vi": "  ❌ Lỗi batch {batch}: {error}",
        "en": "  ❌ Batch {batch} failed: {error}",
    },
    "batch_error_api": {
        "vi": "❌ Lỗi API: {error}",
        "en": "❌ API error: {error}",
    },
    "batch_error_too_many": {
        "vi": "❌ Quá nhiều lỗi ({count} batch lỗi). Đã dừng xử lý.",
        "en": "❌ Too many errors ({count} failed batches). Processing stopped.",
    },
    "batch_status_rate_wait": {
        "vi": "⏳ Đang chờ {seconds:.1f}s vì giới hạn tốc độ đang hoạt động...",
        "en": "⏳ Waiting {seconds:.1f}s while rate limiting is active...",
    },
    "batch_status_partial_retry": {
        "vi": "🔄 Đã giữ {valid} mục hợp lệ; thử lại riêng {missing} mục thiếu (vòng {attempt}/{maximum}).",
        "en": "🔄 Kept {valid} valid items; retrying only {missing} missing items (round {attempt}/{maximum}).",
    },
    "batch_status_partial_complete": {
        "vi": "⚠️ Đã tạo {valid}/{requested} thẻ hợp lệ. {unresolved} mục chưa hoàn thành sau {retries} lần retry; bạn vẫn có thể tiếp tục với phần hợp lệ.",
        "en": "⚠️ Created {valid}/{requested} valid cards. {unresolved} items remain unresolved after {retries} retries; you can continue with the valid cards.",
    },
    "batch_status_complete": {
        "vi": "🎉 Hoàn tất! Tổng: {count} {label} đã xử lý ({batches} batch, {errors} lỗi)",
        "en": "🎉 Complete! Processed {count} {label} in {batches} batches with {errors} errors",
    },
    "organizer_empty": {
        "vi": "Không có từ vựng",
        "en": "No vocabulary",
    },
    "organizer_status_analyzing": {
        "vi": "🧠 AI đang phân tích và tổ chức deck...",
        "en": "🧠 AI is analyzing and organizing the decks...",
    },
    "organizer_status_waiting": {
        "vi": "⏳ Đang chờ AI tổ chức deck...",
        "en": "⏳ Waiting for the AI to organize the decks...",
    },
    "organizer_status_suggested": {
        "vi": "✅ AI đề xuất: {parents} parent deck, {subs} sub deck",
        "en": "✅ AI suggested {parents} parent decks and {subs} sub decks",
    },
    "organizer_other": {"vi": "Khác", "en": "Other"},
    "organizer_uncategorized": {"vi": "Chưa phân loại", "en": "Uncategorized"},
    "organizer_lang_japanese": {"vi": "Tiếng Nhật", "en": "Japanese"},
    "organizer_lang_chinese": {"vi": "Tiếng Trung", "en": "Chinese"},
    "organizer_lang_korean": {"vi": "Tiếng Hàn", "en": "Korean"},
    "organizer_lang_english": {"vi": "Tiếng Anh", "en": "English"},
    "organizer_topic_parent": {"vi": "{language} Theo Chủ Đề", "en": "{language} by Topic"},
    "organizer_level_parent": {"vi": "{language} Theo Cấp Độ", "en": "{language} by Level"},
    "organizer_topic_description": {"vi": "Từ vựng về {topic}", "en": "Vocabulary about {topic}"},
    "organizer_level_description": {"vi": "Từ vựng {level}", "en": "{level} vocabulary"},
    "organizer_level_name": {"vi": "{level} - Từ vựng", "en": "{level} - Vocabulary"},
    "organizer_fallback_suggestion": {
        "vi": "Tổ chức tự động (dự phòng) — nhóm theo chủ đề và cấp độ",
        "en": "Automatic fallback organization — grouped by topic and level",
    },
    "organizer_anki_unavailable": {
        "vi": "⚠️ Không thể truy cập Anki. Hãy đảm bảo add-on đang chạy trong Anki.",
        "en": "⚠️ Could not access Anki. Make sure the add-on is running inside Anki.",
    },
    "organizer_default_parent": {"vi": "Từ Vựng Mới", "en": "New Vocabulary"},
    "organizer_status_create_parent": {
        "vi": "📁 Tạo parent deck: {name}",
        "en": "📁 Creating parent deck: {name}",
    },
    "organizer_status_created": {
        "vi": "✅ Đã tạo {count} deck",
        "en": "✅ Created {count} decks",
    },
    "ai_context_query_failed": {
        "vi": "Không thể truy vấn Anki: {error}",
        "en": "Could not query Anki: {error}",
    },
    "ai_context_language": {
        "vi": "🌐 Ngôn ngữ hiện tại: {language}",
        "en": "🌐 Current language: {language}",
    },
    "ai_context_deck_list": {
        "vi": "📦 Danh sách Deck ({count} deck):",
        "en": "📦 Deck list ({count} decks):",
    },
    "ai_context_card_count": {
        "vi": "{count} thẻ",
        "en": "{count} cards",
    },
    "ai_context_other_decks": {
        "vi": "... và {count} deck khác",
        "en": "... and {count} other decks",
    },
    "ai_context_current_deck": {
        "vi": "📊 Deck hiện tại ({name}):",
        "en": "📊 Current deck ({name}):",
    },
    "ai_context_total": {"vi": "Tổng", "en": "Total"},
    "ai_context_due": {"vi": "Đến hạn", "en": "Due"},
    "ai_context_new": {"vi": "Mới", "en": "New"},
    "history_ai_overview": {
        "vi": "📚 TỔNG QUAN LỊCH SỬ NHẬP THẺ (TÁCH THEO NGÔN NGỮ)",
        "en": "📚 IMPORT HISTORY OVERVIEW (GROUPED BY LANGUAGE)",
    },
    "history_ai_lang_japanese": {
        "vi": "🇯🇵 TIẾNG NHẬT",
        "en": "🇯🇵 JAPANESE",
    },
    "history_ai_lang_chinese": {
        "vi": "🇨🇳 TIẾNG TRUNG",
        "en": "🇨🇳 CHINESE",
    },
    "history_ai_lang_korean": {
        "vi": "🇰🇷 TIẾNG HÀN",
        "en": "🇰🇷 KOREAN",
    },
    "history_ai_lang_english": {
        "vi": "🇬🇧 TIẾNG ANH",
        "en": "🇬🇧 ENGLISH",
    },
    "history_ai_total": {
        "vi": "📊 Tổng: {count} mục đã nhập",
        "en": "📊 Total: {count} imported items",
    },
    "history_ai_levels": {"vi": "🎓 Cấp độ: {levels}", "en": "🎓 Levels: {levels}"},
    "history_ai_topics": {"vi": "🏷 Chủ đề: {topics}", "en": "🏷 Topics: {topics}"},
    "history_ai_recent": {
        "vi": "📝 {count} mục gần nhất:",
        "en": "📝 {count} most recent items:",
    },
    # ── V18.1 AI Study Sessions ─────────────────────────────────────────
    "study_title": {"vi": "🥟 Forge AI", "en": "🥟 Forge AI"},
    "study_subtitle": {"vi": "Hỏi khi cần — học tiếp khi đã rõ.", "en": "Ask when stuck — return when clear."},
    "study_reviewer_title": {"vi": "Study Coach", "en": "Study Coach"},
    "study_reviewer_subtitle": {
        "vi": "Học từ thẻ hiện tại · không tạo thẻ mới.",
        "en": "Learn from the current card · no card creation.",
    },
    "factory_source_panel_title": {
        "vi": "Nguồn học liệu",
        "en": "Learning source",
    },
    "factory_ai_panel_title": {
        "vi": "AI · Soạn yêu cầu",
        "en": "AI · Composer",
    },
    "factory_artifact_panel_title": {
        "vi": "JSON · Artifact đầu ra",
        "en": "JSON · Output artifact",
    },
    "study_forge_title": {"vi": "Trạm AI · Candidate & Artifact", "en": "AI Station · Candidates & Artifacts"},
    "study_forge_subtitle": {
        "vi": "Source dùng chung với Lò đúc · không có cửa sổ Xưởng riêng.",
        "en": "Uses the Forge source directly · no separate Workshop window.",
    },
    "study_sessions": {"vi": "Study Sessions", "en": "Study Sessions"},
    "study_ai_language_label": {"vi": "Ngôn ngữ AI", "en": "AI language"},
    "study_options_toggle": {
        "vi": "Hiện hoặc ẩn tùy chọn học, ngữ cảnh và model AI",
        "en": "Show or hide study options, context, and AI model",
    },
    "study_ai_language_choose": {"vi": "Chọn ngôn ngữ…", "en": "Choose a language…"},
    "study_ai_language_tip": {
        "vi": "Ngôn ngữ thuộc từng session. Đổi lựa chọn sẽ mở session cùng ngôn ngữ hoặc tạo session mới; không đổi lịch sử cũ.",
        "en": "Language belongs to each session. Changing it opens a same-language session or creates one; existing history is never relabeled.",
    },
    "study_new": {"vi": "Session mới", "en": "New session"},
    "study_rename": {"vi": "Đổi tên session", "en": "Rename session"},
    "study_rename_prompt": {"vi": "Tên session:", "en": "Session title:"},
    "study_delete": {"vi": "Xóa session", "en": "Delete session"},
    "study_delete_confirm": {"vi": "Xóa session '{title}', toàn bộ hội thoại và artifact của nó? Thẻ đã import trong Anki không bị xóa.", "en": "Delete '{title}' and its conversation/artifacts? Imported Anki notes are not deleted."},
    "study_default_title": {"vi": "Study Session", "en": "Study Session"},
    "study_conversation": {"vi": "Hội thoại học tập", "en": "Study conversation"},
    "study_quick_explain": {"vi": "Giải thích", "en": "Explain"},
    "study_quick_contrast": {"vi": "Phân biệt", "en": "Contrast"},
    "study_quick_usage": {"vi": "Cách dùng", "en": "Usage"},
    "study_quick_example": {"vi": "Ví dụ mới", "en": "New example"},
    "study_quick_check": {"vi": "Kiểm tra tôi", "en": "Quiz me"},
    "study_quick_hint": {"vi": "Gợi ý", "en": "Hint"},
    "study_quick_tip": {"vi": "Chỉ điền prompt; AI chưa được gọi cho đến khi bạn gửi.", "en": "Fills the prompt only; AI is not called until you send."},
    "study_coach_loop_idle": {"vi": "Vòng học · chưa có checkpoint cho chế độ này", "en": "Learning loop · no checkpoint for this mode"},
    "study_coach_loop_understood": {"vi": "Vòng học · đã rõ trong chế độ này", "en": "Learning loop · understood in this mode"},
    "study_coach_loop_needs_practice": {"vi": "Vòng học · cần luyện thêm trong chế độ này", "en": "Learning loop · more practice needed in this mode"},
    "study_coach_needs_practice": {"vi": "Cần luyện thêm", "en": "More practice"},
    "study_coach_understood": {"vi": "Đã rõ · tiếp tục ôn", "en": "Understood · keep reviewing"},
    "study_coach_checkpoint_understood": {"vi": "✓ Đã rõ · checkpoint cục bộ, Anki chưa đổi lịch ôn.", "en": "✓ Understood · local checkpoint; Anki scheduling was not changed."},
    "study_coach_checkpoint_needs_practice": {"vi": "↻ Cần luyện thêm · checkpoint cục bộ, chưa gọi AI.", "en": "↻ More practice needed · local checkpoint; AI was not called."},
    "study_coach_practice_prepared": {"vi": "Đã soạn micro-quiz; AI chưa được gọi cho đến khi bạn bấm Gửi.", "en": "Micro-quiz prepared; AI is not called until you press Send."},
    "study_coach_context_required": {"vi": "Cần mở Study Coach từ một thẻ Reviewer để lưu checkpoint.", "en": "Open Study Coach from a Reviewer card to save a checkpoint."},
    "study_coach_request_active": {"vi": "Hãy chờ request hiện tại kết thúc trước khi lưu checkpoint.", "en": "Wait for the current request to finish before saving a checkpoint."},
    "study_coach_returning": {"vi": "Đã lưu checkpoint cục bộ; tiếp tục chấm thẻ trong Reviewer.", "en": "Local checkpoint saved; continue grading the card in Reviewer."},
    "study_prompt_explain": {"vi": "Giải thích nội dung của thẻ hiện tại ngắn gọn, tập trung vào điểm dễ nhầm.", "en": "Explain the current card briefly, focusing on the most likely misconception."},
    "study_prompt_contrast": {"vi": "Phân biệt mục hiện tại với từ hoặc cấu trúc gần nghĩa quan trọng nhất nếu có bằng chứng rõ.", "en": "Contrast this item with the most important near-synonym or structure when there is clear evidence."},
    "study_prompt_usage": {"vi": "Giải thích pattern, collocation và register của mục này bằng một ví dụ ngắn.", "en": "Explain this item's pattern, collocation, and register with one short example."},
    "study_prompt_example": {"vi": "Cho 1–2 ví dụ mới cùng đúng nghĩa đang học, không đổi sense.", "en": "Give 1–2 new examples using the same sense being studied."},
    "study_prompt_check": {"vi": "Kiểm tra mình bằng một câu hỏi ngắn dựa trên thẻ hiện tại. Chỉ micro-quiz 1–3 lượt.", "en": "Check my understanding with one short question based on this card; keep it to a 1–3 turn micro-quiz."},
    "study_prompt_hint": {"vi": "Cho tối đa 1–2 gợi ý gián tiếp; không nói đáp án trực tiếp.", "en": "Give at most 1–2 indirect hints; do not reveal the answer."},
    # ── V18.3 Reviewer Study Library ───────────────────────────────────
    "study_library_manage": {"vi": "Thư viện học", "en": "Study Library"},
    "study_library_title": {"vi": "Thư viện học · {language}", "en": "Study Library · {language}"},
    "study_library_intro": {
        "vi": "Tài liệu được sao chép dạng text vào dữ liệu profile và dùng lại cho mọi Study Session cùng ngôn ngữ. Bỏ chọn pack sẽ ngừng đưa nó vào request ngay.",
        "en": "Extracted text is copied into profile data and reused by every same-language Study Session. Unchecking a pack immediately excludes it from requests.",
    },
    "study_library_enabled": {"vi": "Dùng", "en": "Use"},
    "study_library_pack": {"vi": "Study Pack", "en": "Study Pack"},
    "study_library_type": {"vi": "Loại", "en": "Type"},
    "study_library_size": {"vi": "Dung lượng", "en": "Size"},
    "study_library_chunks": {"vi": "Đoạn", "en": "Chunks"},
    "study_library_bytes": {"vi": "{count} byte", "en": "{count} bytes"},
    "study_library_add": {"vi": "Gắn tài liệu…", "en": "Attach document…"},
    "study_library_delete": {"vi": "Xóa pack", "en": "Delete pack"},
    "study_library_delete_confirm": {
        "vi": "Xóa Study Pack đã chọn khỏi dữ liệu profile? Session và thẻ Anki không bị thay đổi.",
        "en": "Delete the selected Study Pack from profile data? Sessions and Anki cards are unchanged.",
    },
    "study_library_clear": {"vi": "Xóa thư viện ngôn ngữ", "en": "Clear language library"},
    "study_library_clear_confirm": {
        "vi": "Xóa toàn bộ Study Pack của ngôn ngữ này? Thao tác không xóa session hoặc thẻ Anki.",
        "en": "Delete every Study Pack for this language? Sessions and Anki cards are not deleted.",
    },
    "study_library_close": {"vi": "Đóng", "en": "Close"},
    "study_library_pack_name": {"vi": "Tên Study Pack", "en": "Study Pack name"},
    "study_library_pack_name_prompt": {"vi": "Tên hiển thị:", "en": "Display name:"},
    "study_library_file_filter": {
        "vi": "Tài liệu hỗ trợ (*.txt *.md *.markdown *.csv *.pdf *.docx *.xlsx *.xls);;Tất cả file (*)",
        "en": "Supported documents (*.txt *.md *.markdown *.csv *.pdf *.docx *.xlsx *.xls);;All files (*)",
    },
    "study_library_error": {"vi": "Không thể gắn tài liệu: {error}", "en": "Could not attach document: {error}"},
    "study_library_added": {"vi": "Đã thêm Study Pack; chưa gọi AI.", "en": "Study Pack added; AI was not called."},
    "study_library_follow_links": {"vi": "Ưu tiên học đầy đủ · theo mục liên quan", "en": "Prefer full coverage · follow related sections"},
    "study_library_follow_links_tip": {
        "vi": "Theo request kế tiếp, có thể thêm tối đa 2 đoạn được liên kết nội bộ; không mở URL/web.",
        "en": "For the next request, may add up to two internally linked chunks; never opens URLs/the web.",
    },
    "study_library_not_used": {"vi": "Không dùng Study Library", "en": "Not using Study Library"},
    "study_library_scope_line": {
        "vi": "Đang dùng: {pack} › {heading} › {count} đoạn",
        "en": "Using: {pack} › {heading} › {count} chunks",
    },
    "study_library_scope_no_enabled_packs": {"vi": "Không dùng Study Library · chưa có pack đang bật", "en": "Not using Study Library · no enabled packs"},
    "study_library_scope_no_match": {"vi": "Không dùng Study Library · không tìm thấy nguồn phù hợp", "en": "Not using Study Library · no relevant source found"},
    "study_library_scope_ambiguous": {"vi": "Study Library · nguồn còn mơ hồ, cần chọn mục", "en": "Study Library · ambiguous source; choose a section"},
    "study_library_scope_details": {"vi": "Chi tiết Scope Manifest", "en": "Scope Manifest details"},
    "study_library_scope_status": {"vi": "Trạng thái: {status}", "en": "Status: {status}"},
    "study_library_scope_confidence": {"vi": "Độ tin cậy retrieval: {value}", "en": "Retrieval confidence: {value}"},
    "study_library_scope_budget": {"vi": "Context nguồn: {count} ký tự", "en": "Source context: {count} characters"},
    "study_library_scope_source": {
        "vi": "{index}. {pack} › {heading} [{provenance}] — {reason}",
        "en": "{index}. {pack} › {heading} [{provenance}] — {reason}",
    },
    "study_library_scope_choose": {"vi": "Chọn mục nguồn cho request", "en": "Choose a source section"},
    "study_library_scope_ambiguous_help": {
        "vi": "Nhiều pack khớp gần ngang nhau. Chọn đúng một mục để tiếp tục; Study Coach sẽ không tự mở rộng âm thầm.",
        "en": "Multiple packs match nearly equally. Choose one section to continue; Study Coach will not expand silently.",
    },
    "study_library_heading": {"vi": "Mục", "en": "Section"},
    "study_library_reason": {"vi": "Lý do", "en": "Reason"},
    "study_library_cancel": {"vi": "Hủy", "en": "Cancel"},
    "study_library_use_section": {"vi": "Dùng mục này", "en": "Use this section"},
    "study_library_scope_waiting": {"vi": "Request chưa gửi; hãy chọn nguồn hoặc tắt pack gây mơ hồ.", "en": "Request not sent; choose a source or disable an ambiguous pack."},
    "study_library_card_drill": {"vi": "Bài tập ngắn", "en": "Quick drill"},
    "study_library_card_drill_prompt": {
        "vi": "Soạn 1–3 câu hỏi ngắn theo chế độ học của thẻ hiện tại. Nếu có Study Pack đang bật và nguồn phù hợp, dùng ví dụ có dẫn pack/mục. Chỉ soạn bài tập, không chấm điểm hoặc đổi lịch ôn.",
        "en": "Draft 1–3 short questions for the current card's study mode. If an enabled Study Pack has relevant evidence, use a pack/section-labeled example. Only draft the drill; do not grade or change scheduling.",
    },
    "study_library_card_drill_ready": {"vi": "Đã soạn yêu cầu Bài tập ngắn; AI chưa được gọi cho đến khi bấm Gửi.", "en": "Quick-drill request drafted; AI is not called until you press Send."},
    "study_forge_quick_analyze": {"vi": "Phân tích nguồn", "en": "Analyze source"},
    "study_forge_quick_vocab": {"vi": "Xây dựng từ vựng", "en": "Build vocabulary"},
    "study_forge_quick_grammar": {"vi": "Xây dựng ngữ pháp", "en": "Build grammar"},
    "study_forge_quick_contrast": {"vi": "Phân biệt ứng viên", "en": "Contrast candidates"},
    "study_forge_quick_examples": {"vi": "Cải thiện ví dụ", "en": "Improve examples"},
    "study_forge_quick_quality": {"vi": "Kiểm tra chất lượng", "en": "Quality check"},
    "study_forge_prompt_analyze": {"vi": "Phân tích source đã gắn, chọn học liệu giá trị cao và giải thích ngắn gọn tiêu chí chọn.", "en": "Analyze the attached source, identify high-value learning material, and briefly explain the selection criteria."},
    "study_forge_prompt_vocab": {"vi": "Tìm các ứng viên từ vựng giá trị trong source theo đúng nghĩa ngữ cảnh. Chưa tạo JSON nếu Card Mode chưa bật.", "en": "Find high-value vocabulary candidates in the source using the correct contextual sense. Do not create JSON unless Card Mode is enabled."},
    "study_forge_prompt_grammar": {"vi": "Tìm các pattern ngữ pháp hữu ích trong source, nêu constraint và ví dụ phù hợp. Chưa tạo JSON nếu Card Mode chưa bật.", "en": "Find useful grammar patterns in the source, including constraints and suitable examples. Do not create JSON unless Card Mode is enabled."},
    "study_forge_prompt_contrast": {"vi": "Phân biệt các ứng viên dễ nhầm trong source bằng constraint ngắn gọn và có căn cứ.", "en": "Contrast confusing candidates from the source using concise, evidence-based constraints."},
    "study_forge_prompt_examples": {"vi": "Cải thiện ví dụ nhưng giữ nguyên target identity, nghĩa ngữ cảnh và ngôn ngữ đích.", "en": "Improve the examples while preserving target identity, contextual sense, and target language."},
    "study_forge_prompt_quality": {"vi": "Kiểm tra material: nghĩa mơ hồ, ví dụ yếu, ứng viên lệch mục tiêu, thiếu constraint hoặc không đáng tạo artifact.", "en": "Quality-check the material for ambiguous senses, weak examples, off-target candidates, missing constraints, or items not worth turning into artifacts."},
    "study_use_card_context": {"vi": "Dùng thẻ hiện tại làm ngữ cảnh", "en": "Use current card as context"},
    "study_card_mode": {"vi": "Bước xử lý", "en": "Production step"},
    "study_create_card_vocab": {
        "vi": "Tạo thẻ · Từ vựng",
        "en": "Create card · Vocabulary",
    },
    "study_create_card_grammar": {
        "vi": "Tạo thẻ · Ngữ pháp",
        "en": "Create card · Grammar",
    },
    "study_create_card_tip": {
        "vi": "Bật để lần Gửi kế tiếp tạo artifact theo loại thẻ đã chọn phía trên. Tắt để trò chuyện bình thường.",
        "en": "Enable to create an artifact using the card type selected above on the next Send. Disable for normal chat.",
    },
    "study_mode_chat": {"vi": "Chat", "en": "Chat"},
    "study_mode_vocab": {"vi": "Card Mode · Từ vựng", "en": "Card Mode · Vocabulary"},
    "study_mode_grammar": {"vi": "Card Mode · Ngữ pháp", "en": "Card Mode · Grammar"},
    "study_forge_mode_candidates": {"vi": "1 · Tuyển candidate từ source", "en": "1 · Mine Source Candidates"},
    "study_forge_mode_vocab": {"vi": "2 · Tạo artifact từ vựng", "en": "2 · Build Vocab Artifact"},
    "study_forge_mode_grammar": {"vi": "2 · Tạo artifact ngữ pháp", "en": "2 · Build Grammar Artifact"},
    "study_forge_mode_artifact": {"vi": "2 · Tạo artifact theo router", "en": "2 · Build Routed Artifact"},
    "study_forge_router_label": {"vi": "Router loại thẻ", "en": "Card-type router"},
    "study_forge_router_auto": {"vi": "Router · Tự động", "en": "Router · Auto"},
    "study_forge_router_vocab": {"vi": "Router · Từ vựng", "en": "Router · Vocabulary"},
    "study_forge_router_grammar": {"vi": "Router · Ngữ pháp", "en": "Router · Grammar"},
    "study_forge_router_result": {"vi": "Tự động → {lane}", "en": "Auto → {lane}"},
    "study_artifacts": {"vi": "Mẻ thẻ của Forge", "en": "Forge card artifacts"},
    "study_review_artifact": {"vi": "Mở", "en": "Review"},
    "study_open_forge": {"vi": "Đưa sang kiểm định", "en": "Send to review"},
    "study_input_placeholder": {"vi": "Hỏi về thẻ, cách dùng, hoặc bật Tạo thẻ cho request kế tiếp…", "en": "Ask about the card or usage, or enable Card Mode for the next request…"},
    "study_input_accessible": {"vi": "Câu hỏi cho Forge AI", "en": "Question for Forge AI"},
    "study_reviewer_input_placeholder": {"vi": "Hỏi về thẻ hiện tại, xin gợi ý hoặc kiểm tra mức hiểu…", "en": "Ask about the current card, request a hint, or test your understanding…"},
    "study_reviewer_input_accessible": {"vi": "Câu hỏi cho Study Coach", "en": "Question for Study Coach"},
    "study_forge_input_placeholder": {"vi": "Nhập yêu cầu sản xuất; trạng thái source được hiển thị riêng ở trên…", "en": "Give a production instruction; source attachment is shown separately above…"},
    "study_forge_input_accessible": {"vi": "Yêu cầu sản xuất cho trạm AI", "en": "Production instruction for the AI station"},
    "study_forge_source_label": {"vi": "NGUỒN HỌC LIỆU", "en": "LEARNING SOURCE"},
    "study_forge_source_placeholder": {"vi": "Chưa có nguồn học liệu. Dán nội dung cần phân tích tại đây…", "en": "No learning source yet. Paste material to analyze here…"},
    "study_forge_route_strip": {"vi": "SOURCE  →  ROUTER  →  CANDIDATE  →  ARTIFACT  →  IMPORT", "en": "SOURCE  →  ROUTER  →  CANDIDATE  →  ARTIFACT  →  IMPORT"},
    "study_candidates_default_instruction": {"vi": "Tuyển các candidate đáng học, bám chính xác source và đúng lane hiện tại.", "en": "Select high-value candidates grounded exactly in the source and current lane."},
    "study_candidates_source_required": {"vi": "Cần gắn source trước khi tuyển candidate.", "en": "Attach a source before mining candidates."},
    "study_candidates_source_changed": {"vi": "Source đã đổi sau khi tuyển candidate. Hãy tuyển lại để giữ provenance trước khi tạo artifact.", "en": "The source changed after candidate selection. Mine candidates again to preserve provenance before building an artifact."},
    "study_candidates_language_only": {"vi": "Tuyển candidate hiện chỉ hỗ trợ workflow Ngôn ngữ.", "en": "Candidate mining currently supports the Language workflow only."},
    "study_candidates_invalid": {"vi": "Manifest candidate không hợp lệ ({error}); không có mục nào được chuyển tiếp.", "en": "The candidate manifest was invalid ({error}); no items were forwarded."},
    "study_candidates_ready": {"vi": "Đã kiểm định {count} candidate từ source; loại {rejected} mục lỗi/trùng; {existing} mục trùng bề mặt với deck hiện tại được giữ để bạn quyết định.", "en": "Validated {count} source candidates; rejected {rejected} invalid/duplicate items; kept {existing} current-deck surface matches for your decision."},
    "study_candidates_selected": {"vi": "Đã chọn {count} candidate; yêu cầu tạo artifact đã được soạn, chưa gọi AI.", "en": "Selected {count} candidates; the artifact request is prepared and AI has not been called."},
    "study_candidates_dialog_title": {"vi": "Duyệt candidate từ source", "en": "Review Source Candidates"},
    "study_candidates_dialog_summary": {"vi": "{count} candidate đã qua kiểm định nguồn. {existing} mục có bề mặt đã xuất hiện trong deck; đây chỉ là cảnh báo, không tự loại vì có thể khác nghĩa.", "en": "{count} candidates passed source validation. {existing} surfaces already occur in the deck; this is advisory because their senses may differ."},
    "study_candidates_header_select": {"vi": "Chọn", "en": "Use"},
    "study_candidates_header_target": {"vi": "Target", "en": "Target"},
    "study_candidates_header_meaning": {"vi": "Nghĩa ngữ cảnh", "en": "Contextual meaning"},
    "study_candidates_header_priority": {"vi": "Ưu tiên", "en": "Priority"},
    "study_candidates_header_source": {"vi": "Trích nguồn", "en": "Source excerpt"},
    "study_candidates_header_reason": {"vi": "Lý do", "en": "Reason"},
    "study_candidates_header_status": {"vi": "Deck", "en": "Deck"},
    "study_candidates_status_existing": {"vi": "Đã có bề mặt · cần kiểm tra nghĩa", "en": "Surface exists · check sense"},
    "study_candidates_status_new": {"vi": "Chưa thấy bề mặt", "en": "Surface not found"},
    "study_candidates_select_all": {"vi": "Chọn tất cả", "en": "Select all"},
    "study_candidates_select_none": {"vi": "Bỏ chọn", "en": "Select none"},
    "study_candidates_cancel": {"vi": "Đóng", "en": "Close"},
    "study_candidates_use_selected": {"vi": "Dùng mục đã chọn", "en": "Use selected"},
    "study_candidates_none_selected": {"vi": "Chưa chọn candidate nào; Forge không soạn yêu cầu tạo artifact.", "en": "No candidates selected; Forge did not prepare an artifact request."},
    "study_edit_latest": {"vi": "Sửa & gửi lại", "en": "Edit & resend"},
    "study_delete_latest": {"vi": "Xóa lượt mới nhất", "en": "Delete latest turn"},
    "study_send": {"vi": "Gửi", "en": "Send"},
    "study_ready": {"vi": "Sẵn sàng", "en": "Ready"},
    "study_thinking": {"vi": "Forge AI đang suy nghĩ…", "en": "Forge AI is thinking…"},
    "study_typing": {"vi": "AI đang soạn tin{dots}", "en": "AI is typing{dots}"},
    "study_stopped": {"vi": "Đã dừng; session vẫn dùng được.", "en": "Stopped; the session remains usable."},
    "study_error": {"vi": "Lỗi: {error}", "en": "Error: {error}"},
    "study_back_review": {"vi": "← Tiếp tục học", "en": "← Back to review"},
    "study_close_workspace": {"vi": "Thu gọn trạm AI", "en": "Collapse AI station"},
    "study_collapse": {"vi": "Thu gọn/mở rộng AI", "en": "Collapse/expand AI"},
    "study_empty": {"vi": "Bắt đầu một câu hỏi ngắn. Memory chỉ thuộc session này.", "en": "Start with a short question. Memory stays in this session only."},
    "study_you": {"vi": "Bạn", "en": "You"},
    "study_ai": {"vi": "Forge AI", "en": "Forge AI"},
    "study_reviewer_ai": {"vi": "Study Coach", "en": "Study Coach"},
    "study_forge_ai": {"vi": "Trạm AI", "en": "AI Station"},
    "study_context_reviewer": {"vi": "REVIEWER · {mode} · {side} · {card}", "en": "REVIEWER · {mode} · {side} · {card}"},
    "study_context_forge": {"vi": "FORGE · {language} · {lane} · {source} · {card}", "en": "FORGE · {language} · {lane} · {source} · {card}"},
    "study_context_question_side": {"vi": "Mặt câu hỏi", "en": "Question side"},
    "study_context_answer_side": {"vi": "Mặt đáp án", "en": "Answer side"},
    "study_context_card_attached": {"vi": "Đã gắn thẻ hiện tại", "en": "Current card attached"},
    "study_context_card_attached_target": {"vi": "Thẻ chính: {target}", "en": "Primary card: {target}"},
    "study_context_card_not_sent": {"vi": "Không gửi ngữ cảnh thẻ", "en": "No current-card context sent"},
    "study_context_no_current_card": {"vi": "Không có thẻ hiện tại", "en": "No current card"},
    "study_context_source_chars": {"vi": "Source {count} ký tự", "en": "Source {count} chars"},
    "study_context_source_none": {"vi": "Không có source", "en": "No source"},
    "study_context_lane_vocab": {"vi": "Từ vựng", "en": "Vocabulary"},
    "study_context_lane_grammar": {"vi": "Ngữ pháp", "en": "Grammar"},
    "study_context_lane_knowledge": {"vi": "Knowledge", "en": "Knowledge"},
    "study_artifact_ready": {"vi": "Đã tạo {count} thẻ đã kiểm định.", "en": "Created {count} validated cards."},
    "study_artifact_rejected": {"vi": "Payload thẻ không đạt reliability gate; không tạo artifact.", "en": "Card payload failed the reliability gate; no artifact was created."},
    "study_artifact_missing": {"vi": "Artifact không còn khả dụng", "en": "Artifact unavailable"},
    "study_artifact_stale_label": {"vi": "{label} · Không tương thích", "en": "{label} · Incompatible"},
    "study_artifact_stale_notice": {"vi": "Artifact này dùng schema cũ hoặc mới hơn bản hiện tại và chỉ có thể xem.", "en": "This artifact uses an older or newer schema and is read-only."},
    "study_artifact_stale_review": {"vi": "Snapshot gốc được giữ lại để tham khảo. Không thể đưa artifact này sang trạm kiểm định.", "en": "The original snapshot is preserved for reference and cannot be sent to the review station."},
    "study_artifact_stale_open_error": {"vi": "Artifact không tương thích với schema hiện tại nên không thể đưa sang trạm kiểm định. Snapshot vẫn được giữ trong session.", "en": "This artifact is incompatible with the current schema and cannot be sent to the review station. Its snapshot remains in the session."},
    "study_sent_forge": {"vi": "Đã đưa snapshot sang trạm kiểm định — không gọi AI lại.", "en": "Snapshot sent to the review station — no AI call was made."},
    "study_artifact_open_error": {"vi": "Không thể đưa artifact sang trạm kiểm định. Snapshot vẫn được giữ trong session.", "en": "Could not send the artifact to the review station. Its snapshot remains in the session."},
    "study_usage": {"vi": "{tokens} tokens · ${cost:.6f}", "en": "{tokens} tokens · ${cost:.6f}"},
    "study_model_fallback": {"vi": "Model đã lưu không còn trong provider; đã dùng fallback an toàn.", "en": "The saved model is no longer available; a safe fallback was selected."},
    "study_menu_action": {"vi": "🥟 AI Study Sessions", "en": "🥟 AI Study Sessions"},
    "study_reviewer_only": {
        "vi": "AI Study Sessions chỉ hoạt động trong Reviewer. Để sản xuất thẻ, mở Bento Forge và dùng dây chuyền Lò đúc AI.",
        "en": "AI Study Sessions is available only in Reviewer. To produce cards, open Bento Forge and use the AI Forge production line.",
    },
    "study_reviewer_action": {"vi": "Hỏi AI", "en": "Ask AI"},
    "production_drill_action": {"vi": "Tự đặt câu", "en": "Make a sentence"},
    "production_drill_title": {"vi": "Production Drill", "en": "Production Drill"},
    "production_drill_instruction": {
        "vi": "Tự viết một câu mới với",
        "en": "Write a new sentence with",
    },
    "production_drill_placeholder": {
        "vi": "Gõ câu của bạn trước khi xem gợi ý…",
        "en": "Type your sentence before revealing guidance…",
    },
    "production_drill_reveal": {"vi": "Xem gợi ý", "en": "Reveal guidance"},
    "production_drill_hide": {"vi": "Ẩn gợi ý", "en": "Hide guidance"},
    "production_drill_clear": {"vi": "Viết lại", "en": "Start over"},
    "production_drill_close": {"vi": "Đóng bài luyện", "en": "Close drill"},
    "production_drill_pattern": {"vi": "Mẫu dùng", "en": "Usage pattern"},
    "production_drill_collocation": {"vi": "Cụm đi kèm", "en": "Collocation"},
    "production_drill_example": {"vi": "Câu mẫu", "en": "Example"},
    # ── AI Deck Blueprint ──────────────────────────────────
    "deck_center_open_blueprint": {"vi": "🌳 AI đề xuất cây deck", "en": "🌳 AI Deck Blueprint"},
    "deck_center_open_blueprint_tip": {
        "vi": "Dùng lại nguồn hiện có từ Forge (nếu có), duyệt/chỉnh cây Parent/Sub rồi mới lưu vào Anki.",
        "en": "Reuse the current Forge source when available, review or edit its Parent/Sub tree, then save it to Anki.",
    },
    "blueprint_title": {"vi": "AI Deck Blueprint — Đề xuất cây deck", "en": "AI Deck Blueprint"},
    "blueprint_intro": {
        "vi": "Dán danh sách từ có H1–H6, kiểm tra outline, rồi để AI đề xuất cây Parent/Sub. Bạn có thể sửa trực tiếp trước khi lưu.",
        "en": "Paste an H1–H6 vocabulary list, verify its outline, then let AI propose an editable Parent/Sub deck tree.",
    },
    "blueprint_language": {"vi": "Ngôn ngữ", "en": "Language"},
    "blueprint_expand_source": {"vi": "Mở rộng nguồn", "en": "Expand source"},
    "blueprint_collapse_source": {"vi": "Thu gọn nguồn", "en": "Collapse source"},
    "blueprint_source_placeholder": {
        "vi": "# Du lịch\n## Sân bay\n搭乗券 | thẻ lên máy bay\n預け荷物 | hành lý ký gửi",
        "en": "# Travel\n## Airport\n搭乗券 | boarding pass\n預け荷物 | checked baggage",
    },
    "blueprint_outline_empty": {"vi": "Chưa nhận diện section H1–H6.", "en": "No H1–H6 sections detected yet."},
    "blueprint_outline_more": {"vi": "+ {count} section khác", "en": "+ {count} more sections"},
    "blueprint_outline_detected": {
        "vi": "Đã nhận diện {count} section: {outline}",
        "en": "Detected {count} sections: {outline}",
    },
    "blueprint_instruction": {"vi": "Yêu cầu", "en": "Constraints"},
    "blueprint_instruction_placeholder": {
        "vi": "Ví dụ: 20–30 từ mỗi sub-deck, ưu tiên N3, gộp section dưới 8 từ…",
        "en": "For example: 20–30 words per subdeck, prioritize N3, merge sections below 8 words…",
    },
    "blueprint_col_deck": {"vi": "Cây deck (sửa trực tiếp)", "en": "Deck tree (edit inline)"},
    "blueprint_col_words": {"vi": "Số từ", "en": "Words"},
    "blueprint_col_description": {"vi": "Mô tả", "en": "Description"},
    "blueprint_words_title": {"vi": "Từ trong nhánh", "en": "Words in branch"},
    "blueprint_words_empty": {"vi": "Chọn một sub-deck để xem từ.", "en": "Select a subdeck to inspect its words."},
    "blueprint_add_parent": {"vi": "+ Parent", "en": "+ Parent"},
    "blueprint_add_sub": {"vi": "+ Sub-deck", "en": "+ Subdeck"},
    "blueprint_remove_branch": {"vi": "Xóa nhánh nháp", "en": "Remove draft branch"},
    "blueprint_name_prompt": {"vi": "Tên deck", "en": "Deck name"},
    "blueprint_select_parent": {"vi": "Hãy chọn một parent deck trước.", "en": "Select a parent deck first."},
    "blueprint_generate": {"vi": "AI đề xuất cây deck", "en": "Generate blueprint"},
    "blueprint_save": {"vi": "Lưu cây deck", "en": "Save deck tree"},
    "blueprint_import": {"vi": "Tạo deck + nhập thẻ", "en": "Create decks + import cards"},
    "blueprint_import_tip": {
        "vi": "Kiểm tra trùng/xung đột, xem trước rồi chỉ nhập note mới; chưa tạo audio.",
        "en": "Review duplicates/conflicts, then import new notes only; audio is not generated yet.",
    },
    "blueprint_undo_import": {"vi": "Hoàn tác batch vừa nhập", "en": "Undo last import batch"},
    "blueprint_status_ready": {"vi": "Sẵn sàng — chưa có thay đổi nào trong collection.", "en": "Ready — the collection has not been changed."},
    "blueprint_source_reused": {
        "vi": "Đã lấy lại nguồn hiện có từ Forge: {chars} ký tự, {files} file. Hãy kiểm tra outline rồi mới chạy AI.",
        "en": "Reused the current Forge source: {chars} characters, {files} files. Check the outline before running AI.",
    },
    "blueprint_status_starting": {"vi": "Đang chuẩn bị nguồn…", "en": "Preparing source…"},
    "blueprint_status_reading_source": {"vi": "Đang đọc H1–H6 và dựng outline…", "en": "Reading H1–H6 and building the outline…"},
    "blueprint_status_enriching": {"vi": "Đang tra soát và làm giàu danh sách từ…", "en": "Reviewing and enriching vocabulary…"},
    "blueprint_status_organizing": {"vi": "Đang đề xuất cây deck theo source path…", "en": "Proposing a deck tree from source paths…"},
    "blueprint_status_generated": {
        "vi": "Đã tạo bản nháp {decks} deck cho {words} từ. Hãy duyệt/sửa trước khi lưu.",
        "en": "Drafted {decks} decks for {words} words. Review or edit before saving.",
    },
    "blueprint_status_stopped": {"vi": "Đã dừng; collection chưa thay đổi.", "en": "Stopped; the collection is unchanged."},
    "blueprint_status_saving": {"vi": "Đang lưu cây deck đã duyệt…", "en": "Saving the approved deck tree…"},
    "blueprint_status_scanning_duplicates": {
        "vi": "Đang kiểm tra trùng/xung đột trên toàn bộ note type…",
        "en": "Scanning the full note type for duplicates and conflicts…",
    },
    "blueprint_status_importing": {
        "vi": "Đang tạo deck và nhập các note mới đã duyệt…",
        "en": "Creating decks and importing approved new notes…",
    },
    "blueprint_status_imported": {
        "vi": "Đã nhập {added} note mới vào {decks} deck; {errors} lỗi, {late} mục được chặn khi kiểm tra lại. Có thể hoàn tác đúng batch này.",
        "en": "Imported {added} new notes into {decks} decks with {errors} errors; {late} items were blocked by the final recheck. This exact batch can be undone.",
    },
    "blueprint_status_undoing": {
        "vi": "Đang hoàn tác đúng các note của batch Blueprint vừa nhập…",
        "en": "Undoing only notes from the latest Blueprint batch…",
    },
    "blueprint_status_undone": {
        "vi": "Đã hoàn tác {count} note của batch Blueprint vừa nhập.",
        "en": "Undid {count} notes from the latest Blueprint batch.",
    },
    "blueprint_status_saved": {
        "vi": "Đã tạo {created} deck mới và dùng lại {reused} deck có sẵn.",
        "en": "Created {created} new decks and reused {reused} existing decks.",
    },
    "blueprint_status_error": {"vi": "Lỗi Blueprint: {error}", "en": "Blueprint error: {error}"},
    "blueprint_error_empty_source": {"vi": "Hãy dán nguồn từ vựng trước.", "en": "Paste a vocabulary source first."},
    "blueprint_error_no_vocab": {"vi": "Không tìm thấy từ vựng hợp lệ trong nguồn.", "en": "No valid vocabulary was found in the source."},
    "blueprint_error_empty_tree": {"vi": "Cây deck đang trống.", "en": "The deck tree is empty."},
    "blueprint_import_nothing": {
        "vi": "Chưa có cây deck kèm dữ liệu từ vựng để nhập.",
        "en": "There is no deck tree with vocabulary data to import.",
    },
    "blueprint_import_language_changed": {
        "vi": "Ngôn ngữ đã đổi sau khi tạo cây. Hãy chạy AI đề xuất lại trước khi nhập.",
        "en": "The language changed after generation. Generate the blueprint again before importing.",
    },
    "blueprint_import_no_valid_cards": {
        "vi": "Không có thẻ hợp lệ để nhập ({invalid} mục không đạt schema).",
        "en": "No valid cards can be imported ({invalid} items failed schema validation).",
    },
    "blueprint_unsectioned": {"vi": "Chưa phân section", "en": "Unsectioned"},
    "blueprint_default_parent": {"vi": "Từ vựng AI", "en": "AI Vocabulary"},
    "blueprint_unassigned": {"vi": "Cần duyệt", "en": "Needs review"},
    "blueprint_general": {"vi": "Tổng hợp", "en": "General"},
    "blueprint_save_confirm_title": {"vi": "Xác nhận lưu cây deck", "en": "Confirm deck tree"},
    "blueprint_save_confirm": {
        "vi": "Lưu {total} deck đã duyệt? Forge sẽ tạo {new} deck mới và dùng lại {reused} deck trùng tên. Không deck/note/SRS hiện hữu nào bị đổi tên hoặc xóa.",
        "en": "Save {total} approved decks? Forge will create {new} new decks and reuse {reused} matching decks. No existing deck, note, or SRS data will be renamed or deleted.",
    },
    "blueprint_saved_tooltip": {"vi": "Đã lưu {count} deck trong Blueprint.", "en": "Saved {count} Blueprint decks."},
    "blueprint_import_confirm_title": {
        "vi": "Duyệt batch Blueprint", "en": "Review Blueprint batch"
    },
    "blueprint_import_confirm": {
        "vi": "Nhập {new} note mới vào {decks} sub-deck? Forge sẽ bỏ qua {duplicates} mục trùng, {conflicts} xung đột, {invalid} mục sai schema và {unassigned} mục chưa gán. Không cập nhật note cũ và chưa tạo audio. Bạn có thể hoàn tác đúng các note vừa thêm.",
        "en": "Import {new} new notes into {decks} subdecks? Forge will skip {duplicates} duplicates, {conflicts} conflicts, {invalid} schema-invalid items, and {unassigned} unassigned items. Existing notes are not updated and audio is not generated. The added notes can be undone as one batch.",
    },
    "blueprint_import_no_new": {
        "vi": "Không có note mới an toàn để nhập. Đã bỏ qua {duplicates} mục trùng, {conflicts} xung đột, {invalid} mục sai schema và {unassigned} mục chưa gán.",
        "en": "There are no safe new notes to import. Skipped {duplicates} duplicates, {conflicts} conflicts, {invalid} schema-invalid items, and {unassigned} unassigned items.",
    },
    "blueprint_imported_tooltip": {
        "vi": "Đã nhập {count} note mới từ Blueprint.",
        "en": "Imported {count} new Blueprint notes.",
    },
    "blueprint_undo_confirm_title": {
        "vi": "Hoàn tác batch Blueprint", "en": "Undo Blueprint batch"
    },
    "blueprint_undo_confirm": {
        "vi": "Xóa đúng {count} note vừa được batch Blueprint gần nhất thêm vào? Deck đã tạo sẽ được giữ lại.",
        "en": "Remove exactly {count} notes added by the latest Blueprint batch? Created decks will be kept.",
    },
    "btn_mode_collocation": {"vi": "🧩 Cụm từ / Thành ngữ", "en": "🧩 Collocations / Idioms"},
    "tooltip_switched_collocation": {"vi": "🧩 Đã chuyển sang Cụm từ / Thành ngữ", "en": "🧩 Switched to Collocations / Idioms"},
    "ai_input_placeholder_collocation": {
        "vi": "Dán ngữ liệu để AI chọn collocation, lexical chunk, phrasal verb và thành ngữ đáng học…",
        "en": "Paste source material so AI can select worthwhile collocations, lexical chunks, phrasal verbs, and idioms…",
    },
    "item_label_collocation": {"vi": "Cụm từ / Thành ngữ", "en": "Collocations / Idioms"},
    "item_label_collocation_lower": {"vi": "cụm từ / thành ngữ", "en": "collocations / idioms"},
    "item_label_collocation_short": {"vi": "Cụm", "en": "Chunks"},
    "worker_progress_collocation": {"vi": "🧩 Đang trích xuất cụm từ và thành ngữ…", "en": "🧩 Extracting chunks and idioms…"},
    "empty_collocation": {"vi": "Không tìm thấy cụm từ/thành ngữ đủ giá trị để tách thẻ.", "en": "No chunk or idiom met the standalone-card threshold."},
    "prompt_kind_collocation": {"vi": "Cụm từ / Thành ngữ", "en": "Collocations / Idioms"},
    "collocation_batch_not_available": {
        "vi": "Batch danh sách chưa dùng cho Collocation; hãy trích từ ngữ liệu để giữ đúng ngữ cảnh.",
        "en": "List batch is not used for Collocations yet; extract from source material to preserve context.",
    },
    "study_forge_router_collocation": {"vi": "Cụm từ / Thành ngữ", "en": "Collocations / Idioms"},
    "study_create_card_collocation": {"vi": "Tạo thẻ · Cụm từ", "en": "Create card · Collocation"},
    "study_context_lane_collocation": {"vi": "Cụm từ / Thành ngữ", "en": "Collocations / Idioms"},
    "status_poured_collocation": {"vi": "✅ Đã đưa {count} thẻ cụm từ vào xưởng", "en": "✅ Poured {count} chunk cards into the Factory"},
    "msg_chat_poured_collocation": {"vi": "Đã đưa {count} thẻ cụm từ/thành ngữ vào xưởng.", "en": "Sent {count} collocation/idiom cards to the Factory."},
}

# ═══════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════

def t(key: str, lang: str = None, **kwargs) -> str:
    """
    Lấy chuỗi dịch theo key.

    Args:
        key: Translation key
        lang: Ngôn ngữ (mặc định: ngôn ngữ hiện tại)
        **kwargs: Tham số format (VD: count=5)

    Returns:
        Chuỗi đã dịch (fallback về key nếu không tìm thấy)

    Example:
        >>> t("filter_raw_count", count=10)
        '📊 Kho hàng: 10 mục'
    """
    if lang is None:
        lang = _current_lang

    entry = _TRANSLATIONS.get(key, {})
    text = entry.get(lang) or entry.get("vi") or key

    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass

    return text


def set_language(lang: str):
    """Đặt ngôn ngữ mặc định, lưu vào config và thông báo cho các UI listener (live refresh)."""
    global _current_lang
    if lang in SUPPORTED_LANGUAGES:
        _current_lang = lang
        _save_config()
        _notify_language_listeners()
    else:
        raise ValueError(f"Unsupported language: {lang}. Supported: {list(SUPPORTED_LANGUAGES.keys())}")


def get_language() -> str:
    """Lấy ngôn ngữ hiện tại."""
    return _current_lang


def toggle_language() -> str:
    """Chuyển đổi ngôn ngữ giao diện giữa vi ⇄ en (trả về ngôn ngữ mới)."""
    next_lang = "en" if _current_lang == "vi" else "vi"
    set_language(next_lang)
    return next_lang


def study_mode_labels(lang: str) -> dict:
    """Nhãn 5 chế độ học (qa/vn/wb/pron/lg) theo ngôn ngữ học + ngôn ngữ UI hiện tại.

    VD (lang=japanese): vi → "1. Nhật→Việt", en → "1. Japanese→English".
    """
    src = {
        "japanese": t("lang_src_ja"),
        "chinese": t("lang_src_zh"),
        "korean": t("lang_src_ko"),
        "english": t("lang_src_en"),
    }.get(lang, t("lang_src_ja"))
    tgt = t("lang_tgt")
    pron = {
        "japanese": t("mode_label_pron_ja"),
        "chinese": t("mode_label_pron_zh"),
        "korean": t("mode_label_pron_ko"),
        "english": t("mode_label_pron_en"),
    }.get(lang, t("mode_label_pron_ja"))
    return {
        "qa": f"1. {src}→{tgt}",
        "vn": f"2. {tgt}→{src}",
        "wb": f"3. {t('mode_label_wb')}",
        "pron": f"4. {pron}",
        "lg": f"5. {t('mode_label_lg')}",
    }


# ═══════════════════════════════════════════════════════════
#  LANGUAGE CHANGE LISTENERS (live refresh UI)
# ═══════════════════════════════════════════════════════════

_language_listeners = []


def add_language_listener(callback):
    """Đăng ký callback được gọi mỗi khi ngôn ngữ thay đổi (để UI refresh mượt mà)."""
    if callback not in _language_listeners:
        _language_listeners.append(callback)


def remove_language_listener(callback):
    """Hủy đăng ký callback."""
    try:
        _language_listeners.remove(callback)
    except ValueError:
        pass


def _notify_language_listeners():
    """Gọi tất cả listener đã đăng ký (mỗi listener một lần, không chặn luồng chính)."""
    for cb in list(_language_listeners):
        try:
            cb()
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
#  PERSISTENCE
# ═══════════════════════════════════════════════════════════

def _save_config():
    """Lưu ngôn ngữ hiện tại vào file config."""
    try:
        atomic_write_json(_CONFIG_PATH, {"language": _current_lang})
    except Exception:
        pass


def _load_config():
    """Tải ngôn ngữ từ file config nếu có."""
    global _current_lang
    try:
        # ``i18n_config.json`` shipped with older releases contains the default
        # Vietnamese value.  It is source data, not a user setting; only migrate
        # a non-default legacy choice so tests and updates never delete it.
        legacy = read_json(
            _LEGACY_CONFIG_PATH,
            {},
            lambda data: isinstance(data, dict) and data.get("language") in SUPPORTED_LANGUAGES,
        )
        if legacy.get("language") not in (None, "vi"):
            migrate_legacy_json(
                _LEGACY_CONFIG_PATH,
                _CONFIG_PATH,
                lambda data: isinstance(data, dict) and data.get("language") in SUPPORTED_LANGUAGES,
            )
        data = read_json(_CONFIG_PATH, {}, lambda value: isinstance(value, dict))
        lang = data.get("language", "vi")
        if lang in SUPPORTED_LANGUAGES:
            _current_lang = lang
    except Exception:
        pass


# Tự động load config khi import module
_load_config()
