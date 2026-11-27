"""Turns a VISION RESULT into EXTRACTED FIELDS (see contracts/PIPELINE_CONTRACT.md).

This file has no Django code, so it can be tested on its own.
It reads the OCR lines and the YOLO boxes together: a detection box tells us
which OCR lines belong to ingredients, the nutrition table, the licence number
and so on. When a box is missing, it falls back to searching the text.
"""
import calendar
import re
from datetime import date, timedelta

try:
    from rapidfuzz import fuzz

    def similarity(a, b):
        return fuzz.ratio(a, b)
except ImportError:  # keeps the code testable without rapidfuzz installed
    from difflib import SequenceMatcher

    def similarity(a, b):
        return SequenceMatcher(None, a, b).ratio() * 100

FIELD_NAMES = [
    'food_name', 'ingredients', 'nutrition', 'allergens', 'net_quantity',
    'manufacturing_date', 'expiry_date', 'fssai_licence_number',
    'manufacturer_address', 'veg_nonveg_mark',
]
NUTRIENT_KEYS = [
    'energy_kcal', 'protein_g', 'carbohydrate_g', 'total_sugars_g',
    'total_fat_g', 'saturated_fat_g', 'sodium_mg',
]
MIN_DETECTION_CONF = 0.3

MONTHS = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}
ALLERGEN_WORDS = [
    'wheat', 'gluten', 'barley', 'rye', 'oats', 'maida', 'atta',
    'milk', 'lactose', 'whey', 'casein', 'butter', 'ghee', 'cream', 'curd', 'cheese',
    'egg', 'eggs', 'soy', 'soya', 'soybean', 'soybeans',
    'peanut', 'peanuts', 'groundnut', 'groundnuts',
    'almond', 'cashew', 'walnut', 'pistachio', 'hazelnut', 'pecan', 'nuts',
    'fish', 'prawn', 'shrimp', 'crab', 'shellfish', 'crustacean', 'crustaceans',
    'sulphite', 'sulphites', 'sulfite', 'sulfites',
]

MFG_RE = re.compile(
    r'\b(?:mfg|mfd|pkd|manufactur(?:ing|ed)\s*(?:date|on)|manufacture\s*date|'
    r'date\s*of\s*manufacture|packed\s*on|packing\s*date|pack\s*date)\b'
)
EXP_RE = re.compile(
    r'\b(?:best\s*before|use\s*by|use\s*before|expiry(?:\s*date)?|expires?|exp)\b'
)
ADDRESS_RE = re.compile(
    r'\b(?:(?:manufactured|marketed|packed|packaged|distributed|imported)\s*(?:and\s*\w+\s*)?by|'
    r'(?:mfd|mfg|mkt|mktd)\.?\s*by|manufacturer|manufactured\s*at)\b'
)
RELATIVE_RE = re.compile(
    r'(\d{1,2})\s*(month|day|week|year)s?\s*(?:from|after|of)\s*(?:the\s*)?'
    r'(?:date\s*of\s*)?(?:manufactur\w*|mfg|packing|pack\w*)'
)
NUM_DATE_RE = re.compile(r'(\d{1,2})\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(\d{2,4})')
TEXT_DATE_RE = re.compile(
    r'(?:(\d{1,2})\s*[-/ .]?\s*)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*[-/ ,.]?\s*(\d{2,4})'
)
MONTH_YEAR_RE = re.compile(r'\b(\d{1,2})\s*[/\-.]\s*(\d{4})\b')
QTY_RE = re.compile(
    r'(\d+(?:[.,]\d+)?)\s*(kgs?|gms?|grams?|g|ml|ltrs?|litres?|liters?|l)\b'
)
UNIT_MAP = {
    'kg': 'kg', 'kgs': 'kg', 'g': 'g', 'gm': 'g', 'gms': 'g', 'gram': 'g', 'grams': 'g',
    'ml': 'ml', 'l': 'l', 'ltr': 'l', 'ltrs': 'l', 'litre': 'l', 'litres': 'l',
    'liter': 'l', 'liters': 'l',
}
VEG_WORDS = {'शाकाहारी', 'मांसाहारी', 'veg', 'vegetarian', 'nonveg', 'non-veg'}


