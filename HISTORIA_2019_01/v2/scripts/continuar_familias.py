"""Etapas siguientes de v2. Nunca abre etiquetas de octubre.
No lanzar hasta aprobar las verificaciones de este módulo y finalizar la escalera.
"""
import sys,json,time,hashlib,gc,traceback
from pathlib import Path
import numpy as np
import polars as pl
import lightgbm as lgb
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score
from ejecutar_v2 import ROOT,save,sha,log,coverage,Experiment,compare,policy
from historia_features import load_and_audit,add_lags_deltas,ID,MONTH,LABEL
from historia import optimize,Budget,lgb_params

SELECTION_HP={'num_leaves':31,'learning_rate':.03,'min_data_in_leaf':1000,'feature_fraction':.8,'bagging_fraction':.8}

def fixed_model(x,y,seed,cfg):
 return lgb.train(lgb_params(cfg,SELECTION_HP,seed),lgb.Dataset(x,label=y),num_boost_round=150)

def shortlist(frame,raw,eligible,cfg,out,budget):
 dest=out/'shortlist.json'
 if dest.exists():return json.loads(dest.read_text())['selected']
 # Criterio fijado en el código antes de ver el ranking. Categorías/fechas no reciben medias o ratios.
 exclude={'active_quarter','cliente_vip','internet','tcuentas','tcallcenter','thomebanking','tmobile_app'}
 candidates=[c for c in eligible if c not in exclude and not any(t in c for t in ['status','delinquency','Fvencimiento','Finiciomora','fultimo_cierre','fechaalta'])]
 tr=frame.filter(pl.col(MONTH).is_in([201903,201904,201905]));va=frame.filter(pl.col(MONTH)==201906)
 x=tr.select(raw).to_numpy().astype('float32');v=va.select(raw).to_numpy().astype('float32')
 yt=tr[LABEL].is_in(['BAJA+1','BAJA+2']).to_numpy().astype('int8');yv=(va[LABEL]=='BAJA+2').to_numpy().astype('int8')
 gains=[];models=[];basepred=[]
 for seed in cfg['seeds'][:5]:
  budget.check();m=fixed_model(x,yt,seed,cfg);g=m.feature_importance('gain');gains.append(g/g.sum());models.append(m);basepred.append(m.predict(v))
 gains=np.array(gains);meanpred=np.mean(basepred,axis=0);baseauc=roc_auc_score(yv,meanpred);records=[]
 for c in candidates:
  budget.check();j=raw.index(c);rng=np.random.default_rng(20261110+j);vp=v.copy();vp[:,j]=vp[rng.permutation(len(vp)),j]
  perm=np.mean([m.predict(vp) for m in models],axis=0);pi=float(baseauc-roc_auc_score(yv,perm))
  # Screening barato de representaciones, sólo junio: RAW -> +lag1 -> +delta1.
  added=[];screen=[]
  for op in ['lag1','delta1']:
   added.append(f'{c}__{op}');xx=np.column_stack([x,tr.select(added).to_numpy()]).astype('float32');vv=np.column_stack([v,va.select(added).to_numpy()]).astype('float32')
   m=fixed_model(xx,yt,cfg['seeds'][0],cfg);screen.append(float(roc_auc_score(yv,m.predict(vv))));del m,xx,vv
  records.append({'variable':c,'gain':float(np.median(gains[:,j])),'stability':float((gains[:,j]>0).mean()),'pi_junio':pi,'lag1_delta_auc_junio':screen[0]-float(roc_auc_score(yv,basepred[0])),'delta1_delta_auc_junio':screen[1]-screen[0]})
  save(out/'shortlist_parcial.json',records);log(f'Selección train-only: {c}')
 if len(records)<20:raise ValueError('Menos de20 fuentes elegibles: no se cambia tamaño de shortlist automáticamente')
 metrics=['gain','stability','pi_junio','lag1_delta_auc_junio','delta1_delta_auc_junio']
 ranks=np.column_stack([rankdata([r[k] for r in records],method='average')/len(records) for k in metrics]);scores=ranks.mean(1)
 order=sorted(range(len(records)),key=lambda i:(-scores[i],records[i]['variable']));selected=[];redundant=[]
 # Correlación sobre todas las filas train03–05, pares observados; sin agosto.
 for i in order:
  c=records[i]['variable'];a=x[:,raw.index(c)];redundancy=False
  for other in selected:
   b=x[:,raw.index(other)];ok=np.isfinite(a)&np.isfinite(b)
   if ok.sum()>1 and np.std(a[ok])>0 and np.std(b[ok])>0 and abs(np.corrcoef(a[ok],b[ok])[0,1])>.98:redundancy=True;break
  if redundancy:redundant.append(c);continue
  selected.append(c)
  if len(selected)==20:break
 if len(selected)<20:raise ValueError('Filtro redundancia deja menos de20: detener y documentar')
 for i,r in enumerate(records):r['score_percentiles']=float(scores[i])
 save(dest,{'selected':selected,'records':records,'redundant':redundant,'rule':'media de5 percentiles (gain mediano, estabilidad, PI junio, deltaAUC lag1 junio, deltaAUC delta1 junio); |corr|<=.98; empate nombre','train':[201903,201904,201905],'holdout':201906,'hp':SELECTION_HP,'rounds':150,'seeds':cfg['seeds'][:5],'august_used':False})
 del x,v,models;gc.collect();return selected

