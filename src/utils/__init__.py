"""
BuyWise Utilities
Re-exports core dashboard utilities (apply_custom_css, load_data)
so imports always succeed whether resolving to package or module.
"""

import sys
from pathlib import Path

_DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "dashboard"
if str(_DASHBOARD_DIR) not in sys.path:
    sys.path.insert(0, str(_DASHBOARD_DIR))

try:
    from src.dashboard.utils import apply_custom_css, load_data
except Exception:
    try:
        from dashboard.utils import apply_custom_css, load_data
    except Exception:
        import importlib.util
        _spec = importlib.util.spec_from_file_location("dashboard_utils", str(_DASHBOARD_DIR / "utils.py"))
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        apply_custom_css = _mod.apply_custom_css
        load_data = _mod.load_data

__all__ = ["apply_custom_css", "load_data"]