# ---------- small helpers ----------

def words(text):
    return re.findall(r'[a-z]+', text.lower())


def has_word(text, keyword, min_score=80):
    """True if the text has the keyword, allowing small OCR mistakes in long words."""
    for word in words(text):
        for candidate in (word, word.replace('rn', 'm')):
            if candidate == keyword:
                return True
            if len(keyword) >= 5 and similarity(candidate, keyword) >= min_score:
                return True
    return False


def fix_digits(text):
    """Fixes letters that OCR often confuses with digits, only next to digits."""
    for _ in range(3):
        text = re.sub(r'(?<=\d)[Oo]|[Oo](?=\d)', '0', text)
        text = re.sub(r'(?<=\d)[lI]|[lI](?=\d)', '1', text)
    return text


def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()


def to_float(text):
    number = float(text.replace(',', '.'))
    return int(number) if number.is_integer() else number


def box_center(box):
    return (box[0] + box[2]) / 2, (box[1] + box[3]) / 2


def inside(box, outer, margin=10):
    cx, cy = box_center(box)
    return (outer[0] - margin <= cx <= outer[2] + margin
            and outer[1] - margin <= cy <= outer[3] + margin)


def reading_order(lines):
    """Sorts OCR lines top to bottom, and left to right inside one row."""
    ordered = sorted(lines, key=lambda l: box_center(l['box'])[1])
    rows, current, current_cy = [], [], None
    for line in ordered:
        cy = box_center(line['box'])[1]
        height = max(line['box'][3] - line['box'][1], 1)
        if current and abs(cy - current_cy) <= 0.6 * height:
            current.append(line)
        else:
            if current:
                rows.append(current)
            current, current_cy = [line], cy
    if current:
        rows.append(current)
    result = []
    for row in rows:
        result.extend(sorted(row, key=lambda l: l['box'][0]))
    return result


def missing():
    return {'found': False, 'value': None, 'confidence': 0.0}


def found(value, confidence):
    return {'found': True, 'value': value, 'confidence': round(float(confidence), 2)}


def parse_lines(vision_result):
    lines = []
    for item in vision_result.get('ocr_lines', []):
        text = clean_text(str(item.get('text', '')))
        box = item.get('box')
        if text and box and len(box) == 4:
            lines.append({
                'text': text,
                'conf': float(item.get('confidence', 0.0)),
                'box': [float(v) for v in box],
                'lang': item.get('language', 'en'),
            })
    return reading_order(lines)


def boxes_of(vision_result, class_name):
    items = [d for d in vision_result.get('detections', [])
             if d.get('class') == class_name
             and float(d.get('confidence', 0)) >= MIN_DETECTION_CONF and d.get('box')]
    items.sort(key=lambda d: -float(d['confidence']))
    return [[float(v) for v in d['box']] for d in items]


def lines_in_boxes(lines, boxes):
    return [l for l in lines if any(inside(l['box'], b) for b in boxes)]


def is_header_line(text):
    """True for lines that start a different part of the label."""
    low = text.lower()
    return bool(
        has_word(text, 'nutrition') or has_word(text, 'ingredients') or has_word(text, 'allergen')
        or ADDRESS_RE.search(low) or MFG_RE.search(low) or EXP_RE.search(low)
        or re.match(r'^\s*(?:may\s+)?contains?\b', low)
        or has_word(text, 'fssai') or re.search(r'\blic(?:ence|ense)?\b', low)
        or re.search(r'\bnet\s*(?:wt|weight|qty|quantity|content)', low)
    )


def min_conf(lines):
    return min((l['conf'] for l in lines), default=0.0)


