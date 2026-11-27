"""The 11 default FSSAI rules. 'python manage.py seed_rules' copies them into the database.

After that the Admin can edit them (name, weight, on/off) without changing code.
"""

DEFAULT_RULES = [
    {'rule_id': 'R01', 'name': 'Name of the food', 'check_type': 'field_found',
     'field_key': 'food_name', 'weight': 1, 'enabled': True},
    {'rule_id': 'R02', 'name': 'List of ingredients', 'check_type': 'field_found',
     'field_key': 'ingredients', 'weight': 1, 'enabled': True},
    {'rule_id': 'R03', 'name': 'Nutrition information', 'check_type': 'nutrition_values',
     'field_key': 'energy_kcal,protein_g,carbohydrate_g,total_fat_g', 'weight': 1, 'enabled': True},
    {'rule_id': 'R04', 'name': 'Allergen declaration', 'check_type': 'allergen_declared',
     'field_key': '', 'weight': 1, 'enabled': True},
    {'rule_id': 'R05', 'name': 'Veg / non-veg symbol', 'check_type': 'field_found',
     'field_key': 'veg_nonveg_mark', 'weight': 1, 'enabled': True},
    {'rule_id': 'R06', 'name': 'Net quantity', 'check_type': 'field_found',
     'field_key': 'net_quantity', 'weight': 1, 'enabled': True},
    {'rule_id': 'R07', 'name': 'Manufacturing date', 'check_type': 'field_found',
     'field_key': 'manufacturing_date', 'weight': 1, 'enabled': True},
    {'rule_id': 'R08', 'name': 'Expiry or best-before date', 'check_type': 'field_found',
     'field_key': 'expiry_date', 'weight': 1, 'enabled': True},
    {'rule_id': 'R09', 'name': 'FSSAI logo', 'check_type': 'detection_found',
     'field_key': 'fssai_logo', 'weight': 1, 'enabled': True},
    {'rule_id': 'R10', 'name': 'FSSAI licence number (14 digits)', 'check_type': 'fssai_licence_14',
     'field_key': 'fssai_licence_number', 'weight': 1, 'enabled': True},
    {'rule_id': 'R11', 'name': 'Manufacturer name and address', 'check_type': 'field_found',
     'field_key': 'manufacturer_address', 'weight': 1, 'enabled': True},
]
