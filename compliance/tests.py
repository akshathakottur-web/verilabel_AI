import json
import unittest
from pathlib import Path

from compliance.default_rules import DEFAULT_RULES
from compliance.extraction import extract_fields
from compliance.rule_logic import evaluate_rules

MOCKS = Path(__file__).resolve().parent.parent / 'mocks'


def load(name):
    with open(MOCKS / name, encoding='utf-8') as file:
        return json.load(file)


def make_vision(lines, detections=None):
    """Builds a small VISION RESULT. Each line is (text, y). Boxes are made up."""
    ocr = []
    for text, y in lines:
        ocr.append({'text': text, 'confidence': 0.9, 'box': [50, y, 600, y + 30], 'language': 'en'})
    return {'image_quality': {'status': 'ok', 'reason': ''},
            'detections': detections or [], 'ocr_lines': ocr}


class SampleTests(unittest.TestCase):
    def test_sample_matches_expected_fields(self):
        vision = load('vision_result_sample.json')
        expected = load('extracted_fields_sample.json')
        got = extract_fields(vision)
        for key, item in expected.items():
            self.assertEqual(got[key]['found'], item['found'], key)
            self.assertEqual(got[key]['value'], item['value'], key)

    def test_sample_score_and_verdict(self):
        vision = load('vision_result_sample.json')
        fields = extract_fields(vision)
        results, score, verdict = evaluate_rules(DEFAULT_RULES, fields, vision['detections'])
        self.assertEqual(len(results), 11)
        failed = [r['rule_id'] for r in results if r['status'] == 'FAIL']
        self.assertEqual(failed, ['R04'])
        self.assertEqual(score, 91)
        self.assertEqual(verdict, 'PARTIAL')


