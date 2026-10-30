import os

# Tests prüfen die deutschen Quelltexte, unabhängig von der Sprache des Rechners.
os.environ["TRETLAGER_LANG"] = "de"

# Protokoll und Zustand der Tests nicht in die echten Ordner des Benutzers schreiben.
import tempfile  # noqa: E402

_tmp = tempfile.mkdtemp(prefix="tretlager-tests-")
os.environ["XDG_STATE_HOME"] = os.path.join(_tmp, "state")
