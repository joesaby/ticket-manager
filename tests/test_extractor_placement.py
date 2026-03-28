import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock native dependencies before importing the module
sys.modules.setdefault('pyzbar', MagicMock())
sys.modules.setdefault('pyzbar.pyzbar', MagicMock())
sys.modules.setdefault('cv2', MagicMock())
sys.modules.setdefault('fitz', MagicMock())

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import fitz  # now the mock
fitz.Rect = lambda x0, y0, x1, y1: MagicMock(x0=x0, y0=y0, x1=x1, y1=y1)

from complete_qr_extractor import CompleteQRExtractor


def test_absolute_position_used_when_qr_xy_provided():
    """When qr_x and qr_y are given, box is placed at those exact coords."""
    extractor = CompleteQRExtractor()

    positions = []

    def capture_rect(rect, stream, overlay):
        positions.append((rect.x0, rect.y0))

    mock_page = MagicMock()
    mock_page.rect = MagicMock(width=800, height=600)
    mock_page.insert_image = capture_rect

    # Minimal box image (1x1 white pixel PNG)
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (60, 70), "white").save(buf, format="PNG")
    box_image_bytes = buf.getvalue()

    extractor._place_box_on_page(mock_page, box_image_bytes, qr_scale=1.0, qr_x=100, qr_y=200)

    assert len(positions) == 1
    assert positions[0] == (100, 200)


def test_margin_position_used_when_no_qr_xy():
    """When qr_x/qr_y are absent, falls back to margin-based right placement."""
    extractor = CompleteQRExtractor()

    positions = []

    def capture_rect(rect, stream, overlay):
        positions.append((rect.x0, rect.y0))

    mock_page = MagicMock()
    mock_page.rect = MagicMock(width=800, height=600)
    mock_page.insert_image = capture_rect

    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (60, 70), "white").save(buf, format="PNG")
    box_image_bytes = buf.getvalue()

    extractor._place_box_on_page(mock_page, box_image_bytes, qr_scale=1.0,
                                  qr_position='right', qr_margin=20,
                                  design_width=800, design_height=600)

    assert len(positions) == 1
    x, y = positions[0]
    # right margin: x = 800 - 60 - 20 = 720
    assert x == 720
    # y = 600 - 70 - 20 = 510
    assert y == 510
