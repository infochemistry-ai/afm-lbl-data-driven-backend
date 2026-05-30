from typing import Type

from app.parsers.base import Parser, Surface

_REGISTRY: dict[str, Type[Parser]] = {}
_EXT_INDEX: dict[str, Type[Parser]] = {}


def register_parser(cls: Type[Parser]) -> Type[Parser]:
    _REGISTRY[cls.name] = cls
    for ext in cls.extensions:
        _EXT_INDEX[ext.lower()] = cls
    return cls


def get_parser_by_name(name: str) -> Type[Parser]:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown parser: {name}")
    return _REGISTRY[name]


def get_parser_for_extension(ext: str) -> Type[Parser]:
    key = ext.lower()
    if key not in _EXT_INDEX:
        raise KeyError(f"No parser for extension: {ext}")
    return _EXT_INDEX[key]


def list_parsers() -> list[str]:
    return sorted(_REGISTRY)


# Force registration on import.
from app.parsers import txt as _txt  # noqa: E402,F401
from app.parsers import native as _native  # noqa: E402,F401

__all__ = ["register_parser", "get_parser_by_name", "get_parser_for_extension", "list_parsers", "Surface", "Parser"]