def strip_header(text, keyword):
    """Removes a heading such as 'INGREDIENTS:' from the start of the text."""
    match = re.match(r'^\s*([^:]{0,25}):\s*(.*)$', text, re.S)
    if match and has_word(match.group(1), keyword):
        return match.group(2).strip()
    first = re.match(r'^\s*([A-Za-z]+)\s*[-:]?\s*(.*)$', text, re.S)
    if first and has_word(first.group(1), keyword):
        return first.group(2).strip()
    return text.strip()


# ---------- individual fields ----------

def find_food_name(lines, vision_result):
    skip_boxes = []
    for name in ('ingredients', 'nutrition_table', 'allergen', 'fssai_no', 'fssai_logo'):
        skip_boxes.extend(boxes_of(vision_result, name))
    candidates = []
    for line in lines:
        text = line['text']
        low = text.lower()
        letters = sum(ch.isalpha() for ch in text)
        digits = sum(ch.isdigit() for ch in text)
        if letters < 3 or digits > 0.3 * len(text):
            continue
        if any(inside(line['box'], b) for b in skip_boxes):
            continue
        if low in VEG_WORDS or text in VEG_WORDS:
            continue
        if is_header_line(text) or QTY_RE.search(low):
            continue
        candidates.append(line)
    if not candidates:
        return missing()
    ys = [box_center(l['box'])[1] for l in lines]
    limit = min(ys) + 0.6 * (max(ys) - min(ys))
    top = [l for l in candidates if box_center(l['box'])[1] <= limit] or candidates
    best = max(top, key=lambda l: ((l['box'][3] - l['box'][1]), l['conf']))
    name = best['text']
    if name.isupper():
        name = name.title()
    return found(name, best['conf'])


def collect_after_header(lines, start_index, limit=12):
    """Takes the header line and the lines after it until another heading starts."""
    block = [lines[start_index]]
    for line in lines[start_index + 1:start_index + 1 + limit]:
        if is_header_line(line['text']):
            break
        block.append(line)
    return block


def ingredients_from(block):
    """Returns (text, confidence, has_heading) for a block of lines, or None."""
    if not block:
        return None
    raw = clean_text(' '.join(l['text'] for l in block))
    text = strip_header(raw, 'ingredients').rstrip(' .')
    if len(text) < 8:
        return None
    has_heading = has_word(raw, 'ingredients') or has_word(raw, 'ingredient', 85)
    return text, min_conf(block), has_heading


def find_ingredients(lines, vision_result):
    """Uses the YOLO box when it looks right, otherwise searches the OCR text."""
    boxed = ingredients_from(lines_in_boxes(lines, boxes_of(vision_result, 'ingredients')))
    if boxed and (boxed[2] or ',' in boxed[0]):
        return found(boxed[0], boxed[1])
    for i, line in enumerate(lines):
        if has_word(line['text'], 'ingredients') or has_word(line['text'], 'ingredient', 85):
            result = ingredients_from(collect_after_header(lines, i))
            if result:
                return found(result[0], result[1])
            break
    return missing()


def find_allergens(lines, vision_result):
    """Uses the YOLO box when it looks like an allergen statement, otherwise searches the OCR text."""
    block = lines_in_boxes(lines, boxes_of(vision_result, 'allergen'))
    if block:
        raw = clean_text(' '.join(l['text'] for l in block))
        low = raw.lower()
        looks_right = (has_word(raw, 'allergen') or has_word(raw, 'allergy') or has_word(raw, 'contains')
                       or any(re.search(r'\b' + w + r'\b', low) for w in ALLERGEN_WORDS))
        if looks_right:
            text = strip_header(raw, 'allergen') if has_word(raw, 'allergen') else raw
            text = strip_header(text, 'contains') if has_word(text, 'contains') else text
            text = text.strip(' .')
            if len(text) >= 3:
                return found(text, min_conf(block))
    for line in lines:
        low = line['text'].lower()
        statement = has_word(line['text'], 'allergen') or has_word(line['text'], 'allergy')
        mentions = re.search(r'\bcontains?\b', low) and any(
            re.search(r'\b' + w + r'\b', low) for w in ALLERGEN_WORDS)
        if statement or mentions:
            text = line['text']
            if ':' in text:
                text = text.split(':', 1)[1]
            text = text.strip(' .')
            if len(text) >= 3:
                return found(text, line['conf'])
    return missing()


