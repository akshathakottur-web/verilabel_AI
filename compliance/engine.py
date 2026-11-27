from django.conf import settings

from .default_rules import DEFAULT_RULES
from .extraction import extract_fields
from .models import Rule
from .rule_logic import evaluate_rules


def get_active_rules():
    """Rules come from the database. If the table is empty, the default rules are used."""
    if not Rule.objects.exists():
        return [dict(rule) for rule in DEFAULT_RULES if rule['enabled']]
    return [
        {
            'rule_id': rule.rule_id,
            'name': rule.name,
            'check_type': rule.check_type,
            'field_key': rule.field_key,
            'weight': rule.weight,
            'enabled': rule.enabled,
        }
        for rule in Rule.objects.filter(enabled=True).order_by('id')
    ]


def run_compliance(vision_result):
    """Takes a VISION RESULT, returns (extracted_fields, compliance_result)."""
    extracted_fields = extract_fields(vision_result)
    results, score, verdict = evaluate_rules(
        get_active_rules(),
        extracted_fields,
        vision_result.get('detections', []),
        partial_min=settings.VERDICT_PARTIAL_MIN,
    )
    compliance_result = {
        'image_quality_warning': None,
        'rules': results,
        'score': score,
        'verdict': verdict,
    }
    return extracted_fields, compliance_result
