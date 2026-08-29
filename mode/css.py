"""
Card CSS — Japanese & Chinese with shared base.
"""

from .shared import _HW_CSS, _SHARED_UI_CSS


# ═══════════════════════════════════════════════════════════
#  BASE CSS — Shared between Japanese & Chinese
# ═══════════════════════════════════════════════════════════
_BASE_CSS = '''
.card.nightMode {
    --bg:#141418;--card-bg:#1e1e26;--border:#2e2e3a;--text:#e8e6f0;
    --muted:#888898;--accent:#e05c4b;--accent-soft:#2e1a18;
    --accent2:#4fa3d1;--accent2-soft:#162030;
    --ex-bg:#1a1a22;--ex-border:#333348;--shadow:0 10px 32px rgba(0,0,0,0.42);--ring:0 0 0 3px rgba(79,163,209,.23);
}
*{box-sizing:border-box;}
body{background:var(--bg);margin:0;padding:20px 16px;color:var(--text);}
.cw{background:var(--card-bg);border:1px solid var(--border);border-radius:var(--r);box-shadow:var(--shadow);width:calc(100% - 8px);max-width:680px;margin:20px auto;overflow:hidden;}
.ch{padding:9px 20px;display:flex;justify-content:space-between;align-items:center;gap:12px;}
.ch .badge{color:rgba(255,255,255,.92);font-size:11px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;flex:0 1 auto;}
.ch .topic{color:rgba(255,255,255,.76);font-size:12px;text-align:right;min-width:0;overflow-wrap:anywhere;word-break:break-word;}
.vb{text-align:center;padding:34px 28px 20px;}
.az{text-align:center;padding:0 24px 14px;}
.az input{border:2px solid var(--border);border-radius:10px;padding:10px 14px;font-size:17px;background:var(--bg);color:var(--text);outline:none;width:min(100%,430px);}
.az input:focus{border-color:var(--accent2);box-shadow:var(--ring);}
.typeGood,.typeBad{border-radius:8px;padding:2px 5px;}
.typeGood{background:#daf5e6;color:#17683f;}
.typeBad{background:#ffe3e1;color:#a52c26;}
.card.nightMode .typeGood{background:#0a2e18;color:#74eba9;}.card.nightMode .typeBad{background:#3b1214;color:#ff9892;}
.ir{display:flex;align-items:center;justify-content:center;gap:10px 18px;padding:14px 24px;border-top:1px solid var(--border);border-bottom:1px solid var(--border);background:var(--accent-soft);flex-wrap:wrap;}
.ir .mn{font-size:22px;font-weight:700;color:var(--accent);}
.ir .sv{font-size:14px;font-weight:700;color:var(--accent2);background:var(--accent2-soft);padding:3px 10px;border-radius:6px;}
.ir .au{font-size:18px;}
.es{padding:20px 24px 26px;}
.esl{font-size:11px;font-weight:800;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase;margin-bottom:10px;}
.ec{background:var(--ex-bg);border:1px solid var(--ex-border);border-radius:12px;padding:14px 16px;margin-bottom:10px;box-shadow:inset 3px 0 0 var(--accent2-soft);}
.ec:last-child{margin-bottom:0;}
.en{font-size:10px;font-weight:700;color:var(--muted);letter-spacing:1px;margin-bottom:4px;}
.ej,.ea,.ev,.trad,.fqm,.wb-meaning,.ga-sentence{overflow-wrap:anywhere;word-break:break-word;}
.ej{font-size:18px;font-weight:700;color:var(--text);line-height:1.65;margin-bottom:5px;}
.ea{font-size:15px;line-height:1.65;margin-bottom:5px;}
.ev{font-size:14px;color:var(--muted);font-style:italic;line-height:1.55;}
.fqw{background:var(--card-bg);border:1px solid var(--border);border-radius:var(--r);box-shadow:var(--shadow);width:calc(100% - 8px);max-width:680px;margin:20px auto;text-align:center;padding:52px 32px;}
.fql{font-size:11px;font-weight:700;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:12px;}
.fqm{font-size:38px;font-weight:900;color:var(--text);}
.blank{display:inline-block;min-width:50px;background:#ffe082;border-bottom:2.5px solid #f57c00;padding:0 8px;border-radius:4px;color:transparent;user-select:none;}
.fill-hint{font-size:14px;color:var(--accent);margin:6px 0 2px;padding:8px 14px;background:var(--accent-soft);border-radius:8px;text-align:center;line-height:1.6;}
.fill-word{background:var(--accent-soft);color:var(--accent);border-bottom:2.5px solid var(--accent);padding:0 3px;border-radius:3px;font-weight:700;}
.wb-wrap{padding:16px 20px 20px;}
.wb-meaning{font-size:32px;font-weight:900;color:var(--text);text-align:center;margin-bottom:6px;line-height:1.2;}
.wb-sub{font-size:14px;color:var(--accent2);text-align:center;margin-bottom:4px;}
.wb-label{font-size:11px;font-weight:700;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase;text-align:center;margin-bottom:12px;}
.wb-ans-area{display:flex;flex-wrap:wrap;gap:6px;min-height:56px;justify-content:center;align-items:center;border:2px dashed var(--border);border-radius:12px;padding:10px;margin-bottom:12px;background:var(--ex-bg);transition:border-color .2s;}
.wb-bank-area{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;min-height:52px;padding:8px;margin-bottom:10px;}
.wb-tile{min-width:42px;height:42px;padding:0 10px;border:2px solid var(--accent);border-radius:8px;display:inline-flex;align-items:center;justify-content:center;font-size:20px;font-weight:700;cursor:pointer;background:var(--card-bg);color:var(--text);user-select:none;transition:transform .1s,box-shadow .1s;}
.wb-tile:hover{transform:translateY(-2px);box-shadow:0 4px 12px rgba(0,0,0,.15);}
.wb-tile.wb-drag{opacity:.4;}
.wb-tile.wb-ok{border-color:#27ae60;background:#d5f5e3;color:#1a5c35;}
.wb-tile.wb-err{border-color:#e74c3c;background:#fdecea;color:#c0392b;}
.card.nightMode .wb-tile.wb-ok{background:#0a2e18;color:#4ae89a;}
.card.nightMode .wb-tile.wb-err{background:#2e0a0a;color:#ff6b6b;}
.wb-actions{display:flex;gap:10px;justify-content:center;margin:4px 0 8px;}
.wb-btn-clear,.wb-btn-check{padding:9px 22px;border-radius:10px;font-weight:700;font-size:14px;cursor:pointer;border:none;}
.wb-btn-clear{background:var(--border);color:var(--text);}
.wb-btn-check{background:var(--accent);color:#fff;}
.wb-result{text-align:center;font-size:16px;font-weight:700;display:none;padding:8px;border-radius:8px;margin-top:4px;}
.wb-result.wb-ok{color:#27ae60;background:#d5f5e3;}
.wb-result.wb-err{color:#c0392b;background:#fdecea;}
.card.nightMode .wb-result.wb-ok{background:#0a2e18;color:#4ae89a;}
.card.nightMode .wb-result.wb-err{background:#2e0a0a;color:#ff6b6b;}
.pron-wrap{text-align:center;padding:0 24px 16px;}
.pron-lbl{font-size:11px;font-weight:700;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;}
.srs-scope{margin:10px 16px 0;padding:8px 12px;border:1px solid var(--border);border-radius:9px;background:var(--accent-soft);color:var(--muted);font-size:12px;font-weight:700;line-height:1.45;text-align:center;}
.srs-scope.srs-independent{border-color:var(--accent2);color:var(--accent2);}
.card.nightMode .srs-scope{background:var(--ex-bg);}
.mode-bar{display:flex;flex-wrap:wrap;gap:7px;justify-content:center;padding:16px 18px 8px;}
.mode-btn{padding:7px 13px;border:1.5px solid var(--border);border-radius:16px;background:var(--card-bg);color:var(--muted);font-size:12px;font-weight:700;cursor:pointer;transition:all .18s;white-space:normal;}
.mode-btn:hover{border-color:var(--accent2);color:var(--accent2);}
.mode-btn:focus-visible,.combo-check input:focus-visible,.combo-check button:focus-visible,.wb-btn-clear:focus-visible,.wb-btn-check:focus-visible{outline:none;box-shadow:var(--ring);}
.mode-btn.active{background:var(--accent2);border-color:var(--accent2);color:#fff;box-shadow:0 3px 9px rgba(0,0,0,.12);}
.mode-panel{display:block;}
.combo-check{display:flex;gap:8px;justify-content:center;padding:0 24px 16px;max-width:560px;margin:0 auto;}
.combo-check input{flex:1;min-width:0;max-width:360px;border:2px solid var(--border);border-radius:10px;padding:10px 14px;font-size:16px;background:var(--bg);color:var(--text);outline:none;}
.combo-check input:focus{border-color:var(--accent2);box-shadow:var(--ring);}
.combo-check button{padding:10px 18px;border-radius:10px;border:none;background:var(--accent);color:#fff;font-weight:700;font-size:14px;cursor:pointer;white-space:nowrap;}
.combo-res{text-align:center;font-size:15px;font-weight:700;display:none;padding:8px;border-radius:8px;margin:0 24px 14px;}
.combo-res.combo-ok{color:#27ae60;background:#d5f5e3;}
.combo-res.combo-err{color:#c0392b;background:#fdecea;}
.card.nightMode .combo-res.combo-ok{background:#0a2e18;color:#4ae89a;}
.card.nightMode .combo-res.combo-err{background:#2e0a0a;color:#ff6b6b;}
@media (max-width:520px){
  body{padding:10px 6px;}
  .cw,.fqw{width:100%;margin:10px auto;border-radius:14px;}
  .ch{padding:8px 14px;align-items:flex-start;}
  .ch .topic{font-size:11px;}
  .vb{padding:28px 18px 16px;}
  .es{padding:18px 14px 20px;}
  .ec{padding:12px;}
  .mode-bar{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));padding:12px 14px 8px;}
  .mode-btn{width:100%;padding:8px 6px;font-size:11px;}
  .mode-btn:last-child{grid-column:1 / -1;width:50%;justify-self:center;}
  .combo-check{flex-direction:column;padding:0 16px 14px;}
  .combo-check input,.combo-check button{width:100%;max-width:none;}
  .ir{padding:12px 16px;}
}
@media (prefers-reduced-motion:reduce){.mode-btn,.wb-tile{transition:none;}}
''' + _HW_CSS


