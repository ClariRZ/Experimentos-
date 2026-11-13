import json,math,hashlib
from pathlib import Path
r=Path(__file__).resolve().parents[1];p=r/'resultados/octubre_v6_01'
f=json.loads((p/'FINAL.json').read_text());policy=json.loads((p/'policy_frozen.json').read_text());gate=json.loads((p/'august_verification.json').read_text())
assert f['training_fits']==0 and f['status']=='OCTOBER_EVALUATED'
assert json.loads((p/'supervisor.json').read_text())['returncode']==0
assert len(gate)==11 and all(len(x)==5 and all(v['exact'] and v['max_error']==0 for v in x.values()) for x in gate.values())
results={a:json.loads((p/a/'result.json').read_text()) for a in f['arms']}
for a,d in results.items():
 assert len(d['seeds'])==5
 for row,prop in [(s,policy['arms'][a]['seeds'][str(s['seed'])]) for s in d['seeds']]+[({'gain':d['ensemble_gain']},policy['arms'][a]['ensemble'])]:
  g=row['gain'];assert g['n_clients']==f['n_october'];assert g['cut_contacts']==math.floor(prop*f['n_october'])
  hits=(g['point_gain']+27500*g['cut_contacts'])/1100000
  assert hits.is_integer() and 0<=hits<=g['cut_contacts']
for c in f['comparisons']:
 a,b=results[c['arm']],results[c['control']]
 assert c['ensemble_gain_delta']==a['ensemble_gain']['point_gain']-b['ensemble_gain']['point_gain']
 ds=[x['gain']['point_gain']-y['gain']['point_gain'] for x,y in zip(a['seeds'],b['seeds'])]
 assert ds==c['paired_seed_deltas'] and c['gain_wins']==sum(d>0 for d in ds)
print('VERIFIED 55 seed policies, 11 ensembles, 18 comparisons, no refits')
print('seconds',f['seconds'],'n',f['n_october'])
base=results['B0_J']['ensemble_gain']['point_gain'];comps={c['arm']:c for c in f['comparisons'] if c['control']=='B0_J'}
for a,d in results.items():
 c=comps.get(a,{});print(a,d['ensemble_gain']['cut_contacts'],d['ensemble_gain']['point_gain'],c.get('ensemble_gain_delta',0),c.get('gain_wins','-'))
