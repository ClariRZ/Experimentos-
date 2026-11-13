"""Audita evidencias sin entrenamiento. Verificar hashes no demuestra reproducción."""
import argparse,hashlib,json,platform,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/'experimento_2026-11-13'
AUD=ROOT/'auditoria_trazabilidad_2026-11-13'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(test,message):
 if not test:raise ValueError(message)
def check_models(folder):
 expected=json.loads((AUD/'modelos_sha256.json').read_text())
 for name,digest in expected.items():
  path=folder/name
  require(path.is_file(),f'Modelo ausente: {name}')
  require(sha(path)==digest,f'Modelo diferente: {name}')
 return len(expected)
def check_protocol(path):
 full=json.loads(path.read_text());ref=json.loads((EXP/'resultados/octubre/protocolo_congelado_resumen.json').read_text())
 require(full['dataset_sha256']==ref['dataset_sha256'],'Dataset diferente')
 require(set(full['frozen'])==set(ref['frozen']),'Brazos diferentes')
 for arm,v in ref['frozen'].items():
  got=full['frozen'][arm];cols=got['columns']
  require(len(cols)==v['n_columns'],f'Cantidad columnas: {arm}')
  digest=hashlib.sha256(json.dumps(cols,separators=(',',':')).encode()).hexdigest()
  require(digest==v['columns_sha256'],f'Orden/contenido columnas: {arm}')
  for k in ['models','proportion','august_result_sha256','august_ensemble_gain']:
   require(got[k]==v[k],f'Protocolo difiere: {arm}/{k}')
 return {arm:len(v['columns']) for arm,v in full['frozen'].items()}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--modelos',type=Path,help='Directorio private de la corrida original; no se copia ni publica')
 p.add_argument('--protocolo',type=Path,help='protocolo_congelado.json completo recuperado')
 p.add_argument('--dataset',type=Path,help='Archivo privado para verificar identidad, sin entrenar')
 a=p.parse_args();manifest=json.loads((EXP/'MANIFIESTO_SHA256.json').read_text())
 for name,digest in manifest.items():require(sha(EXP/name)==digest,f'Archivo diferente: {name}')
 result={'archivos_originales_verificados':len(manifest),'modelos_con_hash_registrado':25,'archivos_modelo_verificados':False,'protocolo_completo_verificado':False,'dataset_verificado':False,'reentrenamiento_independiente':False,'entorno_verificador':{'python':sys.version,'platform':platform.platform()}}
 if a.modelos:result['archivos_modelo_verificados']=check_models(a.modelos)
 if a.protocolo:result['protocolo_completo_verificado']=check_protocol(a.protocolo)
 if a.dataset:
  ref=json.loads((EXP/'configuracion/contrato_original.json').read_text())['data']['sha256']
  require(sha(a.dataset)==ref,'Dataset diferente');result['dataset_verificado']=True
 print(json.dumps(result,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
