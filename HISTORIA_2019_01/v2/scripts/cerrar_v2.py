"""Canaritos, reoptimización pareada y congelamiento; no evalúa octubre sin equivalencia oficial."""
import json,time,gc,traceback
from pathlib import Path
import numpy as np
import polars as pl
import lightgbm as lgb
from ejecutar_v2 import ROOT,save,sha,log,Experiment,compare,policy
from continuar_familias import families,fixed_model
from historia_features import load_and_audit,add_lags_deltas,ID,MONTH,LABEL
from historia import optimize,Budget

def select_methods(frame,raw,columns,cfg,out,budget):
 path=out/'seleccion_canaritos.json'
 if path.exists():return json.loads(path.read_text())
 tr=frame.filter(pl.col(MONTH).is_in([201903,201904,201905,201906]));x=tr.select(columns).to_numpy().astype('float32');y=tr[LABEL].is_in(['BAJA+1','BAJA+2']).to_numpy().astype('int8')
 g=[];noise=[];rng=np.random.default_rng(991);canaries=rng.random((len(x),40)).astype('float32')
 # Las dos selecciones usan los mismos modelos y candidatos, y sólo train.
 for seed in cfg['seeds'][:5]:
  budget.check();m=fixed_model(np.column_stack([x,canaries]),y,seed,cfg);z=m.feature_importance('gain');z=z/max(z.sum(),1);g.append(z[:-40]);noise.append(z[-40:]);del m;gc.collect()
 g=np.asarray(g);med=np.median(g,axis=0);stability=(g>0).mean(0);threshold=float(np.quantile(np.median(noise,axis=0),.95));derived=[c for c in columns if c not in raw]
 order=sorted(derived,key=lambda c:(-stability[columns.index(c)],-med[columns.index(c)],c));keep_gain=order[:max(1,int(np.ceil(.8*len(order))))] if order else []
 keep_noise=[c for c in derived if med[columns.index(c)]>threshold]
 result={'gain_columns':raw+keep_gain,'canary_columns':raw+keep_noise,'candidate_columns':columns,'n_canaries':40,'canary_seed':991,'cutoff':threshold,'rule_gain':'80% de derivadas ordenadas por estabilidad no-cero y gain mediano; RAW siempre conservadas','rule_canary':'gain mediano > percentil95 del gain mediano de40 canarios; RAW siempre conservadas','seeds':cfg['seeds'][:5],'training_months':[201903,201904,201905,201906],'august_used':False}
 save(path,result);return result

def fixed_gain(y,p,ids,fraction):
 k=int(np.floor(fraction*len(y)));order=np.lexsort((ids,-p));return float(np.where(y[order[:k]]==1,1072500.,-27500.).sum())

def final_evaluation(frame,raw,arms,cfg,out,frozen):
 # Debe permanecer cerrado si la referencia adaptada aún no fue verificada contra Alejandro.
 if not cfg.get('official_baseline_verified',False):
  save(out/'estado.json',{'estado':'CANDIDATA_CONGELADA_TEST_PENDIENTE_EQUIVALENCIA_BASELINE','octubre_abierto':False,'reason':'B4 elegible588 no equivale automáticamente al baseline oficial o VM000760. Se necesita verificar la referencia antes del único test final.'});return
 path=out/'evaluacion_octubre.json'
 if path.exists():return
 test=frame.filter(pl.col(MONTH)==201910);ids=test[ID].to_numpy();preds={}
 for key,item in frozen['models'].items():
  x=test.select(item['columns']).to_numpy().astype('float32');ps=[]
  for seed in cfg['seeds']:
   model_path=out/item['name']/f'seed_{seed}.txt';assert sha(model_path)==item['hashes'][str(seed)]
   ps.append(lgb.Booster(model_file=str(model_path)).predict(x))
  preds[key]=np.asarray(ps);del x
 # Sólo aquí se leen etiquetas de octubre, después de congelar modelos/columnas/políticas.
 source=pl.scan_csv(cfg['data'],infer_schema=False,null_values=['','NA','NaN','nan','NULL','null'])
 labels=source.select(pl.col(ID).cast(pl.Int64),pl.col(MONTH).cast(pl.Int64),pl.col(LABEL)).filter(pl.col(MONTH)==201910).collect()
 labels=test.select(ID).join(labels,on=ID,how='left',validate='1:1',maintain_order='left')
 assert labels[LABEL].is_in(['CONTINUA','BAJA+1','BAJA+2']).all() and labels[LABEL].null_count()==0
 y=(labels[LABEL]=='BAJA+2').to_numpy().astype('int8');summary={}
 for key,pa in preds.items():
  frac=frozen['models'][key]['fraction'];g=[fixed_gain(y,p,ids,frac) for p in pa]
  summary[key]={'gain_ensemble':fixed_gain(y,pa.mean(0),ids,frac),'gain_seed_mean':float(np.mean(g)),'gain_seed_median':float(np.median(g)),'gain_seeds':g,'contacts':int(np.floor(frac*len(y))),'fraction_fixed_august':frac}
 rng=np.random.default_rng(20261110);delta=[];a=preds['candidate'].mean(0);b=preds['baseline'].mean(0)
 for _ in range(cfg['bootstrap_replicas']):
  ix=rng.integers(len(y),size=len(y));delta.append(fixed_gain(y[ix],a[ix],ids[ix],frozen['models']['candidate']['fraction'])-fixed_gain(y[ix],b[ix],ids[ix],frozen['models']['baseline']['fraction']))
 ci=np.quantile(delta,[.05,.95]).tolist();wins=int((np.asarray(summary['candidate']['gain_seeds'])>np.asarray(summary['baseline']['gain_seeds'])).sum())
 save(path,{'models':summary,'delta_gain_ensemble':summary['candidate']['gain_ensemble']-summary['baseline']['gain_ensemble'],'delta_gain_bootstrap_ci90':ci,'seed_wins':wins,'superiority':'NO CONCLUYENTE' if ci[0]<=0<=ci[1] else 'Diferencia observada; octubre previamente expuesto en otros experimentos','frozen_sha256':sha(out/'congelamiento_final.json'),'october_previous_exposure':True,'no_future_selection_allowed':True})
 save(out/'estado.json',{'estado':'FINALIZADO','octubre_abierto':True})

