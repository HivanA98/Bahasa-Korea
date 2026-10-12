"""Penyiapan pytest: pastikan folder proyek ada di sys.path."""

import importlib.util
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def load_tool(name: str) -> types.ModuleType:
    """Muat skrip di tools/ sebagai modul, tanpa menjadikan tools/ paket."""
    path = os.path.join(ROOT, "tools", f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"_tool_{name}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
