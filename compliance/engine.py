
import json
from pathlib import Path

from django.conf import settings

MOCKS_DIR = Path(settings.BASE_DIR) / 'mocks'


def _load(name):
    with open(MOCKS_DIR / name, encoding='utf-8') as file:
        return json.load(file)


def run_compliance(vision_result):
    """Takes a VISION RESULT, returns (extracted_fields, compliance_result).

    PLACEHOLDER: returns the sample files from mocks/ until Stage 4 adds the
    real text extraction and FSSAI rule engine.
    """
    extracted_fields = _load('extracted_fields_sample.json')
    compliance_result = _load('compliance_result_sample.json')
    return extracted_fields, compliance_result