def main():
 out=ROOT/'resultados';state=json.loads((out/'estado.json').read_text())
 assert state['estado']=='COMBINACIONES_COMPLETAS_PENDIENTE_CANARITOS_REOPT_TEST'
 cfg=json.loads((ROOT/'configuraciones/protocolo.json').read_text());identity=json.loads((out/'identidad.json').read_text())['identity'];budget=Budget(out,(out/'identidad.json').stat().st_mtime+cfg['max_hours']*3600)
 assert sha(Path(cfg['data']))==cfg['expected_data_sha256']
 frame,raw,_=load_and_audit(cfg);frame=add_lags_deltas(frame,raw);selected=json.loads((out/'shortlist.json').read_text())['selected'];catalog=json.loads((ROOT/'configuraciones/c3_formulas.json').read_text());frame,_=families(frame,selected,catalog)
 arms=json.loads((ROOT/'configuraciones/escalera_congelada.json').read_text())['arms'];pre=json.loads((out/'candidato_preliminar.json').read_text());hp=pre['hp'];exp=Experiment(frame,raw,cfg,out,identity)
 save(out/'estado.json',{'estado':'CANARITOS','octubre_abierto':False});methods=select_methods(frame,raw,pre['columns'],cfg,out,budget)
 parent=exp.fit(pre['name'],pre['columns'],hp,20);pg=exp.fit('SEL_GAIN',methods['gain_columns'],hp,20);pc=exp.fit('SEL_CANARY',methods['canary_columns'],hp,20)
 dg=compare(out,'SEL_GAIN',pre['name'],exp.ids,exp.yv,pg,parent,cfg['bootstrap_replicas']);dc=compare(out,'SEL_CANARY',pre['name'],exp.ids,exp.yv,pc,parent,cfg['bootstrap_replicas']);dm=compare(out,'SEL_CANARY','SEL_GAIN',exp.ids,exp.yv,pc,pg,cfg['bootstrap_replicas'])
 chosen,cols,pred=pre['name'],pre['columns'],parent
 if dg['verdict']=='APORTA':chosen,cols,pred='SEL_GAIN',methods['gain_columns'],pg
 if dc['verdict']=='APORTA' and dm['verdict']=='APORTA':chosen,cols,pred='SEL_CANARY',methods['canary_columns'],pc
 save(out/'estado.json',{'estado':'REOPTIMIZACION_PAREADA','octubre_abierto':False})
 hpbase=optimize(frame,arms['B4'],cfg,out/'optuna_B4',budget) # mismos50 trials existentes, no repetir.
 hpcand=optimize(frame,cols,cfg,out/'optuna_candidata',budget)
 pb=exp.fit('FINAL_BASELINE',arms['B4'],hpbase,20);pa=exp.fit('FINAL_CANDIDATE',cols,hpcand,20)
 oldbase=exp.fit('B4',arms['B4'],hp,20)
 compare(out,'FINAL_BASELINE','B4',exp.ids,exp.yv,pb,oldbase,cfg['bootstrap_replicas']);compare(out,'FINAL_CANDIDATE',chosen,exp.ids,exp.yv,pa,pred,cfg['bootstrap_replicas']);compare(out,'FINAL_CANDIDATE','FINAL_BASELINE',exp.ids,exp.yv,pa,pb,cfg['bootstrap_replicas'])
 frozen={'created_unix':time.time(),'selection_month':201908,'october_opened':False,'october_previous_exposure':True,'models':{},'reference_note':'B4 adaptado por R2; equivalencia oficial pendiente, test bloqueado por defecto'}
 for key,name,columns,p in [('baseline','FINAL_BASELINE',arms['B4'],pb),('candidate','FINAL_CANDIDATE',cols,pa)]:
  opt=policy(exp.ids,exp.yv,p.mean(0));frozen['models'][key]={'name':name,'columns':columns,'fraction':opt['n_send']/len(exp.yv),'august_policy':opt,'hashes':{str(seed):sha(out/name/f'seed_{seed}.txt') for seed in cfg['seeds']}}
 save(out/'congelamiento_final.json',frozen);final_evaluation(frame,raw,arms,cfg,out,frozen)

if __name__=='__main__':
 try:main()
 except BaseException as e:
  save(ROOT/'resultados/error_cierre.json',{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc(),'octubre_abierto':'consultar congelamiento y log, no asumir false'});raise
