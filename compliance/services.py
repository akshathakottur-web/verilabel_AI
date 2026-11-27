"""Functions for the Admin rules page. Member 3's API calls these (see contracts/API_CONTRACT.md).

Every function that gets bad input raises ValueError with a message the page can show.
"""
import re

from .extraction import FIELD_NAMES, NUTRIENT_KEYS
from .models import Rule
from .rule_logic import CHECK_TYPE_LABELS, DETECTION_CLASSES


def rule_to_dict(rule):
    return {
        'rule_id': rule.rule_id,
        'name': rule.name,
        'check_type': rule.check_type,
        'field_key': rule.field_key,
        'weight': rule.weight,
        'enabled': rule.enabled,
    }


def list_rules():
    """All rules (also the switched-off ones), in creation order."""
    return [rule_to_dict(rule) for rule in Rule.objects.order_by('id')]


def _clean(data, existing=None):
    """Checks the input and returns the final values for a rule."""
    values = rule_to_dict(existing) if existing else {
        'name': '', 'check_type': '', 'field_key': '', 'weight': 1, 'enabled': True,
    }
    for key in ('name', 'check_type', 'field_key', 'weight', 'enabled'):
        if key in data:
            values[key] = data[key]

    name = str(values['name']).strip()
    if not name or len(name) > 200:
        raise ValueError('The rule name is required and must be at most 200 characters.')
    values['name'] = name

    check_type = values['check_type']
    if check_type not in CHECK_TYPE_LABELS:
        raise ValueError('check_type must be one of: ' + ', '.join(CHECK_TYPE_LABELS))

    field_key = str(values['field_key']).strip()
    if check_type == 'field_found' and field_key not in FIELD_NAMES:
        raise ValueError('field_key must be one of: ' + ', '.join(FIELD_NAMES))
    if check_type == 'detection_found' and field_key not in DETECTION_CLASSES:
        raise ValueError('field_key must be one of: ' + ', '.join(DETECTION_CLASSES))
    if check_type == 'nutrition_values':
        parts = [p.strip() for p in field_key.split(',') if p.strip()]
        if not parts or any(p not in NUTRIENT_KEYS for p in parts):
            raise ValueError('field_key must list nutrients from: ' + ', '.join(NUTRIENT_KEYS))
        field_key = ','.join(parts)
    values['field_key'] = field_key

    try:
        weight = int(values['weight'])
    except (TypeError, ValueError):
        raise ValueError('weight must be a whole number from 1 to 10.')
    if not 1 <= weight <= 10:
        raise ValueError('weight must be a whole number from 1 to 10.')
    values['weight'] = weight

    if not isinstance(values['enabled'], bool):
        raise ValueError('enabled must be true or false.')
    return values


def _next_rule_id():
    numbers = [int(m.group(1)) for r in Rule.objects.all()
               if (m := re.fullmatch(r'R(\d+)', r.rule_id))]
    return f'R{(max(numbers) + 1) if numbers else 1:02d}'


def create_rule(data):
    values = _clean(data)
    rule_id = str(data.get('rule_id') or '').strip() or _next_rule_id()
    if Rule.objects.filter(rule_id=rule_id).exists():
        raise ValueError(f'A rule with the ID {rule_id} already exists.')
    rule = Rule.objects.create(rule_id=rule_id, **values)
    return rule_to_dict(rule)


def update_rule(rule_id, data):
    rule = Rule.objects.filter(rule_id=rule_id).first()
    if rule is None:
        raise ValueError(f'Rule {rule_id} was not found.')
    values = _clean(data, existing=rule)
    for key, value in values.items():
        setattr(rule, key, value)
    rule.save()
    return rule_to_dict(rule)
