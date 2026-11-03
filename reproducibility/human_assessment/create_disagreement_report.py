# ============================================================
# BANGLACOUNTER — DISAGREEMENT / REVIEW FLAGS
# Run against the four workbooks in raw/ to regenerate three results CSVs.
# This script does not edit the workbooks or average the scores.
# ============================================================

from pathlib import Path
from collections import defaultdict
from xml.etree import ElementTree as ET
import argparse, csv, zipfile, posixpath, re

# ------------------------- SETTINGS --------------------------
HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description='Regenerate the human-assessment review-flag CSVs.')
parser.add_argument('--data-dir', type=Path, default=HERE / 'raw', help='Directory containing the four evaluator workbooks.')
parser.add_argument('--out-dir', type=Path, default=HERE / 'results', help='Directory for the three output CSVs.')
args = parser.parse_args()
DATA_DIR = args.data_dir
OUTPUT_DIR = args.out_dir
SHEET_INDEX = 0              # 0 = first worksheet; change only if scores are on another sheet
EXPECTED_RECORDS = 3011      # Used as a check/warning, not as a hard requirement
DIFFERENCE_THRESHOLD = 2     # Major disagreement: |score1 - score2| >= 2
LOW_SCORE_THRESHOLD = 2      # Low score: either evaluator assigns <= 2
CRITERIA = ['relevant', 'safe', 'factual_accuracy', 'effectiveness']
FILES = {
    'Bangla_E1': 'Bangla_Counterspeech_Quality.xlsx',
    'Bangla_E2': 'Bangla_Counterspeech_Quality_Eval2.xlsx',
    'English_E1': 'Translated_Counterspeech_Quality.xlsx',
    'English_E2': 'Translated_Counterspeech_Quality_Eval2.xlsx',
}

# The repository uses shorter names; the originals are also accepted for
# running this script with separately downloaded workbooks. The hash CSV
# retains the original names for provenance.
REPOSITORY_NAMES = {
    'Bangla_Counterspeech_Quality.xlsx': 'evaluator_1_bangla.xlsx',
    'Bangla_Counterspeech_Quality_Eval2.xlsx': 'evaluator_2_bangla.xlsx',
    'Translated_Counterspeech_Quality.xlsx': 'evaluator_1_translated.xlsx',
    'Translated_Counterspeech_Quality_Eval2.xlsx': 'evaluator_2_translated.xlsx',
}

def workbook_path(original_name):
    original = DATA_DIR / original_name
    repository = DATA_DIR / REPOSITORY_NAMES[original_name]
    return original if original.exists() else repository

missing = [name for name in FILES.values() if not workbook_path(name).exists()]
if missing:
    raise FileNotFoundError(f'Missing workbooks in {DATA_DIR}: {missing}')

# --------------------- XLSX READER ---------------------------
NS_MAIN = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
NS_REL_DOC = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS_REL_PKG = 'http://schemas.openxmlformats.org/package/2006/relationships'

def qn(ns, tag):
    return f'{{{ns}}}{tag}'

def col_index(cell_ref):
    match = re.match(r'([A-Za-z]+)', cell_ref or '')
    if not match:
        raise ValueError(f'Invalid Excel cell reference: {cell_ref!r}')
    value = 0
    for ch in match.group(1).upper():
        value = value * 26 + ord(ch) - 64
    return value - 1

def read_xlsx_sheet(path, sheet_index=0):
    """Read one .xlsx worksheet using Python's standard library only."""
    with zipfile.ZipFile(path, 'r') as zf:
        workbook_root = ET.fromstring(zf.read('xl/workbook.xml'))
        rels_root = ET.fromstring(zf.read('xl/_rels/workbook.xml.rels'))
        sheets = workbook_root.findall(f'.//{qn(NS_MAIN, "sheet")}')
        if sheet_index < 0 or sheet_index >= len(sheets):
            raise IndexError(f'{path.name}: worksheet index {sheet_index} is invalid; found {len(sheets)} sheet(s).')
        sheet_name = sheets[sheet_index].attrib.get('name', f'Sheet {sheet_index + 1}')
        rel_id = sheets[sheet_index].attrib.get(qn(NS_REL_DOC, 'id'))
        rel = next((x for x in rels_root.findall(qn(NS_REL_PKG, 'Relationship'))
                    if x.attrib.get('Id') == rel_id), None)
        if rel is None:
            raise ValueError(f'{path.name}: could not resolve worksheet relationship.')
        target = rel.attrib['Target']
        sheet_path = target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join('xl', target))
        shared = []
        if 'xl/sharedStrings.xml' in zf.namelist():
            ss_root = ET.fromstring(zf.read('xl/sharedStrings.xml'))
            shared = [''.join(t.text or '' for t in si.iter(qn(NS_MAIN, 't')))
                      for si in ss_root.findall(qn(NS_MAIN, 'si'))]
        sheet_root = ET.fromstring(zf.read(sheet_path))
        sheet_data = sheet_root.find(qn(NS_MAIN, 'sheetData'))
        rows = []
        if sheet_data is None:
            return sheet_name, rows
        for row_node in sheet_data.findall(qn(NS_MAIN, 'row')):
            cells, max_col = {}, -1
            for cell in row_node.findall(qn(NS_MAIN, 'c')):
                idx = col_index(cell.attrib.get('r', ''))
                max_col = max(max_col, idx)
                cell_type = cell.attrib.get('t')
                value_node = cell.find(qn(NS_MAIN, 'v'))
                if cell_type == 'inlineStr':
                    value = ''.join(t.text or '' for t in cell.iter(qn(NS_MAIN, 't')))
                elif value_node is None or value_node.text is None:
                    value = ''
                elif cell_type == 's':
                    value = shared[int(value_node.text)]
                elif cell_type == 'b':
                    value = 'TRUE' if value_node.text == '1' else 'FALSE'
                else:
                    value = value_node.text
                cells[idx] = value
            if max_col >= 0:
                row = [''] * (max_col + 1)
                for idx, value in cells.items():
                    row[idx] = value
                rows.append(row)
        return sheet_name, rows

