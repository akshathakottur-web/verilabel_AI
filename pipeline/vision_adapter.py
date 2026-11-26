
import json
from pathlib import Path

from django.conf import settings

MOCK_FILE = Path(settings.BASE_DIR) / 'mocks' / 'vision_result_sample.json'


def get_vision_result(image_path):
    """Returns a VISION RESULT (see contracts/PIPELINE_CONTRACT.md)."""
    if settings.USE_MOCK_VISION:
        with open(MOCK_FILE, encoding='utf-8') as file:
            return json.load(file)
    from ai_vision import analyze_image
    return analyze_image(image_path)
