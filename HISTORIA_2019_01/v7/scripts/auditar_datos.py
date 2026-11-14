"""Read-only real-data gate. Does not load October labels or fit models."""
import argparse
import hashlib
import json
from pathlib import Path
import polars as pl

META = {'numero_de_cliente', 'foto_mes', 'clase_ternaria'}
OCTOBER = ['mrentabilidad', 'mrentabilidad_annual', 'mpasivos_margen',
 'mactivos_margen', 'mcomisiones', 'mcomisiones_otras', 'ccomisiones_otras',
 'chomebanking_transacciones', 'mcajeros_propios_descuentos',
 'ccajeros_propios_descuentos', 'ctarjeta_visa_descuentos',
 'mtarjeta_visa_descuentos', 'ctarjeta_master_descuentos',
 'mtarjeta_master_descuentos']
JULY = ['Visa_fultimo_cierre', 'Master_fultimo_cierre']

def summarize(df, raw):
    rows = []
    for month in sorted(df['foto_mes'].unique().to_list()):
        part = df.filter(pl.col('foto_mes') == month)
        for name in raw:
            s = part[name].cast(pl.Float64, strict=True)
            finite = s.filter(s.is_finite())
            rows.append({'month': month, 'variable': name, 'rows': len(s),
                'nulls': s.null_count(), 'zeros': int((s == 0).sum()),
                'nonfinite': int((s.is_not_null() & ~s.is_finite()).sum()),
                'distinct_finite': finite.n_unique(),
                'minimum': finite.min(), 'maximum': finite.max()})
    return rows

def assess(rows):
    by = {(r['month'], r['variable']): r for r in rows}
    findings = []
    for month, names in [(201907, JULY), (201910, OCTOBER)]:
        for name in names:
            r = by[(month, name)]
            before = by[(month - 1, name)]
            findings.append({'month': month, 'variable': name,
                'zero_fraction': r['zeros'] / r['rows'],
                'previous_zero_fraction': before['zeros'] / before['rows'],
                'previous_distinct_finite': before['distinct_finite'],
                'all_zero_with_previous_variation': r['zeros'] == r['rows'] and before['distinct_finite'] > 1,
                'requires_semantic_review': True})
    return findings

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', type=Path, required=True)
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError('Audit output must be new')
    cfg = json.loads(a.config.read_text())
    with a.dataset.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    if digest != cfg['data']['sha256']:
        raise ValueError('Dataset identity mismatch')
    lf = pl.scan_csv(a.dataset, infer_schema_length=20000)
    # Explicit projection prevents accessing outcome labels in this quality audit.
    names = [n for n in lf.collect_schema().names() if n != 'clase_ternaria']
    df = lf.select(names).filter(pl.col('foto_mes').is_between(201901, 201910)).collect()
    if set(df['foto_mes'].unique()) != set(range(201901, 201911)):
        raise ValueError('January-October months required')
    keys = df.select(['numero_de_cliente', 'foto_mes'])
    if keys.is_duplicated().any() or any(keys.null_count().row(0)):
        raise ValueError('Duplicate or missing keys')
    raw = [n for n in names if n not in META]
    if len(raw) != 152:
        raise ValueError('Unexpected raw schema')
    rows = summarize(df, raw)
    findings = assess(rows)
    a.output.mkdir(parents=True)
    report = {'status': 'AUDITED_REQUIRES_REVIEW_BEFORE_FITTING',
        'dataset_sha256': digest, 'training_executed': False,
        'october_labels_accessed': False, 'raw_columns': raw,
        'monthly_rows': df.group_by('foto_mes').len().sort('foto_mes').to_dicts(),
        'suspected_breaks': findings, 'variable_month_statistics': rows}
    (a.output / 'calidad.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'status': report['status'], 'findings': findings}))

if __name__ == '__main__':
    main()
