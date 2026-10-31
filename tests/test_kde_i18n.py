import pytest

pytest.importorskip("PySide6")

from tretlager.kde.i18n import LocalizedContext, _fill  # noqa: E402


def test_fill_replaces_kde_placeholders():
    assert _fill("%1 of %2", [3, 6]) == "3 of 6"
    assert _fill("%1 and %10", list(range(1, 11))) == "1 and 10"


def test_untranslated_domain_falls_back_to_text():
    ctx = LocalizedContext()
    assert ctx.i18nd("tretlager-does-not-exist", "About %1", "Tretlager") == "About Tretlager"
    assert ctx.i18ndp("tretlager-does-not-exist", "License", "Licenses", 2) == "Licenses"
    assert ctx.i18ndc("tretlager-does-not-exist", "ctx", "Close") == "Close"