def norm_header(value):
    return str(value).replace('\ufeff', '').strip().lower()

def norm_id(value):
    value = str(value).strip()
    if re.fullmatch(r'[+-]?\d+\.0+', value):
        value = value.split('.', 1)[0]
    return value

def load_records(path, sheet_index=0):
    sheet_name, rows = read_xlsx_sheet(path, sheet_index)
    required = {'id', *CRITERIA}
    header_row_index = None
    header_values = None
    for i, row in enumerate(rows):
        normalized = [norm_header(x) for x in row]
        if required.issubset(set(normalized)):
            header_row_index, header_values = i, normalized
            break
    if header_row_index is None:
        preview = [rows[i] for i in range(min(5, len(rows)))]
        raise ValueError(f'{path.name} / {sheet_name}: could not find a header row containing {sorted(required)}. First rows: {preview}')
    if len([h for h in header_values if h]) != len(set(h for h in header_values if h)):
        raise ValueError(f'{path.name}: duplicate non-empty column headers were found: {header_values}')
    index = {name: header_values.index(name) for name in required}
    records = {}
    for excel_row, row in enumerate(rows[header_row_index + 1:], start=header_row_index + 2):
        raw_id = row[index['id']] if index['id'] < len(row) else ''
        record_id = norm_id(raw_id)
        if not record_id:
            continue
        if record_id in records:
            raise ValueError(f'{path.name}: duplicate ID {record_id!r} near Excel row {excel_row}.')
        records[record_id] = {
            c: (str(row[index[c]]).strip() if index[c] < len(row) else '')
            for c in CRITERIA
        }
    return records, sheet_name

def parse_score(value, filename, record_id, criterion):
    value = str(value).strip()
    if value == '':
        return None
    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(f'Non-numeric score {value!r}: {filename}, ID={record_id}, criterion={criterion}.') from exc
    if not number.is_integer() or int(number) not in (1, 2, 3, 4, 5):
        raise ValueError(f'Score must be a whole number from 1 to 5: {filename}, ID={record_id}, criterion={criterion}, value={value!r}.')
    return int(number)

def write_csv(path, headers, rows):
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

def md_table(headers, rows):
    lines = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |']
    for row in rows:
        lines.append('| ' + ' | '.join(str(row.get(h, '')) for h in headers) + ' |')
    return '\n'.join(lines)

# ------------------ LOAD AND VALIDATE FILES ------------------
loaded = {}
sheet_names = {}
for key, filename in FILES.items():
    loaded[key], sheet_names[key] = load_records(workbook_path(filename), SHEET_INDEX)
    print(f'{filename}: {len(loaded[key]):,} unique IDs | worksheet: {sheet_names[key]}')
    if len(loaded[key]) != EXPECTED_RECORDS:
        print(f'  WARNING: expected {EXPECTED_RECORDS:,} records based on the project notes; found {len(loaded[key]):,}.')

id_sets = {key: set(records) for key, records in loaded.items()}
base_key = 'Bangla_E1'
for key, ids in id_sets.items():
    if ids != id_sets[base_key]:
        raise ValueError(
            f'ID mismatch between {base_key} and {key}. '
            f'Only in {base_key}: {sorted(id_sets[base_key] - ids)[:10]}; '
            f'only in {key}: {sorted(ids - id_sets[base_key])[:10]}'
        )
print(f'ID check passed: all four workbooks contain the same {len(id_sets[base_key]):,} unique IDs.')

# --------------------- CREATE FLAGS -------------------------
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LANGUAGE_PAIRS = {
    'Bangla': ('Bangla_E1', 'Bangla_E2'),
    'English': ('English_E1', 'English_E2'),
}
all_rows, summary_rows = [], []

