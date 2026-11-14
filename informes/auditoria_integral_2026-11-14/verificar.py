"""Read-only aggregate audit. No training, cloud access or client data."""
from pathlib import Path
import json,hashlib,math
R=Path(__file__).resolve().parents[2]
def read(p):return json.loads((R/p).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks={}
for name in ['experimento_2026-11-13/MANIFIESTO_SHA256.json','HISTORIA_2019_01/v5/MANIFIESTO_SHA256.json','HISTORIA_2019_01/v6/MANIFIESTO_SHA256.json','HISTORIA_2019_01/v7/MANIFIESTO_CODIGO.json','HISTORIA_2019_01/v7/resultados/MANIFIESTO_SHA256.json']:
 p=R/name;d=json.loads(p.read_text())
 checks[name]={'checked':len(d),'mismatches':[n for n,h in d.items() if not (p.parent/n).is_file() or sha(p.parent/n)!=h]}
v='HISTORIA_2019_01/v7/resultados/'
a=read(v+'octubre/FINAL.json');cfg=read(v+'agosto/config_frozen.json');frozen=read(v+'agosto/policy_frozen.json')
assert a['new_fits']==0 and a['august_predictions_regenerated']==50
for n in ['config_frozen.json','feature_manifest.json','policy_frozen.json','comparisons_201908.json']:
 assert (R/v/'agosto'/n).read_bytes()==(R/v/'octubre'/n).read_bytes()
for arm in a['arms']:
 p=v+'agosto/'+arm+'/'
 trials=read(p+'trials.json');best=read(p+'best.json');winner=max(trials,key=lambda x:x['auc'])
 assert len(trials)==10
 for k in ['trial','params','rounds','auc']:assert winner[k]==best[k]
for stage,month in [('agosto','august'),('octubre','october')]:
 results={arm:read(v+stage+'/'+arm+'/result_'+month+'.json') for arm in a['arms']}
 k=3481 if stage=='agosto' else 3583
 for arm,r in results.items():
  assert len(r['seeds'])==5
  for x in [r['common']]+[s['common'] for s in r['seeds']]:
   assert x['contacts']==k
   assert x['gain']==1100000*x['hits']-27500*k
  if stage=='octubre':
   assert k==math.floor(frozen['common_proportion']*135754)
 for c in read(v+stage+'/comparisons_'+('201908' if stage=='agosto' else '201910')+'.json')['rows']:
  r,b=results[c['arm']],results[c['control']]
  assert [s['seed'] for s in r['seeds']]==[s['seed'] for s in b['seeds']]
  ds=[x['common']['gain']-y['common']['gain'] for x,y in zip(r['seeds'],b['seeds'])]
  assert ds==c['paired_seed_deltas']
  assert c['ensemble_delta']==r['common']['gain']-b['common']['gain']
  assert c['mean_seed_delta']==sum(ds)/5
  assert c['wins']==sum(d>0 for d in ds)
print(json.dumps({'manifests':checks,'v7_trials_verified':100,'v7_seed_common_gains_verified':100,'v7_ensemble_common_gains_verified':20,'v7_new_fits':0,'independent_training_reproduction':False},indent=2))
