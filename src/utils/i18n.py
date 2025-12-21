import gettext
from typing import Callable

def setup_i18n(language: str) -> Callable[[str], str]:
    _ = gettext.translation(
        domain="messages",
        localedir="locale",
        languages=[language],
        fallback=True,
    ).gettext
    return _
