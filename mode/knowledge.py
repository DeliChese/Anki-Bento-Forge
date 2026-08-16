"""Self-contained templates and CSS for the V18 Knowledge note type."""

KNOWLEDGE_MODEL_NAME = "Bento Forge Knowledge V18 (Add-on)"
KNOWLEDGE_FIELDS = (
    "Type", "Question", "Answer", "Explanation", "Source", "Cloze Text", "Duplicate Key",
)

KNOWLEDGE_MODEL_CONFIG = {
    "model_name": KNOWLEDGE_MODEL_NAME,
    # Knowledge is a new model.  Never rename a Language model into it.
    "old_model_names": (),
    "all_fields": list(KNOWLEDGE_FIELDS),
    "template_names": ("Basic Q&A", "Cloze"),
}


def knowledge_basic_question() -> str:
    return """{{#Question}}{{^Cloze Text}}
<main class="knowledge-card knowledge-basic">
  <div class="knowledge-label">QUESTION</div>
  <div class="knowledge-question">{{Question}}</div>
</main>
{{/Cloze Text}}{{/Question}}"""


def knowledge_basic_answer() -> str:
    return """{{#Question}}{{^Cloze Text}}
{{FrontSide}}
<hr id="answer">
<main class="knowledge-card knowledge-basic">
  <div class="knowledge-label">ANSWER</div>
  <div class="knowledge-answer">{{Answer}}</div>
  {{#Explanation}}<section class="knowledge-explanation">{{Explanation}}</section>{{/Explanation}}
  {{#Source}}<footer class="knowledge-source">Source: {{Source}}</footer>{{/Source}}
</main>
{{/Cloze Text}}{{/Question}}"""


def knowledge_cloze_question() -> str:
    return """{{#Cloze Text}}
<main class="knowledge-card knowledge-cloze">{{cloze:Cloze Text}}</main>
{{/Cloze Text}}"""


def knowledge_cloze_answer() -> str:
    return """{{#Cloze Text}}
{{FrontSide}}
<hr id="answer">
<main class="knowledge-card knowledge-cloze">
  <div class="knowledge-cloze-answer">{{cloze:Cloze Text}}</div>
  {{#Explanation}}<section class="knowledge-explanation">{{Explanation}}</section>{{/Explanation}}
  {{#Source}}<footer class="knowledge-source">Source: {{Source}}</footer>{{/Source}}
</main>
{{/Cloze Text}}"""


KNOWLEDGE_TEMPLATES = (
    knowledge_basic_question, knowledge_basic_answer,
    knowledge_cloze_question, knowledge_cloze_answer,
)


def knowledge_css() -> str:
    return """
.card { background: #f7f8fa; color: #1f2937; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 20px; text-align: left; }
.knowledge-card { max-width: 46rem; margin: 0 auto; padding: 1.25rem; line-height: 1.55; }
.knowledge-label { color: #64748b; font-size: .7rem; font-weight: 700; letter-spacing: .12em; margin-bottom: .55rem; }
.knowledge-question { font-size: 1.35em; font-weight: 650; }
.knowledge-answer, .knowledge-cloze-answer { color: #0f766e; font-size: 1.15em; font-weight: 600; }
.knowledge-cloze .cloze { color: #b45309; font-weight: 700; }
.knowledge-explanation { border-top: 1px solid #dbe1e8; color: #475569; font-size: .82em; margin-top: 1rem; padding-top: .8rem; }
.knowledge-source { color: #64748b; font-size: .7em; font-style: italic; margin-top: 1rem; }
""".strip()
