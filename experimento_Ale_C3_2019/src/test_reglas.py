import pandas as pd,numpy as np
from comun import formulas,curve,policy,transfer
m=pd.DataFrame([['r','ticket','a','b'],['s','suma_tarjetas','a','b']],columns=['variable','familia','fuente_1','fuente_2'])
df=pd.DataFrame({'a':[10,-4,0,np.nan,4,np.inf],'b':[2,2,0,3,np.nan,2]})
x=formulas(df,m);np.testing.assert_array_equal(x[:,0],[5,-2,np.nan,np.nan,np.nan,np.nan]);np.testing.assert_array_equal(x[:,1],[12,-2,0,np.nan,np.nan,np.nan])
ids=np.array([3,1,2]);labels=np.array(['CONTINUA','BAJA+2','BAJA+1']);scores=np.array([.1,.9,.9]);g=curve(ids,labels,scores);np.testing.assert_array_equal(g,[0,1072500,1045000,1017500]);p=policy(ids,labels,scores);assert p['validation_k']==1 and transfer(p,10)==3
assert policy(ids,np.array(['CONTINUA']*3),scores)['validation_k']==0
print('Reglas verificadas: faltantes, signos, ceros, desempate, BAJA+1 sin premio y transferencia floor.')
