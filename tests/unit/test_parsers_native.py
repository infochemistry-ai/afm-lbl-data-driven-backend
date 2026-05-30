from app.parsers import get_parser_for_extension, list_parsers
from app.parsers.native import NativeAfmParser


def test_native_parser_registered_for_known_extensions():
    for ext in (".spm", ".ibw", ".sxm"):
        assert get_parser_for_extension(ext) is NativeAfmParser


def test_native_parser_listed():
    assert "native" in list_parsers()