def families(frame,selected,catalog):
 families={k:[] for k in ['M1','M2','M3','M4','Z','R','K','T1','C3_TICKETS','C3_SUMAS']};expr=[]
 for c in selected:
  a,b,d=[pl.col(n).cast(pl.Float64) for n in [c,f'{c}__lag1',f'{c}__lag2']];full=pl.all_horizontal([z.is_finite().fill_null(False) for z in [a,b,d]]);mean=(a+b+d)/3
  recipes={'M1':mean,'M2':pl.min_horizontal(a,b,d),'M3':pl.max_horizontal(a,b,d),'M4':(((a-mean)**2+(b-mean)**2+(d-mean)**2)/3).sqrt(),'T1':(a-d)/2,'Z':pl.when(a!=0).then(0).when(b!=0).then(1).when(d!=0).then(2).otherwise(3),'R':pl.when((a>=0)&(b>=0)&(d>=0)&(mean>1e-12)).then(a/mean)}
  for k,v in recipes.items():
   name=f'v2_{k}__{c}';families[k].append(name);expr.append(pl.when(full).then(v).otherwise(None).cast(pl.Float32).alias(name))
  # Ranking monetario sólo para fuentes monetarias; ceros reales conservan rango 0, NA conserva NA.
  if c.startswith('m') or '_m' in c:
   name=f'v2_K__{c}';families['K'].append(name);expr.append(pl.when(a.is_null()).then(None).when(a==0).then(0).otherwise(a.rank(method='average').over(MONTH)/a.count().over(MONTH)).cast(pl.Float32).alias(name))
 for item in catalog:
  sources=item['sources'];kind=item['kind']
  if not set(sources)<=set(selected):continue
  a,b=map(pl.col,sources);ok=a.is_finite().fill_null(False)&b.is_finite().fill_null(False)
  v=pl.when(b>0).then(a/b) if kind=='C3_TICKETS' else a+b
  name='v2_'+item['feature'];families[kind].append(name);expr.append(pl.when(ok).then(v).otherwise(None).cast(pl.Float32).alias(name))
 return frame.with_columns(expr),families