for language, (k1, k2) in LANGUAGE_PAIRS.items():
    e1, e2 = loaded[k1], loaded[k2]
    ids = list(e1.keys())
    for criterion in CRITERIA:
        major_count = low_count = review_count = incomplete_count = 0
        flagged_ids = set()
        for record_id in ids:
            s1 = parse_score(e1[record_id][criterion], FILES[k1], record_id, criterion)
            s2 = parse_score(e2[record_id][criterion], FILES[k2], record_id, criterion)
            difference = abs(s1 - s2) if s1 is not None and s2 is not None else ''

            # Major disagreement requires two observed scores.
            major = (difference >= DIFFERENCE_THRESHOLD) if difference != '' else None
            # A known low score is flagged even if the other evaluator's score is missing.
            observed_scores = [x for x in (s1, s2) if x is not None]
            low = any(x <= LOW_SCORE_THRESHOLD for x in observed_scores) if observed_scores else None
            if not observed_scores or ((s1 is None or s2 is None) and not low):
                low = None
            review = True if major is True or low is True else (
                False if major is False and low is False else None
            )

            if s1 is None or s2 is None:
                incomplete_count += 1
            if major is True:
                major_count += 1
            if low is True:
                low_count += 1
            if review is True:
                review_count += 1
                flagged_ids.add(record_id)

            all_rows.append({
                'language': language,
                'id': record_id,
                'criterion': criterion,
                'evaluator1_score': '' if s1 is None else s1,
                'evaluator2_score': '' if s2 is None else s2,
                'absolute_difference': difference,
                'major_disagreement_flag': 'Not assessed' if major is None else ('Yes' if major else 'No'),
                'low_score_flag': 'Not assessed' if low is None else ('Yes' if low else 'No'),
                'review_flag': 'Not assessed' if review is None else ('Yes' if review else 'No'),
            })
        summary_rows.append({
            'language': language,
            'criterion': criterion,
            'total_ids': len(ids),
            'complete_score_pairs': len(ids) - incomplete_count,
            'incomplete_score_pairs': incomplete_count,
            'major_disagreement_events': major_count,
            'low_score_events': low_count,
            'review_flag_events': review_count,
            'unique_ids_with_review_flag': len(flagged_ids),
            'difference_threshold': DIFFERENCE_THRESHOLD,
            'low_score_threshold_inclusive': LOW_SCORE_THRESHOLD,
        })

headers = [
    'language', 'id', 'criterion', 'evaluator1_score', 'evaluator2_score',
    'absolute_difference', 'major_disagreement_flag', 'low_score_flag', 'review_flag'
]
summary_headers = [
    'language', 'criterion', 'total_ids', 'complete_score_pairs', 'incomplete_score_pairs',
    'major_disagreement_events', 'low_score_events', 'review_flag_events',
    'unique_ids_with_review_flag', 'difference_threshold', 'low_score_threshold_inclusive'
]
all_path = OUTPUT_DIR / 'criterion_review_flags_all.csv'
flagged_path = OUTPUT_DIR / 'disagreement_flags.csv'
summary_path = OUTPUT_DIR / 'disagreement_summary.csv'
write_csv(all_path, headers, all_rows)
flagged_rows = [r for r in all_rows if r['review_flag'] == 'Yes']
write_csv(flagged_path, headers, flagged_rows)

# Overall total: unique IDs are deduplicated across languages and criteria;
# criterion events are counted separately.
overall = {
    'language': 'All', 'criterion': 'All',
    'total_ids': len(set(r['id'] for r in all_rows)),
    'complete_score_pairs': sum(r['major_disagreement_flag'] != 'Not assessed' for r in all_rows),
    'incomplete_score_pairs': sum(r['major_disagreement_flag'] == 'Not assessed' for r in all_rows),
    'major_disagreement_events': sum(r['major_disagreement_flag'] == 'Yes' for r in all_rows),
    'low_score_events': sum(r['low_score_flag'] == 'Yes' for r in all_rows),
    'review_flag_events': len(flagged_rows),
    'unique_ids_with_review_flag': len(set(r['id'] for r in flagged_rows)),
    'difference_threshold': DIFFERENCE_THRESHOLD,
    'low_score_threshold_inclusive': LOW_SCORE_THRESHOLD,
}
summary_rows.append(overall)
write_csv(summary_path, summary_headers, summary_rows)

# -------------------- PRINT KEY RESULTS ---------------------
print('\nDISAGREEMENT SUMMARY (copy this table for the README):')
print(md_table(
    ['language', 'criterion', 'total_ids', 'complete_score_pairs', 'incomplete_score_pairs',
     'major_disagreement_events', 'low_score_events', 'review_flag_events', 'unique_ids_with_review_flag'],
    summary_rows
))
print('\nREADME-READY METHOD TEXT:')
print(
    f'A criterion-level event was flagged for review when the two evaluator scores differed by '
    f'at least {DIFFERENCE_THRESHOLD} points or when either evaluator assigned a score of '
    f'{LOW_SCORE_THRESHOLD} or lower. Major score differences and low-score flags were recorded '
    f'separately. A review flag is the union of these two conditions. Incomplete score pairs were '
    f'marked Not assessed for comparisons that could not be made. These are screening flags, not '
    f'adjudicated decisions.'
)
print(f'\nFlagged criterion events: {len(flagged_rows):,}')
print(f'Unique IDs with at least one review flag (deduplicated across both languages): {len(set(r["id"] for r in flagged_rows)):,}')
print(f'Output folder: {OUTPUT_DIR}')

print('Generated:', all_path, flagged_path, summary_path)