def nutrient_key(text):
    """Which nutrient is this line about? Returns a key or None."""
    ws = words(text)
    if not ws:
        return None
    fuzzy = lambda kw: has_word(text, kw, 78)
    if 'added' in ws:
        return None
    if fuzzy('saturated') or 'sat' in ws:
        return 'saturated_fat_g'
    if 'trans' in ws or fuzzy('unsaturated') or 'mono' in ws or 'poly' in ws:
        return None
    if fuzzy('sodium'):
        return 'sodium_mg'
    if fuzzy('energy') or 'calories' in ws or 'calorie' in ws:
        return 'energy_kcal'
    if fuzzy('protein') or fuzzy('proteins'):
        return 'protein_g'
    if fuzzy('carbohydrate') or fuzzy('carbohydrates') or 'carbs' in ws:
        return 'carbohydrate_g'
    if fuzzy('sugars') or 'sugar' in ws:
        return 'total_sugars_g'
    if 'fat' in ws or 'fats' in ws:
        return 'total_fat_g'
    return None


def number_and_unit(text):
    text = fix_digits(text)
    match = re.search(r'(\d+(?:[.,]\d+)?)\s*(kcal|kj|mg|mcg|g)?', text.lower())
    if not match:
        return None
    return to_float(match.group(1)), (match.group(2) or '')


def parse_nutrition(block):
    """Reads nutrient values from a block of lines. Returns (values, used_lines) or None."""
    values, used = {}, []
    for i, line in enumerate(block):
        key = nutrient_key(line['text'])
        if key is None or key in values:
            continue
        text = fix_digits(line['text'])
        if key == 'energy_kcal':
            kcal = re.search(r'(\d+(?:[.,]\d+)?)\s*kcal', text.lower())
            kj = re.search(r'(\d+(?:[.,]\d+)?)\s*kj', text.lower())
            if kcal:
                values[key] = to_float(kcal.group(1))
                used.append(line)
                continue
            if kj:
                values[key] = round(to_float(kj.group(1)) / 4.184)
                used.append(line)
                continue
        parsed = number_and_unit(text)
        source = line
        if parsed is None and i + 1 < len(block) and nutrient_key(block[i + 1]['text']) is None:
            parsed = number_and_unit(block[i + 1]['text'])
            source = block[i + 1]
        if parsed is None:
            continue
        number, unit = parsed
        if key == 'sodium_mg' and unit == 'g':
            number = round(number * 1000, 2)
        if key == 'energy_kcal' and unit == 'kj':
            number = round(number / 4.184)
        values[key] = int(number) if float(number).is_integer() else number
        used.append(line)
        if source is not line:
            used.append(source)
    if not values:
        return None
    return {k: values[k] for k in NUTRIENT_KEYS if k in values}, used


def find_nutrition(lines, vision_result):
    """Reads the YOLO box and also the text after a 'Nutrition' heading, and keeps the fuller result."""
    options = []
    box_block = lines_in_boxes(lines, boxes_of(vision_result, 'nutrition_table'))
    if box_block:
        parsed = parse_nutrition(box_block)
        if parsed:
            options.append(parsed)
    for i, line in enumerate(lines):
        if has_word(line['text'], 'nutrition') or has_word(line['text'], 'nutritional'):
            parsed = parse_nutrition(collect_after_header(lines, i, limit=14))
            if parsed:
                options.append(parsed)
            break
    if not options:
        return missing()
    values, used = max(options, key=lambda option: len(option[0]))
    return found(values, min_conf(used))


def format_quantity(number, unit):
    if float(number).is_integer():
        number = int(number)
    return f'{number} {UNIT_MAP[unit]}'