class NoisyTextTests(unittest.TestCase):
    def test_dates_on_one_line_and_relative_expiry(self):
        fields = extract_fields(make_vision([('Mfg: 05/11/2026  Exp: 04/05/2027', 100)]))
        self.assertEqual(fields['manufacturing_date']['value'], '2026-11-05')
        self.assertEqual(fields['expiry_date']['value'], '2027-05-04')
        fields = extract_fields(make_vision([
            ('MFG DATE: 15 NOV 2026', 100),
            ('BEST BEFORE 6 MONTHS FROM THE DATE OF MANUFACTURE', 140)]))
        self.assertEqual(fields['manufacturing_date']['value'], '2026-11-15')
        self.assertEqual(fields['expiry_date']['value'], '2027-05-15')

    def test_relative_expiry_without_mfg(self):
        fields = extract_fields(make_vision([('Best before 9 months from packing', 100)]))
        self.assertEqual(fields['expiry_date']['value'], '9 months from manufacture')

    def test_month_year_dates_and_date_on_next_line(self):
        fields = extract_fields(make_vision([('Mfg. Date', 100), ('10/2026', 140), ('Use by', 180), ('MAR 2027', 220)]))
        self.assertEqual(fields['manufacturing_date']['value'], '2026-10-01')
        self.assertEqual(fields['expiry_date']['value'], '2027-03-31')

    def test_licence_with_spaces_and_wrong_length(self):
        fields = extract_fields(make_vision([('FSSAI Lic No: 1001 2345 678901', 100)]))
        self.assertEqual(fields['fssai_licence_number']['value'], '10012345678901')
        fields = extract_fields(make_vision([('FSSAI Lic. No. 100123456789', 100)]))
        self.assertTrue(fields['fssai_licence_number']['found'])
        vision = make_vision([('FSSAI Lic. No. 100123456789', 100)])
        results, _, _ = evaluate_rules(DEFAULT_RULES, extract_fields(vision), [])
        r10 = [r for r in results if r['rule_id'] == 'R10'][0]
        self.assertEqual(r10['status'], 'FAIL')
        self.assertIn('12 digits', r10['reason'])

    def test_ocr_letter_mistakes(self):
        fields = extract_fields(make_vision([
            ('NUTRITION INFORMATION per 100 g', 100),
            ('Energy 1885 kJ (450 kcal)', 140),
            ('Protein 7 g', 180),
            ('Carbohydrate 76 g', 220),
            ('Total Fat l4 g', 260),
            ('Sodiurn 0.33 g', 300)]))
        values = fields['nutrition']['value']
        self.assertEqual(values['energy_kcal'], 450)
        self.assertEqual(values['total_fat_g'], 14)
        self.assertEqual(values['sodium_mg'], 330)

    def test_kj_only_and_split_lines(self):
        fields = extract_fields(make_vision([
            ('Nutrition Facts', 100), ('Energy', 140), ('1884 kJ', 180), ('Protein', 220), ('8 g', 260)]))
        values = fields['nutrition']['value']
        self.assertEqual(values['energy_kcal'], 450)
        self.assertEqual(values['protein_g'], 8)

    def test_net_quantity_variants(self):
        self.assertEqual(extract_fields(make_vision([('Net Weight 1.5 kg', 100)]))['net_quantity']['value'], '1.5 kg')
        self.assertEqual(extract_fields(make_vision([('NET QTY: 500 ml', 100)]))['net_quantity']['value'], '500 ml')
        self.assertEqual(extract_fields(make_vision([('Net Wt. 2OO gm', 100)]))['net_quantity']['value'], '200 g')

    def test_ingredients_heading_with_ocr_mistake_and_stop(self):
        fields = extract_fields(make_vision([
            ('lNGREDlENTS: Rice flour, Salt,', 100),
            ('Edible oil, Spices.', 130),
            ('Net Wt. 100 g', 300)]))
        self.assertEqual(fields['ingredients']['value'], 'Rice flour, Salt, Edible oil, Spices')

    def test_allergen_statement(self):
        fields = extract_fields(make_vision([('Allergen Information: Contains milk and wheat.', 100)]))
        self.assertEqual(fields['allergens']['value'], 'Contains milk and wheat')
        # A flavour statement is not an allergen statement.
        fields = extract_fields(make_vision([('Contains added flavour (natural flavouring substances)', 100)]))
        self.assertFalse(fields['allergens']['found'])

    def test_allergen_rule_passes_when_no_allergen_in_ingredients(self):
        vision = make_vision([('Ingredients: Rice, salt, turmeric', 100)])
        results, _, _ = evaluate_rules(DEFAULT_RULES, extract_fields(vision), [])
        r04 = [r for r in results if r['rule_id'] == 'R04'][0]
        self.assertEqual(r04['status'], 'PASS')

    def test_veg_marks(self):
        self.assertEqual(extract_fields(make_vision([('x', 10)], [
            {'class': 'nonveg_symbol', 'confidence': 0.8, 'box': [0, 0, 10, 10]}]))['veg_nonveg_mark']['value'], 'nonveg')
        self.assertEqual(extract_fields(make_vision([('NON VEG', 10)]))['veg_nonveg_mark']['value'], 'nonveg')
        self.assertEqual(extract_fields(make_vision([('Pure Vegetarian', 10)]))['veg_nonveg_mark']['value'], 'veg')
        self.assertFalse(extract_fields(make_vision([('Fresh vegetable oil', 10)]))['veg_nonveg_mark']['found'])

    def test_manufacturer_address_two_lines(self):
        fields = extract_fields(make_vision([
            ('Manufactured by: ABC Foods Pvt Ltd,', 100),
            ('12 Industrial Area, Mysuru - 570001', 135)]))
        self.assertEqual(fields['manufacturer_address']['value'],
                         'ABC Foods Pvt Ltd, 12 Industrial Area, Mysuru - 570001')

    def test_empty_input_does_not_crash(self):
        fields = extract_fields({'image_quality': {'status': 'ok'}, 'detections': [], 'ocr_lines': []})
        self.assertFalse(any(f['found'] for f in fields.values()))
        results, score, verdict = evaluate_rules(DEFAULT_RULES, fields, [])
        self.assertEqual(score, 0)
        self.assertEqual(verdict, 'NON_COMPLIANT')


