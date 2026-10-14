import os
import sys

# Default language: 'en' for global usage, or 'tr' if invoked via 'ajansohbeti' or env var
_default_lang = os.environ.get("AGENT_COUNCIL_LANG", "").strip().lower()
if not _default_lang:
    invoked_as = os.path.basename(sys.argv[0]).lower()
    if "ajansohbeti" in invoked_as:
        _default_lang = "tr"
    else:
        _default_lang = "en"

# Check CLI flags (--lang tr / --lang en / --tr / --en)
if "--tr" in sys.argv or "--lang=tr" in sys.argv:
    _default_lang = "tr"
elif "--en" in sys.argv or "--lang=en" in sys.argv:
    _default_lang = "en"
elif "--lang" in sys.argv:
    idx = sys.argv.index("--lang")
    if idx + 1 < len(sys.argv):
        val = sys.argv[idx + 1].strip().lower()
        if val in ("en", "tr"):
            _default_lang = val

CURRENT_LANG = _default_lang if _default_lang in ("en", "tr") else "en"


def get_lang() -> str:
    return CURRENT_LANG


def set_lang(lang: str) -> None:
    global CURRENT_LANG
    if lang.lower() in ("en", "tr"):
        CURRENT_LANG = lang.lower()


def toggle_lang() -> str:
    global CURRENT_LANG
    CURRENT_LANG = "tr" if CURRENT_LANG == "en" else "en"
    return CURRENT_LANG


def is_tr() -> bool:
    return CURRENT_LANG == "tr"


def t(en_text: str, tr_text: str) -> str:
    """Return translated string based on current active language."""
    return tr_text if CURRENT_LANG == "tr" else en_text
