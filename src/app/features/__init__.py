from typing import Type

from app.features.base import FeatureExtractor

_REGISTRY: dict[str, Type[FeatureExtractor]] = {}


def register_extractor(cls: Type[FeatureExtractor]) -> Type[FeatureExtractor]:
    _REGISTRY[cls.name] = cls
    return cls


def list_extractors() -> list[str]:
    return sorted(_REGISTRY)


def get_extractor(name: str) -> Type[FeatureExtractor]:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown extractor: {name}")
    return _REGISTRY[name]


def all_extractors_by_scope(scope: str) -> list[Type[FeatureExtractor]]:
    return [cls for cls in _REGISTRY.values() if cls.scope == scope]


__all__ = ["register_extractor", "list_extractors", "get_extractor", "all_extractors_by_scope"]