class BoxAndTextTests(unittest.TestCase):
    """The text step must still work when a YOLO box is missing or wrong."""

    def box(self, class_name, y1, y2, confidence=0.9):
        return {'class': class_name, 'confidence': confidence, 'box': [0, y1, 700, y2]}

    def test_ingredients_box_in_empty_area_falls_back_to_text(self):
        vision = make_vision(
            [('INGREDIENTS: Rice flour, Salt, Oil', 100), ('Net Wt. 100 g', 300)],
            [self.box('ingredients', 800, 900)])
        self.assertEqual(extract_fields(vision)['ingredients']['value'], 'Rice flour, Salt, Oil')

    def test_ingredients_box_over_wrong_line_falls_back_to_text(self):
        vision = make_vision(
            [('INGREDIENTS: Rice flour, Salt, Oil', 100), ('Net Wt. 100 g', 300)],
            [self.box('ingredients', 290, 340)])
        self.assertEqual(extract_fields(vision)['ingredients']['value'], 'Rice flour, Salt, Oil')

    def test_ingredients_box_without_heading_text_is_used(self):
        vision = make_vision(
            [('Wheat flour, Sugar, Palm oil, Salt', 100)],
            [self.box('ingredients', 90, 140)])
        self.assertEqual(extract_fields(vision)['ingredients']['value'], 'Wheat flour, Sugar, Palm oil, Salt')

    def test_no_boxes_at_all_text_only(self):
        vision = make_vision([
            ('INGREDIENTS: Rice flour, Salt', 100),
            ('Contains: Milk', 140),
            ('FSSAI Lic. No. 10012345678901', 200)])
        fields = extract_fields(vision)
        self.assertEqual(fields['ingredients']['value'], 'Rice flour, Salt')
        self.assertEqual(fields['allergens']['value'], 'Milk')
        self.assertEqual(fields['fssai_licence_number']['value'], '10012345678901')

    def test_allergen_box_over_wrong_line_falls_back_to_text(self):
        vision = make_vision(
            [('Net Wt. 100 g', 100), ('Contains: Milk and Wheat', 300)],
            [self.box('allergen', 90, 140)])
        self.assertEqual(extract_fields(vision)['allergens']['value'], 'Milk and Wheat')

    def test_nutrition_keeps_the_fuller_result(self):
        vision = make_vision([
            ('NUTRITION INFORMATION', 100),
            ('Energy 450 kcal', 140),
            ('Protein 7 g', 180),
            ('Carbohydrate 76 g', 220),
            ('Total Fat 14 g', 260)],
            [self.box('nutrition_table', 130, 170)])
        values = extract_fields(vision)['nutrition']['value']
        self.assertEqual(sorted(values), ['carbohydrate_g', 'energy_kcal', 'protein_g', 'total_fat_g'])

    def test_licence_box_over_wrong_line_still_finds_number(self):
        vision = make_vision(
            [('Net Wt. 100 g', 100), ('FSSAI Lic. No. 10012345678901', 300)],
            [self.box('fssai_no', 90, 140)])
        self.assertEqual(extract_fields(vision)['fssai_licence_number']['value'], '10012345678901')

    def test_low_confidence_detection_is_ignored(self):
        vision = make_vision([('x', 100)], [self.box('fssai_logo', 0, 50, confidence=0.1)])
        results, _, _ = evaluate_rules(DEFAULT_RULES, extract_fields(vision), vision['detections'])
        r09 = [r for r in results if r['rule_id'] == 'R09'][0]
        self.assertEqual(r09['status'], 'FAIL')


class ScoringTests(unittest.TestCase):
    def test_all_pass_is_compliant(self):
        rules = [{'rule_id': 'A', 'name': 'x', 'check_type': 'field_found',
                  'field_key': 'food_name', 'weight': 1, 'enabled': True}]
        fields = {'food_name': {'found': True, 'value': 'x', 'confidence': 1}}
        self.assertEqual(evaluate_rules(rules, fields, [])[1:], (100, 'COMPLIANT'))

    def test_weights_and_disabled_rules(self):
        rules = [
            {'rule_id': 'A', 'name': 'a', 'check_type': 'field_found', 'field_key': 'food_name', 'weight': 3, 'enabled': True},
            {'rule_id': 'B', 'name': 'b', 'check_type': 'field_found', 'field_key': 'net_quantity', 'weight': 1, 'enabled': True},
            {'rule_id': 'C', 'name': 'c', 'check_type': 'field_found', 'field_key': 'ingredients', 'weight': 5, 'enabled': False},
        ]
        fields = {'food_name': {'found': True, 'value': 'x', 'confidence': 1}}
        results, score, verdict = evaluate_rules(rules, fields, [])
        self.assertEqual(len(results), 2)
        self.assertEqual((score, verdict), (75, 'PARTIAL'))

    def test_no_active_rules(self):
        self.assertEqual(evaluate_rules([], {}, [])[1:], (None, None))


if __name__ == '__main__':
    unittest.main()
