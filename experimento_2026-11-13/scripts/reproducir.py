"""Entrada por etapas. Nunca inicia entrenamiento sin subcomando explicito."""
import argparse, hashlib, json, math, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ARMS=['B0','F1','F3','F4a','F4b']
def read(p): return json.loads(p.read_text())
def same(a,b,path=''):
    if isinstance(b,dict):
        for k,v in b.items():
            if k not in ['seconds']: same(a[k],v,path+'/'+k)
    elif isinstance(b,list):
        assert len(a)==len(b),path
        for i,(x,y) in enumerate(zip(a,b)):same(x,y,path+'/'+str(i))
    elif isinstance(b,(int,float)) and not isinstance(b,bool):
        assert math.isclose(a,b,rel_tol=0,abs_tol=1e-8),(path,a,b)
    else: assert a==b,(path,a,b)
def verify_august(prior):
    frozen=read(ROOT/'resultados/octubre/protocolo_congelado_resumen.json')['frozen']
    registry=read(prior/'feature_manifest.json')
    for arm in ARMS:
        same(read(prior/arm/'best.json'),read(ROOT/'resultados/agosto'/arm/'best.json'),arm+'/best')
        same(read(prior/arm/'result.json'),read(ROOT/'resultados/agosto'/arm/'result.json'),arm+'/result')
        cols=registry[arm]['columns']
        assert hashlib.sha256(json.dumps(cols,separators=(',',':')).encode()).hexdigest()==frozen[arm]['columns_sha256'],arm+'/columns'
    identity=read(prior/'data_identity.json'); expected=read(ROOT/'resultados/agosto/data_identity.json')
    for key in ['n_train','n_valid','train_keys_sha256','valid_ids_sha256']:same(identity[key],expected[key],key)
    print('AGOSTO_REPRODUCIDO: resultados, hiperparametros, filas y orden de columnas coinciden.')
def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='stage',required=True)
    sub.add_parser('verificar-archivos')
    q=sub.add_parser('entrenar');q.add_argument('--dataset',type=Path,required=True);q.add_argument('--salida',type=Path,required=True);q.add_argument('--horas',type=float,default=16)
    q=sub.add_parser('verificar-agosto');q.add_argument('--corrida',type=Path,required=True)
    q=sub.add_parser('octubre');q.add_argument('--dataset',type=Path,required=True);q.add_argument('--corrida',type=Path,required=True);q.add_argument('--salida',type=Path,required=True)
    q=sub.add_parser('verificar-octubre');q.add_argument('--corrida',type=Path,required=True)
    a=parser.parse_args()
    if a.stage=='verificar-archivos':
        for name,digest in read(ROOT/'MANIFIESTO_SHA256.json').items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
        print('ARCHIVOS_VERIFICADOS');return
    if a.stage=='verificar-agosto':verify_august(a.corrida);return
    if a.stage=='verificar-octubre':
        got=read(a.corrida/'FINAL.json');ref=read(ROOT/'resultados/octubre/FINAL.json')
        for key in ['n_clients','baja2','new_fits','results','comparisons']:same(got[key],ref[key],key)
        print('OCTUBRE_REPRODUCIDO');return
    if a.stage=='entrenar':
        assert 0<a.horas<=16,'Usar un limite entre 0 y 16 horas'
        deadline=time.time()+3600*a.horas
        cmd=[sys.executable,str(ROOT/'scripts/entrenar_desde_cero.py'),'--config',str(ROOT/'configuracion/contrato_original.json'),'--dataset',str(a.dataset.resolve()),'--output',str(a.salida.resolve()),'--deadline',str(deadline)]
        subprocess.run(cmd,check=True,timeout=3600*a.horas);verify_august(a.salida);return
    verify_august(a.corrida)
    expected=a.corrida/'agosto_verificado_para_octubre.json'
    expected.write_text(json.dumps({arm:read(a.corrida/arm/'result.json') for arm in ARMS}))
    cmd=[sys.executable,str(ROOT/'scripts/evaluar_octubre.py'),'--root',str(ROOT),'--prior',str(a.corrida.resolve()),'--dataset',str(a.dataset.resolve()),'--output',str(a.salida.resolve()),'--expected',str(expected.resolve())]
    subprocess.run(cmd,check=True,timeout=2700)
if __name__=='__main__':main()
