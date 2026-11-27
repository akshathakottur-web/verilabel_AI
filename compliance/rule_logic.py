"""The FSSAI rule checks and the scoring. No Django code, so it can be tested on its own.

A rule is a small record: rule_id, name, check_type, field_key, weight, enabled.
The checks read the EXTRACTED FIELDS and the YOLO detections.
"""
import re

from .extraction import ALLERGEN_WORDS, FIELD_NAMES, MIN_DETECTION_CONF, NUTRIENT_KEYS

DETECTION_CLASSES = [
    'veg_symbol', 'nonveg_symbol', 'nutrition_table', 'allergen',
    'fssai_no', 'ingredients', 'fssai_logo',
]

CHECK_TYPE_LABELS = {
    'field_found': 'A field was found on the label (field_key = the field name)',
    'detection_found': 'A detected item was found (field_key = the detection class)',
    'nutrition_values': 'Required nutrition values were read (field_key = comma-separated nutrient names)',
    'allergen_declared': 'An allergen declaration is present when the ingredients need one',
    'fssai_licence_14': 'The FSSAI licence number has exactly 14 digits',
}


def _field(fields, key):
    return fields.get(key) or {'found': False, 'value': None, 'confidence': 0.0}


def check_field_found(rule, fields, detections):
    field = _field(fields, rule['field_key'])
    if field['found']:
        return True, f"{rule['name']} found"
    return False, f"{rule['name']} not found on the label"


def check_detection_found(rule, fields, detections):
    for item in detections:
        if item.get('class') == rule['field_key'] and float(item.get('confidence', 0)) >= MIN_DETECTION_CONF:
            return True, f"{rule['name']} detected"
    return False, f"{rule['name']} not detected on the label"


def check_nutrition_values(rule, fields, detections):
    required = [k.strip() for k in rule['field_key'].split(',') if k.strip()] or NUTRIENT_KEYS
    field = _field(fields, 'nutrition')
    values = field['value'] if field['found'] and isinstance(field['value'], dict) else {}
    absent = [k for k in required if k not in values]
    if not field['found']:
        return False, 'Nutrition information not found on the label'
    if absent:
        return False, 'Nutrition values missing: ' + ', '.join(absent)
    return True, 'Required nutrition values found'


def allergen_words_in(text):
    low = (text or '').lower()
    return sorted({w for w in ALLERGEN_WORDS if re.search(r'\b' + w + r'\b', low)})


def check_allergen_declared(rule, fields, detections):
    if _field(fields, 'allergens')['found']:
        return True, 'Allergen declaration found'
    ingredients = _field(fields, 'ingredients')
    if ingredients['found']:
        hits = allergen_words_in(str(ingredients['value']))
        if hits:
            return False, 'Ingredients mention ' + ', '.join(hits) + ' but no allergen declaration was found'
        return True, 'No common allergen found in the ingredients, so no declaration is needed'
    return False, 'No allergen declaration found (ingredients could not be read to check)'


def check_fssai_licence_14(rule, fields, detections):
    field = _field(fields, 'fssai_licence_number')
    if not field['found']:
        return False, 'FSSAI licence number not found on the label'
    digits = re.sub(r'\D', '', str(field['value']))
    if len(digits) == 14:
        return True, '14-digit licence number found'
    return False, f'Licence number has {len(digits)} digits, it must have 14'


CHECKS = {
    'field_found': check_field_found,
    'detection_found': check_detection_found,
    'nutrition_values': check_nutrition_values,
    'allergen_declared': check_allergen_declared,
    'fssai_licence_14': check_fssai_licence_14,
}


def evaluate_rules(rules, fields, detections, partial_min=70):
    """Returns (rule_results, score, verdict).

    score = share of rule weight that passed, from 0 to 100.
    verdict: COMPLIANT (everything passed), PARTIAL (score at least partial_min),
    NON_COMPLIANT (below that). With no active rules: score and verdict are None.
    """
    results = []
    total, passed = 0, 0
    for rule in rules:
        if not rule.get('enabled', True):
            continue
        weight = max(int(rule.get('weight', 1)), 1)
        check = CHECKS.get(rule['check_type'])
        if check is None:
            ok, reason = False, f"Unknown check type: {rule['check_type']}"
        else:
            ok, reason = check(rule, fields, detections)
        total += weight
        passed += weight if ok else 0
        results.append({
            'rule_id': rule['rule_id'],
            'name': rule['name'],
            'status': 'PASS' if ok else 'FAIL',
            'reason': reason,
        })
    if total == 0:
        return results, None, None
    score = round(100 * passed / total)
    if passed == total:
        verdict = 'COMPLIANT'
    elif score >= partial_min:
        verdict = 'PARTIAL'
    else:
        verdict = 'NON_COMPLIANT'
    return results, score, verdict
