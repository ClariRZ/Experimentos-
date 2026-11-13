import importlib.util,json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('trace',ROOT/'herramientas/verificar_trazabilidad.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_missing_models_rejected(tmp_path):
 with pytest.raises(ValueError,match='Modelo ausente'):m.check_models(tmp_path)
def test_corrupted_model_rejected(tmp_path):
 p=tmp_path/'B0';p.mkdir();(p/'seed_101.txt').write_text('corrupto')
 with pytest.raises(ValueError,match='Modelo diferente'):m.check_models(tmp_path)
def test_reordered_columns_rejected(tmp_path):
 ref=json.loads((m.EXP/'resultados/octubre/protocolo_congelado_resumen.json').read_text())
 for v in ref['frozen'].values():v['columns']=['incorrecta']*v['n_columns']
 p=tmp_path/'protocolo.json';p.write_text(json.dumps(ref))
 with pytest.raises(ValueError,match='Orden/contenido columnas'):m.check_protocol(p)

def test_recovered_original_protocol_accepted():
 p=m.AUD/'protocolo_congelado_completo.json'
 assert m.sha(p)=='aa1ca2cf7eb7c7c5cfaf9c15c06d627ed60e23ce07c164da06d030677b26d479'
 assert m.check_protocol(p)=={'B0':652,'F1':1156,'F3':1030,'F4a':778,'F4b':1786}
