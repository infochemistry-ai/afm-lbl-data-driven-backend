import numpy as np

from app.parsers import get_parser_for_extension
from app.parsers.txt import TxtParser


def test_txt_parser_registered():
    cls = get_parser_for_extension(".txt")
    assert cls is TxtParser


def test_txt_parser_reads_fixture():
    p = TxtParser()
    surface = p.parse("tests/fixtures/sample_scan.txt")
    assert surface.heights.ndim == 2
    assert surface.heights.dtype == np.float64
    assert surface.width_um == 5.02
    assert surface.height_um == 5.02
    assert surface.units == "m"
    assert "Height" in (surface.channel or "")
    assert surface.heights.shape[0] == surface.heights.shape[1]
