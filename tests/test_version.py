import re
from pathlib import Path

import tretlager


def test_version_matches_changelog():
    changelog = (Path(__file__).resolve().parent.parent / "CHANGELOG.md").read_text()
    top = re.search(r"^## \[(\d[^\]]*)\]", changelog, re.M).group(1)
    assert tretlager.__version__ == top
