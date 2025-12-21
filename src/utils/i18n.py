import gettext

def setup_i18n(language):
    _ = gettext.translation(
        domain="messages",
        localedir="locale",
        languages=[language],
        fallback=True,
    ).gettext
    return _
