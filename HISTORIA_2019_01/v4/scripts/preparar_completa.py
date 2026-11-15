from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
s=(root/'scripts/ejecutar_inicial.py').read_text()
a=s.index("  self.state('MEDICION');pilots=[]")
b=s.index("  for arm in ['B0','F1','F3','F4a','F4b']:",a)
s=s[:a]+"  self.state('CORRIDA_COMPLETA_AUTORIZADA')\n"+s[b:]
s=s.replace('if self.fits>77:', 'if self.fits>75:')
s=s.replace("  df=pl.scan_csv(args.dataset,infer_schema_length=20000).filter(pl.col(MONTH).is_between(201901,201908)).collect()\n  self.registry=prepare(df,self.cfg,self.art,self.out,self.check);del df;gc.collect()",'''  prior=ROOT/'resultados/inicial_20261111_01'
  previous=json.loads((prior/'config_frozen.json').read_text())
  for key in ['data','feature_policy','recipes','arms','hyperparameter_search','evaluation']:
   assert self.cfg[key]==previous[key], 'Experimental design changed: '+key
  self.registry=json.loads((prior/'feature_manifest.json').read_text())
  for arm,entry in self.registry.items():
   source=prior/'private'/f'{arm}.parquet'
   assert sha(source)==entry['matrix_file_sha256']
   (self.art/source.name).symlink_to(source)
  (self.art/'meta.parquet').symlink_to(prior/'private/meta.parquet')
  save(self.out/'feature_manifest.json',self.registry)
  save(self.out/'matrix_reuse.json',{'source':str(prior),'verified':True,'meta_sha256':sha(prior/'private/meta.parquet')})''')
s=s.replace("  self.check();self.fits+=1", "  self.check();self.fits+=1\n  print('FIT_START',self.fits,'seed',seed,'round_cap',rounds,flush=True)")
(root/'scripts/ejecutar_completa.py').write_text(s)
c=json.loads((root/'configuraciones/ejecucion_inicial.json').read_text())
c.update(version='v4_completa_16h',status='APROBADO_EJECUTAR_TRAS_CALIBRACION',authorization={'user_message':'corrrelo carajoooo','date':'2026-11-11','interpretation':'Proceed with complete five-arm experiment after being informed of approximately 15 hour projection; cap 16 hours'})
c['budget'].update(hard_vm_run_cap_minutes=960,pilot_fits=0,max_total_fits=75,pilot_budget_gate='Already calibrated. Explicit authorization to run complete experiment; enforce 16 hour cap.',max_total_boosting_rounds_bound=112500)
(root/'configuraciones/ejecucion_completa.json').write_text(json.dumps(c,indent=2)+'\n')
compile(s,'ejecutar_completa.py','exec')
print('PREPARADO: 5 brazos, 75 ajustes, 16 horas, octubre cerrado')
