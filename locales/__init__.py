from locales import en, ru

LOCALES = {
    "en": en.TEXTS,
    "ru": ru.TEXTS,
}

DEFAULT_LANG = "ru"
SUPPORTED_LANGS = ("en", "ru")


def t(lang: str, key: str, **kwargs) -> str:
    texts = LOCALES.get(lang, LOCALES[DEFAULT_LANG])
    template = texts.get(key, LOCALES[DEFAULT_LANG][key])
    if kwargs:
        return template.format(**kwargs)
    return template


def btn(lang: str, key: str) -> str:
    return t(lang, f"btn_{key}")


def all_button_texts(key: str) -> frozenset[str]:
    return frozenset(t(code, f"btn_{key}") for code in SUPPORTED_LANGS)


BUTTON_KEYS = (
    "start_search",
    "matched",
    "rejected",
    "applied",
    "settings",
    "change_query",
    "change_filter",
    "language",
)

ALL_MENU_TEXTS = frozenset(
    text for key in BUTTON_KEYS for text in all_button_texts(key)
)
