import pytest

pytest.importorskip("PySide6")

from tretlager.kde.i18n import LocalizedContext, _fill  # noqa: E402


def test_fill_replaces_kde_placeholders():
    assert _fill("%1 von %2", [3, 6]) == "3 von 6"
    assert _fill("%1 und %10", list(range(1, 11))) == "1 und 10"


def test_untranslated_domain_falls_back_to_text():
    ctx = LocalizedContext()
    assert ctx.i18nd("tretlager-gibt-es-nicht", "About %1", "Tretlager") == "About Tretlager"
    assert ctx.i18ndp("tretlager-gibt-es-nicht", "License", "Licenses", 2) == "Licenses"
    assert ctx.i18ndc("tretlager-gibt-es-nicht", "ctx", "Close") == "Close"
