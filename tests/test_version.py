import re
from pathlib import Path

import tretlager


def test_version_matches_changelog():
    changelog = (Path(__file__).resolve().parent.parent / "CHANGELOG.md").read_text()
    top = re.search(r"^## \[(\d[^\]]*)\]", changelog, re.M).group(1)
    assert tretlager.__version__ == top


def test_build_id(tmp_path):
    from tretlager import build_id
    info = tmp_path / "flatpak-info"
    info.write_text("[Application]\nname=de.linuxundich.Tretlager\n\n[Instance]\napp-commit=9ea5ca9b93b1b4f1\n")
    assert build_id(str(info)) == "9ea5ca9"
    assert build_id(str(tmp_path / "fehlt")) == ""
