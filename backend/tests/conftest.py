"""
Shared test configuration and fixtures.

Sets up sys.path and mocks heavy dependencies before any backend module
is imported. This prevents loading the SentenceTransformer model, creating
a real ChromaDB on disk, or calling the Anthropic API during tests.
"""

import os
import sys
import types
from unittest.mock import MagicMock

# Add backend/ to sys.path so tests can import backend modules directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock heavy/external dependencies before any backend module imports them
for _mod in [
    "chromadb",
    "chromadb.config",
    "chromadb.utils",
    "chromadb.utils.embedding_functions",
    "sentence_transformers",
    "anthropic",
]:
    sys.modules[_mod] = MagicMock()


# Replace StaticFiles with a no-op class so app.py can be imported without
# ../frontend existing on disk.
class _FakeStaticFiles:
    def __init__(self, *args, **kwargs):
        pass

    async def __call__(self, scope, receive, send):
        pass


# Inject fake StaticFiles so app.py can be imported without ../frontend existing.
# Using types.ModuleType avoids needing starlette/fastapi installed just for conftest.
for _mod_name in ("starlette.staticfiles", "fastapi.staticfiles"):
    if _mod_name not in sys.modules:
        _m = types.ModuleType(_mod_name)
        _m.StaticFiles = _FakeStaticFiles
        sys.modules[_mod_name] = _m
    else:
        sys.modules[_mod_name].StaticFiles = _FakeStaticFiles
