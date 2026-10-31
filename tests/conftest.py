import os

# Tests run with the English UI language, independent of the machine's locale;
# several tests compare UI texts.
os.environ["TRETLAGER_LANG"] = "en"

# Do not write the tests' log and state into the user's real directories.
import tempfile  # noqa: E402

_tmp = tempfile.mkdtemp(prefix="tretlager-tests-")
os.environ["XDG_STATE_HOME"] = os.path.join(_tmp, "state")