def find_net_quantity(lines, vision_result):
    table = boxes_of(vision_result, 'nutrition_table')
    pool = [l for l in lines
            if not any(inside(l['box'], b) for b in table) and nutrient_key(l['text']) is None]
    markers = re.compile(r'\b(?:net|wt|weight|qty|quantity|contents?)\b')
    for line in pool:
        low = fix_digits(line['text']).lower()
        if markers.search(low):
            match = QTY_RE.search(low)
            if match:
                return found(format_quantity(to_float(match.group(1)), match.group(2)), line['conf'])
    for line in pool:
        low = fix_digits(line['text']).lower().replace('℮', '').strip()
        match = QTY_RE.fullmatch(low)
        if match:
            return found(format_quantity(to_float(match.group(1)), match.group(2)), line['conf'])
    return missing()


def make_date(day, month, year, mode):
    if year < 100:
        year += 2000
    if not (2000 <= year <= 2100 and 1 <= month <= 12):
        return None
    last = calendar.monthrange(year, month)[1]
    if day is None:
        day = last if mode == 'exp' else 1
    if not 1 <= day <= last:
        return None
    return date(year, month, day)


def parse_date(text, mode):
    """Finds the first date in the text. mode is 'mfg' or 'exp'."""
    text = fix_digits(text).lower()
    match = NUM_DATE_RE.search(text)
    if match:
        return make_date(int(match.group(1)), int(match.group(2)), int(match.group(3)), mode)
    match = TEXT_DATE_RE.search(text)
    if match:
        day = int(match.group(1)) if match.group(1) else None
        return make_date(day, MONTHS[match.group(2)], int(match.group(3)), mode)
    match = MONTH_YEAR_RE.search(text)
    if match:
        return make_date(None, int(match.group(1)), int(match.group(2)), mode)
    return None


def add_months(start, months):
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def segments(low, regex_a, regex_b):
    """Splits a line so each date keyword gets the text up to the next keyword."""
    marks = [(m.start(), m.end(), 'a') for m in regex_a.finditer(low)]
    marks += [(m.start(), m.end(), 'b') for m in regex_b.finditer(low)]
    marks.sort()
    result = []
    for i, (start, end, kind) in enumerate(marks):
        stop = marks[i + 1][0] if i + 1 < len(marks) else len(low)
        result.append((kind, low[end:stop]))
    return result


def find_dates(lines):
    mfg, exp = None, None
    relative = None
    for i, line in enumerate(lines):
        low = fix_digits(line['text']).lower()
        # Skip "Manufactured by ..." address lines.
        if ADDRESS_RE.search(low) and not re.search(r'manufactur\w*\s*(?:date|on)', low):
            continue
        rel = RELATIVE_RE.search(low)
        if rel and EXP_RE.search(low):
            relative = (int(rel.group(1)), rel.group(2), line['conf'])
            continue
        parts = segments(low, MFG_RE, EXP_RE)
        for kind, tail in parts:
            mode = 'mfg' if kind == 'a' else 'exp'
            parsed = parse_date(tail, mode)
            confidence = line['conf']
            if parsed is None and i + 1 < len(lines):
                nxt = lines[i + 1]
                if not is_header_line(nxt['text']):
                    parsed = parse_date(nxt['text'], mode)
                    confidence = min(confidence, nxt['conf'])
            if parsed is None:
                continue
            if mode == 'mfg' and mfg is None:
                mfg = (parsed, confidence)
            if mode == 'exp' and exp is None:
                exp = (parsed, confidence)
    mfg_field = found(mfg[0].isoformat(), mfg[1]) if mfg else missing()
    if exp:
        exp_field = found(exp[0].isoformat(), exp[1])
    elif relative:
        number, unit, confidence = relative
        text_value = f'{number} {unit}{"s" if number != 1 else ""} from manufacture'
        if mfg:
            if unit == 'month':
                value = add_months(mfg[0], number)
            elif unit == 'year':
                value = add_months(mfg[0], 12 * number)
            elif unit == 'week':
                value = mfg[0] + timedelta(weeks=number)
            else:
                value = mfg[0] + timedelta(days=number)
            exp_field = found(value.isoformat(), min(confidence, mfg[1]))
        else:
            exp_field = found(text_value, confidence)
    else:
        exp_field = missing()
    return mfg_field, exp_field


