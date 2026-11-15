import importlib.util
import sys
from pathlib import Path
import numpy as np
import polars as pl
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('audit',ROOT/'scripts/01_full_audit.py')
audit=importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
from fe_core import build_exact_lags,build_window_families,evaluate_gain_curve,sanitize_base

@pytest.mark.parametrize('L',[3,4,6])
def test_slope_and_extrema(L):
    vals=[10.,13.,19.,22.,25.,31.][-L:]
    df=pl.DataFrame({'numero_de_cliente':[1]*L,'foto_mes':list(range(201907-L,201907)),'x':vals})
    out=build_window_families(build_exact_lags(df,['x'],L-1),['x'],L,include_f2=True).row(-1,named=True)
    assert out[f'x__f2_slope_W{L}']==pytest.approx(np.polyfit(range(L),vals,1)[0])
    assert out[f'x__f1_mean_W{L}']==pytest.approx(np.mean(vals))
    assert out[f'x__f1_range_W{L}']==max(vals)-min(vals)

def test_gain_tie_amount_and_zero_contacts():
    ids=np.array([2,1]); scores=np.array([.5,.5]); labels=np.array([0,1])
    result=evaluate_gain_curve(ids,scores,labels,frozen_prop=.5)
    assert result['point_gain']==1072500
    assert evaluate_gain_curve(ids,scores,labels,frozen_prop=1)['point_gain']==1045000
    assert evaluate_gain_curve(ids,scores,labels,frozen_prop=0)['point_gain']==0

def test_smoothed_curve_independent_reference():
    n=3000; ids=np.arange(n); scores=-ids.astype(float); y=(ids<300).astype(int)
    cum=np.cumsum(np.where(y,1072500.,-27500.))
    expected=np.array([cum[i-1000:i+1001].mean() for i in range(1000,n-1000)])
    got=evaluate_gain_curve(ids,scores,y)
    assert got['smoothed_gain_max']==pytest.approx(expected.max())
    assert got['cut_contacts']==int(expected.argmax())+1001

def test_coverage_rejects_nonfinite():
    df=pl.DataFrame({'foto_mes':[201906]*4,'x':[None,float('nan'),float('inf'),2.]})
    assert audit.coverage(df,['x'],[201906])['x']['201906']==.25

def test_duplicate_detection_and_constant_do_not_drop_other_source_features():
    df=pl.DataFrame({'a':[None,1.,2.],'b':[None,1.,2.],'c':[0.,0.,0.],'d':[None,2.,1.]})
    result=audit.redundancies(df,list(df.columns))
    assert result=={'b':'duplicada_de:a','c':'constante'}
    assert df.columns==['a','b','c','d']

def test_masks_and_nonfinite():
    df=pl.DataFrame({'numero_de_cliente':[1,1,1],'foto_mes':[201903,201904,201905],'x':[1.,2.,float('inf')]})
    out=sanitize_base(df,['x'],{201904:['x']})
    assert out['x'].to_list()==[1.,None,None]

def test_overflow_ratio_becomes_null():
    df=pl.DataFrame({'numero_de_cliente':[1]*3,'foto_mes':[201901,201902,201903],'x':[1e-300,1e-300,1e300]})
    out=build_window_families(build_exact_lags(df,['x'],2),['x'],3)
    assert out['x__f3_rel_prev_W3'][-1] is None

def test_required_months_and_labels():
    df=pl.DataFrame({'numero_de_cliente':[1]*8,'foto_mes':list(range(201901,201909)),'clase_ternaria':['CONTINUA']*8})
    audit.validate(df)
    with pytest.raises(ValueError,match='Faltan meses'): audit.validate(df.head(7))
    with pytest.raises(ValueError,match='Etiquetas'): audit.validate(df.with_columns(pl.lit(None).alias('clase_ternaria')))

def test_prior_seed_mismatch_stops_audit():
    audit.validate_seeds({'seeds':audit.SEEDS},{'seeds':audit.SEEDS})
    with pytest.raises(ValueError): audit.validate_seeds({'seeds':audit.SEEDS},{'seeds':audit.SEEDS[:-1]})

def test_end_to_end_audit_synthetic(tmp_path):
    import json,hashlib,subprocess
    cfg=json.loads((ROOT/'configuraciones/auditoria.json').read_text())
    rows=[]
    for m in range(201901,201909):
        for client in range(1,5):
            row={'numero_de_cliente':client,'foto_mes':m,'clase_ternaria':'CONTINUA','saldo':float(client+m%100)}
            for c in sum(cfg['broken_masks'].values(),[]): row[c]=float(client+m%100)
            rows.append(row)
    data=tmp_path/'synthetic.parquet';pl.DataFrame(rows).write_parquet(data)
    cfg.update(expected_dataset_sha256=hashlib.sha256(data.read_bytes()).hexdigest(),sources_reviewed=True,history_sources=['saldo'])
    config=tmp_path/'config.json';config.write_text(json.dumps(cfg))
    prior=tmp_path/'prior.json';prior.write_text(json.dumps({'seeds':audit.SEEDS}))
    out=tmp_path/'result'
    subprocess.run([sys.executable,str(ROOT/'scripts/01_full_audit.py'),'--dataset',str(data),'--prior-config',str(prior),'--config',str(config),'--output',str(out)],check=True,capture_output=True,text=True)
    report=json.loads((out/'audit_summary.json').read_text())
    assert report['status']=='AUDITADO'
    assert report['baseline_count']==14
    assert len(report['r2_common_source_formula_pairs'])==8
    assert report['training_executed'] is False


def test_reviewed_count_with_only_two_values_is_valid():
    df=pl.DataFrame({'foto_mes':[201903,201904], 'cantidad':[0,1], 'estado':[0,6]})
    cfg={'sources_reviewed':True,'history_sources':['cantidad']}
    assert audit.select_sources(df,['cantidad','estado'],cfg)==['cantidad']
    with pytest.raises(ValueError):
        audit.select_sources(df,['cantidad','estado'],{'sources_reviewed':True,'history_sources':['ausente']})

def test_dictionary_classification_matches_schema_and_configuration():
    import json
    review=json.loads((ROOT/'configuraciones/revision_diccionario.json').read_text())
    cfg=json.loads((ROOT/'configuraciones/auditoria.json').read_text())
    records=review['variables']
    assert len(records)==len({v['dataset_column'] for v in records})==152
    assert cfg['history_sources']==[v['dataset_column'] for v in records if v['history_candidate']]
    assert len(cfg['history_sources'])==129
    assert 'mttarjeta_visa_debitos_automaticos' in cfg['history_sources']
    assert 'tcuentas' not in cfg['history_sources']
    assert 'Master_fechaalta' not in cfg['history_sources']


def test_mobile_numeric_text_and_nulls_cast_without_imputation():
    df=pl.DataFrame({'cmobile_app_trx':['1',None,'0']})
    out,names=audit.normalize_mobile_count(df)
    assert names==['cmobile_app_trx']
    assert out['cmobile_app_trx'].to_list()==[1.,None,0.]
    with pytest.raises(pl.exceptions.InvalidOperationError):
        audit.normalize_mobile_count(pl.DataFrame({'cmobile_app_trx':['corrupto']}))
