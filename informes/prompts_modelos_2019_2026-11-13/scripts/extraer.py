import json, math, statistics as st, hashlib, subprocess, argparse
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--repo',default='Experimentos-');ap.add_argument('--output',default='work/informe_prompts_2019');args=ap.parse_args();R=Path(args.repo);O=Path(args.output);O.mkdir(parents=True,exist_ok=True)
paths={'v4':'experimento_2026-11-13/resultados/agosto','v5':'HISTORIA_2019_01/v5/resultados/entrenamiento_20261113_01','v6':'HISTORIA_2019_01/v6/resultados/v6_20261113_02'}
configs={'v4':'experimento_2026-11-13/configuracion/contrato_original.json',**{v:p+'/config_frozen.json' for v,p in paths.items() if v!='v4'}}
used={}
def read(p):
 f=R/p;used[p]=hashlib.sha256(f.read_bytes()).hexdigest();return json.loads(f.read_text())
O4=read('experimento_2026-11-13/resultados/octubre/FINAL.json');O6=read('HISTORIA_2019_01/v6/resultados/octubre_v6_01/FINAL.json')
D={'source_commit':subprocess.check_output(['git','-C',str(R),'rev-parse','HEAD'],text=True).strip(),'versions':{},'models':[]}
for ver,path in paths.items():
 final=read(path+'/FINAL.json');cfg=read(configs[ver]);ident=read(path+'/data_identity.json');manifest=read(path+'/feature_manifest.json') if ver!='v4' else read('auditoria_trazabilidad_2026-11-13/protocolo_congelado_completo.json')['frozen']
 D['versions'][ver]={'final':final,'config':cfg,'identity':ident}
 base='B0_J' if ver=='v6' else 'B0';br=read(path+'/'+base+'/result.json')
 for arm in final['arms']:
  a=read(path+'/'+arm+'/result.json');best=read(path+'/'+arm+'/best.json');trials=read(path+'/'+arm+'/trials.json')
  assert len(trials)==10 and len(a['seeds'])==5
  win=max(trials,key=lambda t:t['auc']);assert win['trial']==best['trial'] and win['params']==best['params'] and win['rounds']==best['rounds']
  if manifest: assert len(manifest[arm]['columns'])==a['columns']
  assert [s['seed'] for s in a['seeds']]==[s['seed'] for s in br['seeds']]
  da=[s['auc']-b['auc'] for s,b in zip(a['seeds'],br['seeds'])];dg=[s['gain']['smoothed_gain_max']-b['gain']['smoothed_gain_max'] for s,b in zip(a['seeds'],br['seeds'])]
  if arm!=base:
   c=next(c for c in final['comparisons'] if c['arm']==arm and c['control']==base)
   assert math.isclose(st.mean(dg),c['delta_gain_mean'],abs_tol=1e-6)
  m={'version':ver,'arm':arm,'base':base,'best':best,'columns':a['columns'],'feature_names':manifest[arm]['columns'] if manifest else None,'august':a,'october':None,'summary':{'auc_delta_mean':st.mean(da),'auc_wins':sum(x>0 for x in da),'gain_delta_mean':st.mean(dg),'gain_delta_median':st.median(dg),'gain_delta_sd':st.stdev(dg),'gain_wins':sum(x>0 for x in dg),'ensemble_delta':a['ensemble_gain']['smoothed_gain_max']-br['ensemble_gain']['smoothed_gain_max']},'source':path+'/'+arm}
  if ver=='v4':
   o=O4['results'][arm];b=O4['results'][base];m['october']={'ensemble_auc':o['ensemble']['auc'],'ensemble_gain':o['ensemble'],'seeds':[{'seed':x['seed'],'auc':x['auc'],'gain':x} for x in o['seeds']]};basegain=b['ensemble']['point_gain'];bseeds=b['seeds'];get=lambda x:x['point_gain']
  elif ver=='v6':
   o=read('HISTORIA_2019_01/v6/resultados/octubre_v6_01/'+arm+'/result.json');b=read('HISTORIA_2019_01/v6/resultados/octubre_v6_01/'+base+'/result.json');m['october']=o;basegain=b['ensemble_gain']['point_gain'];bseeds=b['seeds'];get=lambda x:x['gain']['point_gain']
  if m['october']:
   oo=m['october'];g=oo['ensemble_gain'];k=g['cut_contacts'];hits=(g['point_gain']+27500*k)/1100000;assert hits.is_integer();g['hits_recalculated']=int(hits)
   assert k==math.floor(a['ensemble_gain']['contact_proportion']*135754)
   od=[x['gain']['point_gain']-get(y) for x,y in zip(oo['seeds'],bseeds)]
   oo['summary']={'ensemble_delta':g['point_gain']-basegain,'ensemble_delta_pct':100*(g['point_gain']-basegain)/basegain,'gain_mean':st.mean(x['gain']['point_gain'] for x in oo['seeds']),'gain_delta_mean':st.mean(od),'gain_delta_median':st.median(od),'gain_delta_sd':st.stdev(od),'wins':sum(x>0 for x in od)}
  ga=a['ensemble_gain'];hit=(ga['point_gain_at_cut']+27500*ga['cut_contacts'])/1100000;assert hit.is_integer();ga['hits_recalculated']=int(hit)
  m['eligible']=False if arm==base else (st.mean(da)>0 and sum(x>0 for x in da)>=4 if ver=='v4' else m['summary']['ensemble_delta']>0 and st.mean(dg)>0 and sum(x>0 for x in dg)>=4)
  D['models'].append(m)
D['october_v6_contrasts']=O6['comparisons']
extra=['experimento_2026-11-13/prompts/01_prompt_original.txt','experimento_2026-11-13/prompts/02_plan_adaptado.md','experimento_2026-11-13/prompts/03_contrato_ejecutado.json','HISTORIA_2019_01/v5/prompts/PROMPT_MAESTRO_HISTORIA_2019_v5.md','HISTORIA_2019_01/v6/prompts/PROMPT_MAESTRO_HISTORIA_2019_v6.md','auditoria_trazabilidad_2026-11-13/INFORME.md','auditoria_trazabilidad_2026-11-13/calibrar_original_vm.py','auditoria_trazabilidad_2026-11-13/modelos_sha256.json','HISTORIA_2019_01/v6/auditoria/INCIDENTE_ARRANQUE_01.json','HISTORIA_2019_01/v6/resultados/octubre_v6_01/august_verification.json','HISTORIA_2019_01/v6/resultados/octubre_v6_01/policy_frozen.json']
for ver,path in paths.items():
 if ver!='v4':extra.append(path+'/entorno.json')
for p in extra:used[p]=hashlib.sha256((R/p).read_bytes()).hexdigest()
assert (R/extra[2]).read_bytes()==(R/configs['v4']).read_bytes()
D['source_files_sha256']=used
(O/'evidencia.json').write_text(json.dumps(D,ensure_ascii=False,indent=2)+'\n')
print('Verificados',len(D['models']),'brazos,',sum(len(v['final']['arms'])*15 for v in D['versions'].values()),'ajustes; selección Optuna, columnas, métricas, cortes y aciertos.')
for m in D['models']:
 print(m['version'],m['arm'],m['columns'],'auc',round(m['august']['ensemble_auc'],6),'g',round(m['august']['ensemble_gain']['smoothed_gain_max']/1e6,4),'d',round(m['summary']['ensemble_delta']/1e6,4),'wins',m['summary']['gain_wins'],'eligible',m['eligible'])