# ═══════════════════════════════════════════════════════════
#  JAPANESE CSS
# ═══════════════════════════════════════════════════════════

_JA_THEME = '''
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&family=Noto+Serif+JP:wght@700&display=swap');
:root {
    --bg:#f7f5f0;--card-bg:#ffffff;--border:#e8e2d9;--text:#1a1a2e;
    --muted:#7a7a8a;--accent:#c0392b;--accent-soft:#fdecea;
    --accent2:#2980b9;--accent2-soft:#eaf4fb;
    --ex-bg:#f9f7f4;--ex-border:#d4c5b0;--shadow:0 4px 20px rgba(0,0,0,0.07);--r:16px;
    --flag:"🇯🇵";
}
body{font-family:'Noto Sans JP','Meiryo',sans-serif;}
'''

_JA_SPECIFIC = '''
.furi{font-size:16px;color:var(--muted);letter-spacing:.05em;min-height:22px;margin-bottom:4px;}
.kanji{font-family:'Noto Serif JP',serif;font-size:64px;font-weight:700;color:var(--text);line-height:1.1;}
'''

_JA_EXTRA = '''
body{background:linear-gradient(150deg,#f7f5f0 0%,#fef0f4 100%);}
.ch{background:linear-gradient(135deg,#bc002d 0%,#8b0021 60%,#bc002d 100%);position:relative;}
.ch::before{content:'⛩';font-size:13px;opacity:.45;margin-right:6px;}
.cw{border-left:3px solid #bc002d;}
'''


