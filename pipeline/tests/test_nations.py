import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nations import CODE_PATTERN, NATION_CODES, UnknownNationError, nation_code  # noqa: E402

FLAGS_DIR = Path(__file__).resolve().parents[2] / "app" / "node_modules" / "flag-icons" / "flags" / "4x3"


def test_codes_have_the_flag_icons_format():
    bad = {n: c for n, c in NATION_CODES.items() if not CODE_PATTERN.match(c)}
    assert bad == {}


def test_home_nations_and_kosovo():
    assert nation_code("England") == "gb-eng"
    assert nation_code("Scotland") == "gb-sct"
    assert nation_code("Wales") == "gb-wls"
    assert nation_code("Northern Ireland") == "gb-nir"
    assert nation_code("Kosovo") == "xk"
    assert nation_code("Côte d'Ivoire") == "ci"


def test_codes_are_unique():
    codes = list(NATION_CODES.values())
    assert len(codes) == len(set(codes))


def test_unknown_nation_raises():
    with pytest.raises(UnknownNationError, match="Atlantis"):
        nation_code("Atlantis")


@pytest.mark.skipif(not FLAGS_DIR.exists(), reason="app/node_modules/flag-icons not installed")
def test_every_code_has_a_flag_file():
    missing = sorted(c for c in NATION_CODES.values() if not (FLAGS_DIR / f"{c}.svg").exists())
    assert missing == []
