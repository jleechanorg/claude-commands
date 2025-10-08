"""Compatibility shim for legacy ``firestore_service`` imports.

Historically modules imported ``firestore_service`` from the project root. This
shim returns the canonical module object from ``mvp_site.firestore_service`` so
that monkeypatching and attribute assignment affect the real implementation.
"""

from importlib import import_module
import sys

_module = import_module("mvp_site.firestore_service")
sys.modules[__name__] = _module

# Re-export public attributes for type checkers and tooling
__all__ = getattr(_module, "__all__", [])
