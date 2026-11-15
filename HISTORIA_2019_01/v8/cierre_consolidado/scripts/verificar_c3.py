"""Compare RR4 against the actual original C3 generator, without fitting."""
import argparse,hashlib,itertools,json,sys
from pathlib import Path
import numpy as np
from rr4 import rr4
p=argparse.ArgumentParser();p.add_argument('--c3-directory',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
sys.path.insert(0,str(a.c3_directory))
# Load unchanged pure helper definitions, avoiding unrelated pandas Panel dependency.
import ast,types
core=types.ModuleType('fe_core');core.np=np;core.FORBIDDEN={'numero_de_cliente','foto_mes','clase_ternaria','clase_binaria'}
tree=ast.parse((a.c3_directory/'fe_core.py').read_text())
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'flag','safe_divide'}]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(a.c3_directory/'fe_core.py'),'exec'),core.__dict__)
sys.modules['fe_core']=core
from fe_univariadas import generate_univariate
x=np.array(list(itertools.product([0.,-2.,5.,np.nan],repeat=4)))
class Panel:
 n=len(x)
 def get(self,name):return x[:,0]
 def lag(self,values,k):return x[:,k]
 def row_present(self,k):return np.ones(len(x),dtype=bool)
 def rank(self,values):return np.zeros(len(x))
ops=['meses_desde_no_cero_observado','racha_cero_observada','racha_no_cero_observada'];found={}
for name,values,meta in generate_univariate(Panel(),{'variable':'mtest','kind':'numeric'},{'lags':[1,2,3],'windows':[4]}):
 op=name.split('__')[-1]
 if op in ops:found[op]=values
 if len(found)==3:break
expected=np.column_stack([found[k] for k in ops]);np.testing.assert_equal(rr4(x),expected)
a.output.write_text(json.dumps({'cases':len(x),'status':'PASSED','reference_sha256':hashlib.sha256((a.c3_directory/'fe_univariadas.py').read_bytes()).hexdigest(),'method':'actual generate_univariate C3, maxk=3; 256 input combinations'},indent=2)+'\n')
print('C3 vs RR4: 256 cases passed')