def main():
 cfg=json.loads((ROOT/'configuraciones/protocolo.json').read_text());out=ROOT/'resultados';state=json.loads((out/'estado.json').read_text())
 assert state['estado'] in ['ESCALERA_COMPLETA_PENDIENTE_FAMILIAS','SHORTLIST_TRAIN_ONLY','SCREENING_FAMILIAS'],'Estado no compatible'
 identity=json.loads((out/'identidad.json').read_text())['identity'];budget=Budget(out,(out/'identidad.json').stat().st_mtime+cfg['max_hours']*3600)
 assert sha(Path(cfg['data']))==cfg['expected_data_sha256']
 frame,raw,audit=load_and_audit(cfg);frame=add_lags_deltas(frame,raw);frozen=json.loads((ROOT/'configuraciones/escalera_congelada.json').read_text());arms=frozen['arms'];hp=json.loads((out/'optuna_B4/best.json').read_text())['hyperparams']
 save(out/'estado.json',{'estado':'SHORTLIST_TRAIN_ONLY','octubre_abierto':False})
 selected=shortlist(frame,raw,frozen['eligible'],cfg,out,budget)
 catalog=json.loads((ROOT/'configuraciones/c3_formulas.json').read_text());frame,fams=families(frame,selected,catalog)
 cov=coverage(frame,[c for cols in fams.values() for c in cols]);eligibility={}
 for name,cols in fams.items():
  ok=bool(cols) and all(cov[m][c]>=.9 for m in [201903,201904,201905,201906] for c in cols)
  eligibility[name]={'status':'IDENTIFICABLE' if ok else 'NO IDENTIFICABLE','columns':cols,'coverage':{str(m):{c:cov[m][c] for c in cols} for m in cov}}
 save(ROOT/'auditoria/familias_cobertura.json',eligibility)
 exp=Experiment(frame,raw,cfg,out,identity);base=exp.fit('B4',arms['B4'],hp,5);candidates={};screen={}
 save(out/'estado.json',{'estado':'SCREENING_FAMILIAS','octubre_abierto':False})
 for name,info in eligibility.items():
  if info['status']!='IDENTIFICABLE':log(f'{name}: NO IDENTIFICABLE');continue
  cols=arms['B4']+info['columns'];pa=exp.fit(name,cols,hp,5);screen[name]=compare(out,name,'B4',exp.ids,exp.yv,pa,base,cfg['bootstrap_replicas']);candidates[name]=cols
 # Confirmar una sola vez todos los APORTA/INDICIO del screening; mismas semillas pareadas.
 pending=[name for name,d in screen.items() if d['verdict'] in ['APORTA','INDICIO']]
 if not pending:
  save(out/'estado.json',{'estado':'FIN_SIN_FAMILIAS_PROMOVIBLES','octubre_abierto':False,'reason':'Regla de etapa2: ninguna familia APORTA/INDICIO; no combinar ni reoptimizar a posteriori'});return
 base20=exp.fit('B4',arms['B4'],hp,20);confirmed={}
 for name in pending:
  pa=exp.fit(name,candidates[name],hp,20);d=compare(out,name,'B4',exp.ids,exp.yv,pa,base20,cfg['bootstrap_replicas'])
  if d['verdict']=='APORTA':confirmed[name]=d
 # Ratios individuales condicionados al resultado de familia; no sustituyen confirmación de la familia.
 if 'R' in pending:
  for i,col in enumerate(fams['R']):
   name=f'R_{i+1:02}';pa=exp.fit(name,arms['B4']+[col],hp,5);compare(out,name,'B4',exp.ids,exp.yv,pa,base,cfg['bootstrap_replicas'])
 if not confirmed:
  save(out/'estado.json',{'estado':'FIN_SIN_APORTA_CONFIRMADO','octubre_abierto':False,'reason':'Regla de etapa3: ninguna familia APORTA confirmada con20 semillas'});return
 # Confirmación de escalera antes de fijar punto de partida por ganancia de agosto.
 bpred={name:exp.fit(name,cols,hp,20) for name,cols in arms.items()}
 best=max(arms,key=lambda n:policy(exp.ids,exp.yv,bpred[n].mean(0))['gain_smoothed']);current_name=best;current_cols=arms[best];current=bpred[best]
 order=sorted(confirmed,key=lambda n:(-confirmed[n]['delta_gain_mean'],n));save(out/'orden_combinaciones.json',{'base':best,'families':order,'rule':'delta ganancia confirmada decreciente, empate nombre; sin reordenar'})
 for j,name in enumerate(order,1):
  proposed=f'COMB_{j:02}';cols=current_cols+[c for c in fams[name] if c not in current_cols];pa=exp.fit(proposed,cols,hp,20);d=compare(out,proposed,current_name,exp.ids,exp.yv,pa,current,cfg['bootstrap_replicas'])
  if d['verdict']=='APORTA':current_name,current_cols,current=proposed,cols,pa
 # Detener antes de nuevas decisiones no implementadas/verificadas: no llamarlo experimento completo.
 save(out/'candidato_preliminar.json',{'name':current_name,'columns':current_cols,'hp':hp,'selection':'agosto','octubre_abierto':False})
 save(out/'estado.json',{'estado':'COMBINACIONES_COMPLETAS_PENDIENTE_CANARITOS_REOPT_TEST','candidate':current_name,'octubre_abierto':False})

if __name__=='__main__':
 try:main()
 except BaseException as e:
  save(ROOT/'resultados/error_familias.json',{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc(),'octubre_abierto':False});raise
