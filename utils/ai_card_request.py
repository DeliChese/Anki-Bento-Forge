"""Pure prompt fragments for requests that generate cards without a source."""


def build_card_request_message(text, *, kind="vocab", ui_language_is_english=False,
                               generation_request=False):
    """Build direct-generation or source-extraction request text."""
    if not generation_request:
        if ui_language_is_english:
            request = (
                "Extract high-value collocations, chunks, and idioms from the following text:"
                if kind == "collocation" else "Extract all grammar patterns from the following text:"
                if kind == "grammar" else "Extract all vocabulary from the following text:"
            )
        else:
            request = (
                "Hãy trích xuất collocation, cụm từ và thành ngữ đáng học từ văn bản sau:"
                if kind == "collocation" else "Hãy trích xuất tất cả cấu trúc ngữ pháp từ văn bản sau:"
                if kind == "grammar" else "Hãy trích xuất tất cả từ vựng từ văn bản sau:"
            )
        return f"{request}\n\n{text}"

    labels = {
        "vocab": ("vocabulary", "từ vựng"),
        "collocation": ("collocation", "collocation"),
        "grammar": ("grammar", "ngữ pháp"),
    }
    english_kind, vietnamese_kind = labels.get(kind, labels["vocab"])
    if ui_language_is_english:
        request = (
            f"Create study-ready {english_kind} cards directly from this learner request; "
            "it is not source material."
        )
        heading = "LEARNER REQUEST"
    else:
        request = (
            f"Hãy tạo trực tiếp các thẻ {vietnamese_kind} sẵn sàng học theo yêu cầu người học; "
            "đây không phải tài liệu nguồn."
        )
        heading = "YÊU CẦU NGƯỜI HỌC"
    return f"{request}\n\n{heading}:\n{text}"