def find_fssai_number(lines, vision_result):
    pool = lines_in_boxes(lines, boxes_of(vision_result, 'fssai_no'))
    for line in lines:
        low = line['text'].lower()
        if line in pool:
            continue
        if has_word(line['text'], 'fssai') or re.search(r'\blic(?:ence|ense)?\b', low):
            pool.append(line)
    best = None
    for line in pool:
        text = fix_digits(line['text'])
        for match in re.finditer(r'\d[\d \-]{6,22}\d', text):
            digits = re.sub(r'\D', '', match.group(0))
            if len(digits) == 14:
                return found(digits, line['conf'])
            if len(digits) >= 8 and (best is None or len(digits) > len(best[0])):
                best = (digits, line['conf'])
    if best:
        return found(best[0], best[1])
    for line in lines:
        match = re.search(r'(?<!\d)\d{14}(?!\d)', fix_digits(line['text']))
        if match:
            return found(match.group(0), line['conf'])
    return missing()


def find_address(lines, vision_result):
    blocked = []
    for name in ('ingredients', 'nutrition_table'):
        blocked.extend(boxes_of(vision_result, name))
    for i, line in enumerate(lines):
        low = line['text'].lower()
        match = ADDRESS_RE.search(low)
        if not match or re.search(r'manufactur\w*\s*(?:date|on)\b', low):
            continue
        if any(inside(line['box'], b) for b in blocked):
            continue
        block = [line]
        previous = line
        for nxt in lines[i + 1:i + 4]:
            gap = nxt['box'][1] - previous['box'][3]
            height = max(previous['box'][3] - previous['box'][1], 1)
            if gap > 0.8 * height or is_header_line(nxt['text']):
                break
            block.append(nxt)
            previous = nxt
        text = clean_text(' '.join(l['text'] for l in block))
        cut = re.search(r'(?:by|:)\s*(.*)$', text, re.I)
        value = cut.group(1).strip() if cut else text
        value = value.strip(' ,.:-')
        if len(value) >= 10:
            return found(value, min_conf(block))
    return missing()


def find_veg_mark(lines, vision_result):
    best = None
    for class_name, value in (('veg_symbol', 'veg'), ('nonveg_symbol', 'nonveg')):
        for d in vision_result.get('detections', []):
            conf = float(d.get('confidence', 0))
            if d.get('class') == class_name and conf >= MIN_DETECTION_CONF:
                if best is None or conf > best[1]:
                    best = (value, conf)
    if best:
        return found(best[0], best[1])
    for line in lines:
        low = line['text'].lower()
        if 'मांसाहारी' in line['text'] or re.search(r'\bnon[\s\-]?veg(?:etarian)?\b', low):
            return found('nonveg', min(line['conf'], 0.6))
    for line in lines:
        low = line['text'].lower()
        if 'शाकाहारी' in line['text'] or re.search(r'\bveg(?:etarian)?\b', low):
            return found('veg', min(line['conf'], 0.6))
    return missing()


# ---------- main entry ----------

def extract_fields(vision_result):
    """VISION RESULT in, EXTRACTED FIELDS out."""
    lines = parse_lines(vision_result)
    mfg, exp = find_dates(lines)
    return {
        'food_name': find_food_name(lines, vision_result),
        'ingredients': find_ingredients(lines, vision_result),
        'nutrition': find_nutrition(lines, vision_result),
        'allergens': find_allergens(lines, vision_result),
        'net_quantity': find_net_quantity(lines, vision_result),
        'manufacturing_date': mfg,
        'expiry_date': exp,
        'fssai_licence_number': find_fssai_number(lines, vision_result),
        'manufacturer_address': find_address(lines, vision_result),
        'veg_nonveg_mark': find_veg_mark(lines, vision_result),
    }
