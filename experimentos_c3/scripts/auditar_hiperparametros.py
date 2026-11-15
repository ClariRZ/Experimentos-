"""Extrae parámetros efectivos del texto de los boosters, sin entrenar."""
import argparse, csv, hashlib, json, re
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--models',type=Path,required=True)
p.add_argument('--ours',type=Path,default=Path(__file__).resolve().parents[2]/'experimento_historicas_B0_B5')
p.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'00_auditoria')
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
plan=json.loads((Path(__file__).resolve().parents[1]/'config/c3_plan_original.json').read_text())
def parse(path):
    text=path.read_text()
    params=dict(re.findall(r'^\[([^:\n]+): (.*)\]$',text,re.M))
    assert params, f'No hay parámetros: {path}'
    return params,len(re.findall(r'^Tree=\d+$',text,re.M)),hashlib.sha256(path.read_bytes()).hexdigest()
records=[];comparisons=[]; allparams={}
for seed in plan['seeds']:
    params,trees,digest=parse(a.models/f'modelo_{seed}.txt')
    assert int(params['seed'])==seed and trees==plan['rounds']
    for k,v in plan['params'].items():
        actual=params[{'boosting_type':'boosting'}.get(k,k)]
        if isinstance(v,bool): assert actual==str(int(v)),(seed,k)
        elif isinstance(v,(float,int)): assert float(actual)==v,(seed,k)
        else: assert actual==v,(seed,k,actual,v)
    allparams[str(seed)]=params
    records.append({'seed':seed,'trees':trees,'sha256':digest,'plan_coincide':True})
keys=['objective','metric','learning_rate','num_leaves','min_data_in_leaf','feature_fraction','bagging_fraction','bagging_freq','max_bin','max_depth','lambda_l1','lambda_l2','min_gain_to_split','min_sum_hessian_in_leaf','num_threads','deterministic','feature_pre_filter','zero_as_missing','scale_pos_weight','is_unbalance']
for model in ['C3','B0','B1','B2','B3','B4','B5']:
    if model=='C3': params=allparams[str(plan['seeds'][0])];trees=plan['rounds']
    else: params,trees,_=parse(a.ours/f'resultados/{model}/model.txt')
    comparisons.append({'modelo':model,'arboles_guardados':trees,**{k:params.get(k,'NO_REGISTRADO') for k in keys}})
varying={k:{seed:d.get(k) for seed,d in allparams.items()} for k in allparams[str(plan['seeds'][0])] if len({d.get(k) for d in allparams.values()})>1}
for name,rows in [('hiperparametros_comparados.csv',comparisons),('verificacion_20_modelos.csv',records)]:
    with (a.output/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(a.output/'parametros_efectivos_20_modelos.json').write_text(json.dumps(allparams,indent=2))
(a.output/'parametros_que_varian_entre_seeds.json').write_text(json.dumps(varying,indent=2))
print(json.dumps({'modelos_verificados':len(records),'parametros_variables':list(varying),'comparacion':comparisons},indent=2))