def css_japanese():
    return _JA_THEME + _BASE_CSS + _JA_SPECIFIC + _JA_EXTRA + _SHARED_UI_CSS


# ═══════════════════════════════════════════════════════════
#  CHINESE CSS
# ═══════════════════════════════════════════════════════════

_ZH_THEME = '''
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&family=Noto+Serif+SC:wght@700&family=Noto+Sans+TC:wght@400;700;900&display=swap');
:root {
    --bg:#f7f7f5;--card-bg:#ffffff;--border:#e0ded8;--text:#1a1a2e;
    --muted:#7a7a8a;--accent:#c0392b;--accent-soft:#fdecea;
    --accent2:#2980b9;--accent2-soft:#eaf4fb;
    --ex-bg:#f9f8f5;--ex-border:#d4c5b0;--shadow:0 4px 20px rgba(0,0,0,0.07);--r:16px;
    --flag:"🇨🇳";
}
body{font-family:'Noto Sans SC','Noto Sans TC','Microsoft YaHei','PingFang SC',sans-serif;}
'''

_ZH_SPECIFIC = '''
.pinyin{font-size:16px;color:var(--muted);letter-spacing:.05em;min-height:22px;margin-bottom:4px;}
.hanzi{font-family:'Noto Serif SC','Noto Sans TC','KaiTi','STKaiti',serif;font-size:64px;font-weight:700;color:var(--text);line-height:1.1;}
.trad{font-size:14px;color:var(--muted);margin-top:6px;font-style:italic;}
.ep{font-size:13px;color:var(--accent2);margin-bottom:4px;}
'''

