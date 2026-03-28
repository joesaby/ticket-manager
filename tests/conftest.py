import sys
import os

# Add project root to path so app.py is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Pre-import real fitz and app BEFORE test_extractor_placement.py is collected.
# test_extractor_placement.py uses sys.modules.setdefault() at module level to
# mock fitz for its unit tests. Since setdefault() only sets if absent, importing
# the real fitz here first ensures test_app.py gets the real module.
import fitz  # noqa
import app   # noqa
