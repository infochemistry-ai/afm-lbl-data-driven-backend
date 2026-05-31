"""
Feature-extractor plugin registry.

Each extractor module under ``app.features`` declares a class that conforms
to :class:`app.features.base.FeatureExtractor` and decorates it with
:func:`register_extractor`. Importing this package triggers registration of
all built-in extractors via the ``from app.features import ...`` block at
the bottom of this file.

Worker code iterates over the registry through
:func:`all_extractors_by_scope` (``"scan"`` or ``"sample"``); the HTTP API
exposes :func:`list_extractors` and :func:`get_extractor` for name-based
lookup.
"""

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

# Force registration on import.
from app.features import metadata as _metadata  # noqa: E402,F401
from app.features import iso25178 as _iso25178  # noqa: E402,F401
from app.features import distribution as _distribution  # noqa: E402,F401
from app.features import polyelectrolyte as _polyelectrolyte  # noqa: E402,F401
from app.features import minmax_patches as _minmax_patches  # noqa: E402,F401
# preprocessing is invoked directly (not registered as a feature row), no import needed.
from app.features import pe_sequence_kmer as _pe_sequence_kmer  # noqa: E402,F401
from app.features import acf_2d as _acf_2d  # noqa: E402,F401
from app.features import psd_radial as _psd_radial  # noqa: E402,F401
from app.features import acf_rowcol as _acf_rowcol  # noqa: E402,F401
from app.features import rdkit_monomer as _rdkit_monomer  # noqa: E402,F401
from app.features import tda_persistence as _tda_persistence  # noqa: E402,F401
from app.features import lacunarity as _lacunarity  # noqa: E402,F401
