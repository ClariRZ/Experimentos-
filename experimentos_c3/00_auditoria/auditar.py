"""Auditoría sin entrenamiento. Ejecutar desde cualquier directorio con el entorno científico."""
from pathlib import Path
import hashlib, json, zipfile, itertools, argparse
import numpy as np
import pandas as pd
import lightgbm as lgb

ap=argparse.ArgumentParser()
ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
a=ap.parse_args(); root=a.root
src=root/'work/radiografia_c3'; out=Path(__file__).resolve().parent
ours=root/'outputs/experimento_historicas'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads((src/'PLAN_FINAL.json').read_text())
delivery=json.loads((src/'ENTREGA.json').read_text())
catalog=pd.read_csv(src/'catalogo_features.csv').set_index('feature')
assert sha(src/'catalogo_features.csv')==plan['august_bank_hashes']['catalogo_features.csv']
features=plan['schema']; seeds=plan['seeds']
raw=json.loads((ours/'manifest.json').read_text())['families']['original']
assert features[:152]==raw and len(set(features))==2062
gains=[]; splits=[]; scores=[]; sets=[]; models=[]; hashes={}
for seed in seeds:
    p=src/f'modelos/modelo_{seed}.txt'; b=lgb.Booster(model_file=str(p))
    assert b.feature_name()==features and b.num_trees()==300
    z=np.load(src/f'modelos/seed_{seed}.npz',allow_pickle=False)
    assert sha(p)==str(z['model_sha256'].item())
    assert str(z['identity'].item())==delivery['plan_identity']
    assert int(z['seed'])==seed
    if scores: assert np.array_equal(ids,z['ids'])
    ids=z['ids']; pred=z['scores']; assert np.isfinite(pred).all()
    g=b.feature_importance('gain'); sp=b.feature_importance('split')
    gains.append(g/g.sum()); splits.append(sp); scores.append(pred)
    sets.append(set(np.lexsort((ids,-pred))[:11000].tolist()))
    models.append({'seed':seed,'trees':b.num_trees(),'variables_usadas':int((sp>0).sum()),'splits':int(sp.sum())})
    hashes[str(p.relative_to(root))]=sha(p)
    hashes[str((src/f'modelos/seed_{seed}.npz').relative_to(root))]=sha(src/f'modelos/seed_{seed}.npz')
