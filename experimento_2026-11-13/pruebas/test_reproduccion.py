import ast, importlib.util, json
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('repro',ROOT/'scripts/reproducir.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
def test_metric_discrepancy_stops_verification():
    with pytest.raises(AssertionError):r.same({'auc':.9},{'auc':.91})
    r.same({'auc':.9,'seconds':1},{'auc':.9,'seconds':999})
def test_portable_preserves_feature_and_training_logic():
    old=ast.parse((ROOT/'originales/ejecutar_completa_vm.py').read_text())
    new=ast.parse((ROOT/'scripts/entrenar_desde_cero.py').read_text())
    def funcs(tree):
        return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
    assert funcs(old)==funcs(new)
    def methods(tree):
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Run')
        return {n.name:ast.dump(n,include_attributes=False) for n in cls.body if isinstance(n,ast.FunctionDef) and n.name!='__init__'}
    assert methods(old)==methods(new)
