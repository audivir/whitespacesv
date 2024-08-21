"""The main module of the whitespacesv package."""

from __future__ import annotations

from whitespacesv.document import WsvDocument
from whitespacesv.utils import reinfer_types

__all__ = ["WsvDocument", "SerializationMode", "reinfer_types"]