gains=np.array(gains); splits=np.array(splits); scores=np.array(scores)
assert len(np.unique(ids))==164647
ensemble=scores.mean(axis=0); idx=np.lexsort((ids,-ensemble))[:11000]
blob=('\n'.join(map(str,np.sort(ids[idx].astype(np.int64))))+'\n').encode()
with zipfile.ZipFile(src/'C3_ENSEMBLE_ZULIP.zip') as z: original=z.read(delivery['ensemble']['file'])
assert hashlib.sha256(original).hexdigest()==delivery['ensemble']['sha256']
assert blob==original
fi=pd.DataFrame({'feature':features,'gain_pct':100*gains.mean(axis=0),'gain_sd_pct':100*gains.std(axis=0,ddof=1),'seeds_uso':(splits>0).sum(axis=0),'splits_promedio':splits.mean(axis=0)})
fi['bloque']=['RAW' if f in raw else catalog.loc[f,'block'] for f in features]
fi['fuentes']=[json.dumps([f]) if f in raw else catalog.loc[f,'sources'] for f in features]
fi['missing_agosto_catalogo']=[np.nan if f in raw else catalog.loc[f,'missing_fraction'] for f in features]
fi.sort_values('gain_pct',ascending=False).to_csv(out/'importancias_C3.csv',index=False)
block=fi.groupby('bloque').agg(variables=('feature','size'),gain_pct=('gain_pct','sum'),usadas_alguna_seed=('seeds_uso',lambda x:int((x>0).sum())),usadas_20_seeds=('seeds_uso',lambda x:int((x==20).sum()))).sort_values('gain_pct',ascending=False)
block.to_csv(out/'bloques_C3.csv')
pd.DataFrame(models).to_csv(out/'modelos_C3.csv',index=False)
pair=[len(x&y)/11000 for x,y in itertools.combinations(sets,2)]
ensset=set(idx.tolist())
stability={'interseccion_seed_seed_media':float(np.mean(pair)), 'interseccion_seed_seed_min':float(min(pair)), 'interseccion_seed_ensemble_media':float(np.mean([len(s&ensset)/11000 for s in sets])), 'seleccionados_todas_seeds':len(set.intersection(*sets)),'seleccionados_alguna_seed':len(set.union(*sets))}
families=json.loads((ours/'manifest.json').read_text())['families']
fammap={f:k for k,v in families.items() for f in v}
comparisons=[]; economic=[]; sources=[]
for exp in ['B0','B1','B2','B3','B4','B5']:
    imp=pd.read_csv(ours/f'resultados/{exp}/importance.csv')
    imp['gain_pct']=100*imp.gain/imp.gain.sum(); imp['familia']=imp.feature.map(fammap)
    for fam,d in imp.groupby('familia'):
        comparisons.append({'modelo':exp,'familia':fam,'variables':len(d),'usadas':int((d.split>0).sum()),'gain_pct':d.gain_pct.sum()})
    curve=pd.read_csv(ours/f'resultados/{exp}/curva_octubre.csv').set_index('contactos')
    for n in [10500,11000,11500]:
        gain=int(curve.loc[n,'ganancia']); hits=(gain+27500*n)/1100000
        assert hits==int(hits)
        economic.append({'modelo':exp,'contactos':n,'ganancia':gain,'aciertos_BAJA2':int(hits),'precision':hits/n})
    # Atribución descriptiva a fuentes: dividir gain de derivadas entre sus fuentes.
    for r in imp.itertuples():
        matches=[f for f in raw if r.feature==f or r.feature.startswith(f+'__')]
        # Nombres exactos del pipeline: buscar también sufijos utilizados.
        if not matches:
            matches=[f for f in raw if r.feature.startswith(f+'_')]
        if matches:
            f=max(matches,key=len); sources.append({'modelo':exp,'fuente':f,'gain_pct':r.gain_pct})
        else: sources.append({'modelo':exp,'fuente':'SIN_MAPEAR','gain_pct':r.gain_pct})
for r in fi.itertuples():
    fs=json.loads(r.fuentes)
    for f in fs: sources.append({'modelo':'C3','fuente':f,'gain_pct':r.gain_pct/len(fs)})
pd.DataFrame(comparisons).to_csv(out/'familias_B0_B5.csv',index=False)
econ=pd.DataFrame(economic);econ.to_csv(out/'ganancias_B0_B5_cortes_fijos.csv',index=False)
source=pd.DataFrame(sources).groupby(['fuente','modelo']).gain_pct.sum().unstack(fill_value=0)
source.to_csv(out/'fuentes_comparadas.csv')
summary={'run':plan['run'],'modelos':len(seeds),'features':len(features),'arboles_total':6000,'variables_usadas_alguna_seed':int((splits.sum(axis=0)>0).sum()),'variables_nunca_usadas':int((splits.sum(axis=0)==0).sum()),'variables_usadas_todas_seeds':int(((splits>0).sum(axis=0)==20).sum()),'esquema_y_orden_verificados':True,'modelos_checkpoint_sha_verificados':True,'envio_reconstruido_byte_a_byte':True,'envio_sha256':hashlib.sha256(blob).hexdigest(),'estabilidad':stability,'alcance':'Auditoria de artefactos; no reentrenamiento ni regeneracion de matrices originales','versions':{'lightgbm':lgb.__version__,'numpy':np.__version__,'pandas':pd.__version__}}
for p in src.glob('*.json'): hashes[str(p.relative_to(root))]=sha(p)
hashes[str((src/'catalogo_features.csv').relative_to(root))]=sha(src/'catalogo_features.csv')
for p in [ours/'manifest.json',*ours.glob('resultados/B*/importance.csv'),*ours.glob('resultados/B*/curva_octubre.csv')]:
    hashes[str(p.relative_to(root))]=sha(p)
(out/'verificacion.json').write_text(json.dumps(summary,indent=2))
(out/'insumos_sha256.json').write_text(json.dumps(hashes,indent=2))
print(json.dumps(summary,indent=2)); print(block.to_string());print(fi.nlargest(10,'gain_pct')[['feature','gain_pct']].to_string(index=False));print(econ[econ.contactos==11000].to_string(index=False))