_ZH_EXTRA = '''
body{background:linear-gradient(150deg,#f7f7f5 0%,#fef5f2 100%);}
.ch{background:linear-gradient(135deg,#de2910 0%,#a3150a 60%,#de2910 100%);position:relative;}
.ch::before{content:'🐉';font-size:13px;opacity:.45;margin-right:6px;}
.cw{border-left:3px solid #de2910;}
'''


def css_chinese():
    return _ZH_THEME + _BASE_CSS + _ZH_SPECIFIC + _ZH_EXTRA + _SHARED_UI_CSS


# ═══════════════════════════════════════════════════════════
#  KOREAN CSS
# ═══════════════════════════════════════════════════════════

_KO_THEME = '''
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&family=Noto+Serif+KR:wght@700&display=swap');
:root {
    --bg:#f7f5f8;--card-bg:#ffffff;--border:#e2dce8;--text:#1a1a2e;
    --muted:#7a7a8a;--accent:#c0392b;--accent-soft:#fdecea;
    --accent2:#2d6fa3;--accent2-soft:#e8f2f8;
    --ex-bg:#f9f7fa;--ex-border:#d5c9e0;--shadow:0 4px 20px rgba(0,0,0,0.07);--r:16px;
    --flag:"🇰🇷";
}
body{font-family:'Noto Sans KR','Malgun Gothic','Apple SD Gothic Neo',sans-serif;}
'''

_KO_SPECIFIC = '''
.pinyin{font-size:16px;color:var(--muted);letter-spacing:.05em;min-height:22px;margin-bottom:4px;}
.hanzi{font-family:'Noto Serif KR','Malgun Gothic',serif;font-size:60px;font-weight:700;color:var(--text);line-height:1.2;}
.ep{font-size:13px;color:var(--accent2);margin-bottom:4px;}
'''

_KO_EXTRA = '''
body{background:linear-gradient(150deg,#f7f5f8 0%,#fef4f4 100%);}
.ch{background:linear-gradient(135deg,#c60c30 0%,#8e0a22 60%,#c60c30 100%);position:relative;}
.ch::before{content:'🎎';font-size:13px;opacity:.45;margin-right:6px;}
.cw{border-left:3px solid #c60c30;}
'''


def css_korean():
    return _KO_THEME + _BASE_CSS + _KO_SPECIFIC + _KO_EXTRA + _SHARED_UI_CSS


# ═══════════════════════════════════════════════════════════
#  ENGLISH CSS
# ═══════════════════════════════════════════════════════════

_EN_THEME = '''
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=Merriweather:wght@700&display=swap');
:root {
    --bg:#f4f7fb;--card-bg:#ffffff;--border:#dce4ef;--text:#152238;
    --muted:#718096;--accent:#c8102e;--accent-soft:#fdecef;
    --accent2:#1f5fa8;--accent2-soft:#eaf2fb;
    --ex-bg:#f8fafc;--ex-border:#d9e2ec;--shadow:0 4px 20px rgba(31,70,110,.09);--r:16px;
    --flag:"🇬🇧";
}
body{font-family:'Inter','Segoe UI',Arial,sans-serif;}
'''

