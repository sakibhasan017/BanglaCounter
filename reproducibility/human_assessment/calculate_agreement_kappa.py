# ============================================================
# BANGLACOUNTER — COLAB CELL 2: EXACT AGREEMENT + WEIGHTED KAPPA
# Run Cell 1 first. This cell re-reads the same four uploaded XLSX files.
# It uses original paired scores; no average/final score is required.
# ============================================================

from pathlib import Path
from xml.etree import ElementTree as ET
import csv, zipfile, posixpath, re, math, hashlib

# ------------------------- SETTINGS --------------------------
DATA_DIR = Path('/content')
OUTPUT_DIR = DATA_DIR / 'banglacounter_audit_outputs'
SHEET_INDEX = 0              # Keep the same worksheet index as Cell 1
EXPECTED_RECORDS = 3011
SCORES = [1, 2, 3, 4, 5]
CRITERIA = ['relevant', 'safe', 'factual_accuracy', 'effectiveness']
FILES = {
    'Bangla_E1': 'Bangla_Counterspeech_Quality.xlsx',
    'Bangla_E2': 'Bangla_Counterspeech_Quality_Eval2.xlsx',
    'English_E1': 'Translated_Counterspeech_Quality.xlsx',
    'English_E2': 'Translated_Counterspeech_Quality_Eval2.xlsx',
}

try:
    from google.colab import files as colab_files
    IN_COLAB = True
except ImportError:
    colab_files = None
    IN_COLAB = False

missing = [name for name in FILES.values() if not (DATA_DIR / name).exists()]
if missing:
    if not IN_COLAB:
        raise FileNotFoundError('Run Colab Cell 1 first, or place all four workbooks in /content. Missing: ' + ', '.join(missing))
    print('The four workbooks are not all present. Please upload them again.')
    uploaded = colab_files.upload()
    missing = [name for name in FILES.values() if not (DATA_DIR / name).exists()]
    if missing:
        raise FileNotFoundError('Still missing exact filenames: ' + ', '.join(missing))

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
    if not number.is_integer() or int(number) not in SCORES:
        raise ValueError(f'Score must be a whole number from 1 to 5: {filename}, ID={record_id}, criterion={criterion}, value={value!r}.')
    return int(number)

def linear_weighted_kappa(pairs):
    """Linear-weighted Cohen's kappa for ordinal categories 1–5."""
    n = len(pairs)
    if not n:
        return None, None, None
    matrix = [[0 for _ in SCORES] for _ in SCORES]
    for s1, s2 in pairs:
        matrix[s1 - 1][s2 - 1] += 1
    row_totals = [sum(row) for row in matrix]
    col_totals = [sum(matrix[i][j] for i in range(5)) for j in range(5)]
    def weight(i, j):
        return 1.0 - abs(i - j) / 4.0
    observed = sum(matrix[i-1][j-1] * weight(i, j) for i in SCORES for j in SCORES) / n
    expected = sum(row_totals[i-1] * col_totals[j-1] * weight(i, j)
                   for i in SCORES for j in SCORES) / (n * n)
    if math.isclose(1.0 - expected, 0.0, abs_tol=1e-15):
        return None, observed, expected
    return (observed - expected) / (1.0 - expected), observed, expected

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
for key, filename in FILES.items():
    loaded[key], sheet_name = load_records(DATA_DIR / filename, SHEET_INDEX)
    print(f'{filename}: {len(loaded[key]):,} unique IDs | worksheet: {sheet_name}')
    if len(loaded[key]) != EXPECTED_RECORDS:
        print(f'  WARNING: expected {EXPECTED_RECORDS:,} records based on project notes; found {len(loaded[key]):,}.')
base_ids = set(loaded['Bangla_E1'])
for key, records in loaded.items():
    if set(records) != base_ids:
        raise ValueError(f'ID mismatch between Bangla_E1 and {key}. Check workbook IDs before calculating agreement.')
print(f'ID check passed: all four workbooks contain the same {len(base_ids):,} unique IDs.')

# -------------------- CALCULATE METRICS ----------------------
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LANGUAGE_PAIRS = {
    'Bangla': ('Bangla_E1', 'Bangla_E2'),
    'English': ('English_E1', 'English_E2'),
}
summary_rows, matrix_rows, distribution_rows = [], [], []