_EN_SPECIFIC = '''
.pinyin{font-size:16px;color:var(--accent2);letter-spacing:.03em;min-height:22px;margin-bottom:5px;}
.hanzi{font-family:'Merriweather',Georgia,serif;font-size:50px;font-weight:700;color:var(--text);line-height:1.2;}
'''

_EN_EXTRA = '''
body{background:linear-gradient(150deg,#f4f7fb 0%,#fff5f6 100%);}
.ch{background:linear-gradient(135deg,#1f5fa8 0%,#173f72 60%,#c8102e 100%);}
.cw{border-left:3px solid #1f5fa8;}
'''


def css_english():
    return _EN_THEME + _BASE_CSS + _EN_SPECIFIC + _EN_EXTRA + _SHARED_UI_CSS


# LANG_CSS Registry
LANG_CSS = {
    "japanese": css_japanese,
    "chinese":  css_chinese,
    "korean":   css_korean,
    "english":  css_english,
}


# ═══════════════════════════════════════════════════════════
#  GRAMMAR CSS — Note Type ngữ pháp (dùng chung 2 ngôn ngữ)
# ═══════════════════════════════════════════════════════════
_GRAMMAR_EXTRA = '''
.ch{background:linear-gradient(135deg,#34495e 0%,#22313f 60%,#34495e 100%);}
.ch::before{content:'📘';font-size:13px;opacity:.5;margin-right:6px;}
.cw{border-left:3px solid #34495e;}
.kanji,.hanzi{font-size:44px;}
/* Đánh dấu pattern trong câu ví dụ (AI bọc <b>…</b>) */
.ec .ej b,.ec .ep b{color:var(--accent);font-weight:900;background:var(--accent-soft);border-radius:3px;padding:0 2px;}
/* ── Panel Luyện dịch AI (ngữ pháp) ── */
.ga-box{margin-top:14px;padding:14px;border:1px dashed var(--border,#ccc);border-radius:14px;background:var(--ex-bg,rgba(0,0,0,.03));}
.ga-head{font-size:12px;font-weight:800;color:var(--accent);margin-bottom:6px;}
.ga-status{font-size:12px;color:var(--muted,#777);margin-bottom:6px;}
.ga-sentence{font-size:20px;font-weight:700;min-height:32px;line-height:1.5;color:var(--text,#222);padding:6px 0;}
.ga-btn{display:inline-block;margin:4px 6px 4px 0;padding:7px 14px;border:none;border-radius:10px;
  background:linear-gradient(135deg,#4fa3d1,#2980b9);color:#fff;font-weight:700;font-size:13px;cursor:pointer;}
.ga-btn:hover{filter:brightness(1.08);}
.ga-input{display:none;width:100%;box-sizing:border-box;margin:6px 0;padding:9px 12px;
  border:1px solid var(--border,#bbb);border-radius:10px;font-size:14px;background:var(--card-bg,#fff);color:var(--text,#222);}
'''


def css_japanese_grammar():
    return _JA_THEME + _BASE_CSS + _JA_SPECIFIC + _GRAMMAR_EXTRA + _SHARED_UI_CSS


def css_chinese_grammar():
    return _ZH_THEME + _BASE_CSS + _ZH_SPECIFIC + _GRAMMAR_EXTRA + _SHARED_UI_CSS


def css_korean_grammar():
    return _KO_THEME + _BASE_CSS + _KO_SPECIFIC + _GRAMMAR_EXTRA + _SHARED_UI_CSS


def css_english_grammar():
    return _EN_THEME + _BASE_CSS + _EN_SPECIFIC + _GRAMMAR_EXTRA + _SHARED_UI_CSS


# LANG_GRAMMAR_CSS Registry
LANG_GRAMMAR_CSS = {
    "japanese": css_japanese_grammar,
    "chinese":  css_chinese_grammar,
    "korean":   css_korean_grammar,
    "english":  css_english_grammar,
}