for language, (k1, k2) in LANGUAGE_PAIRS.items():
    e1, e2 = loaded[k1], loaded[k2]
    ids = list(e1.keys())
    for criterion in CRITERIA:
        pairs = []
        incomplete = 0
        e1_dist = {s: 0 for s in SCORES}
        e2_dist = {s: 0 for s in SCORES}
        for record_id in ids:
            s1 = parse_score(e1[record_id][criterion], FILES[k1], record_id, criterion)
            s2 = parse_score(e2[record_id][criterion], FILES[k2], record_id, criterion)
            if s1 is not None:
                e1_dist[s1] += 1
            if s2 is not None:
                e2_dist[s2] += 1
            if s1 is None or s2 is None:
                incomplete += 1
            else:
                pairs.append((s1, s2))
        n = len(pairs)
        exact_n = sum(s1 == s2 for s1, s2 in pairs)
        exact_pct = exact_n / n * 100 if n else None
        kappa, observed_w, expected_w = linear_weighted_kappa(pairs)
        mean_abs_diff = sum(abs(s1-s2) for s1, s2 in pairs) / n if n else None
        summary_rows.append({
            'language': language,
            'criterion': criterion,
            'total_ids': len(ids),
            'valid_paired_ratings': n,
            'incomplete_paired_ratings': incomplete,
            'exact_agreements': exact_n,
            'exact_agreement_percent': '' if exact_pct is None else round(exact_pct, 4),
            'linear_weighted_cohens_kappa': '' if kappa is None else round(kappa, 6),
            'observed_weighted_agreement': '' if observed_w is None else round(observed_w, 6),
            'expected_weighted_agreement': '' if expected_w is None else round(expected_w, 6),
            'mean_absolute_score_difference': '' if mean_abs_diff is None else round(mean_abs_diff, 6),
        })
        # Long-form 5x5 table: all cells included, including zero counts.
        counts = [[0 for _ in SCORES] for _ in SCORES]
        for s1, s2 in pairs:
            counts[s1-1][s2-1] += 1
        for s1 in SCORES:
            for s2 in SCORES:
                matrix_rows.append({
                    'language': language, 'criterion': criterion,
                    'evaluator1_score': s1, 'evaluator2_score': s2,
                    'count': counts[s1-1][s2-1]
                })
        distribution_rows.append({
            'language': language, 'criterion': criterion,
            'evaluator1_nonmissing_n': sum(e1_dist.values()),
            **{f'evaluator1_score_{s}': e1_dist[s] for s in SCORES},
            'evaluator2_nonmissing_n': sum(e2_dist.values()),
            **{f'evaluator2_score_{s}': e2_dist[s] for s in SCORES},
        })

summary_headers = [
    'language', 'criterion', 'total_ids', 'valid_paired_ratings', 'incomplete_paired_ratings',
    'exact_agreements', 'exact_agreement_percent', 'linear_weighted_cohens_kappa',
    'observed_weighted_agreement', 'expected_weighted_agreement', 'mean_absolute_score_difference'
]
matrix_headers = ['language', 'criterion', 'evaluator1_score', 'evaluator2_score', 'count']
dist_headers = ['language', 'criterion', 'evaluator1_nonmissing_n'] + [f'evaluator1_score_{s}' for s in SCORES] + ['evaluator2_nonmissing_n'] + [f'evaluator2_score_{s}' for s in SCORES]
summary_path = OUTPUT_DIR / 'agreement_summary.csv'
matrix_path = OUTPUT_DIR / 'agreement_confusion_matrices.csv'
dist_path = OUTPUT_DIR / 'score_distributions.csv'
write_csv(summary_path, summary_headers, summary_rows)
write_csv(matrix_path, matrix_headers, matrix_rows)
write_csv(dist_path, dist_headers, distribution_rows)

# SHA-256 hashes make it possible to identify exactly which workbooks were audited.
hash_rows = []
for key, filename in FILES.items():
    digest = hashlib.sha256((DATA_DIR / filename).read_bytes()).hexdigest()
    hash_rows.append({'workbook_role': key, 'filename': filename, 'sha256': digest})
hash_path = OUTPUT_DIR / 'source_workbook_hashes.csv'
write_csv(hash_path, ['workbook_role', 'filename', 'sha256'], hash_rows)

# -------------------- PRINT README RESULTS -------------------
print('\nAGREEMENT SUMMARY (copy this table for the README):')
print(md_table(
    ['language', 'criterion', 'valid_paired_ratings', 'incomplete_paired_ratings',
     'exact_agreements', 'exact_agreement_percent', 'linear_weighted_cohens_kappa'],
    summary_rows
))

exact_values = [float(r['exact_agreement_percent']) for r in summary_rows if r['exact_agreement_percent'] != '']
kappa_values = [float(r['linear_weighted_cohens_kappa']) for r in summary_rows if r['linear_weighted_cohens_kappa'] != '']
if exact_values:
    print(f'\nExact agreement range across {len(exact_values)} comparisons: {min(exact_values):.2f}% to {max(exact_values):.2f}%.')
if kappa_values:
    print(f'Linear-weighted Cohen\'s kappa range across {len(kappa_values)} defined comparisons: {min(kappa_values):.3f} to {max(kappa_values):.3f}.')
undefined_kappa = sum(r['linear_weighted_cohens_kappa'] == '' for r in summary_rows)
if undefined_kappa:
    print(f'Undefined kappa values: {undefined_kappa} comparison(s); inspect score distributions/confusion matrices.')

print('\nSCORE DISTRIBUTIONS (copy or use to describe score concentration):')
print(md_table(dist_headers, distribution_rows))
print('\nSOURCE WORKBOOK SHA-256 HASHES:')
print(md_table(['workbook_role', 'filename', 'sha256'], hash_rows))
print('\nREAD-ME INTERPRETATION NOTE:')
print(
    'Exact agreement is the percentage of complete paired ratings with identical scores. '
    'Linear-weighted Cohen\'s kappa uses weights 1 - |score1 - score2| / 4 for the 1–5 ordinal scale. '
    'Metrics are calculated separately for each language and criterion from the original paired scores; '
    'no averaged or final score is required. Incomplete pairs are excluded from that criterion\'s metrics '
    'and reported separately.'
)
print(f'\nOutput folder: {OUTPUT_DIR}')

zip_path = OUTPUT_DIR / 'banglacounter_agreement_outputs.zip'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for path in (summary_path, matrix_path, dist_path, hash_path):
        zf.write(path, arcname=path.name)
print(f'Download bundle: {zip_path}')
if IN_COLAB:
    colab_files.download(str(zip_path))
