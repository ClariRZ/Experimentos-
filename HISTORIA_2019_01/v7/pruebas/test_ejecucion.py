import tempfile
import unittest
from pathlib import Path
import sys
import numpy as np
import polars as pl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from ejecutar_v7 import history,materialize,payoff,bootstrap_joint,ARMS

class V7Tests(unittest.TestCase):
    def test_frozen_features_reproduce_august_without_october_labels(self):
        rng=np.random.default_rng(43)
        data=[]
        for client in range(1,60):
            for month in range(201901,201911):
                if client==1 and month==201902:continue
                data.append({'numero_de_cliente':client,'foto_mes':month,
                    'x':float(rng.normal(10,5)), 'z':float(rng.uniform(0,100))})
        df=pl.DataFrame(data)
        cfg={'data':{'history_sources':['x','z'],'broken_masks':{}}}
        with tempfile.TemporaryDirectory() as temp:
            dev=Path(temp)/'dev';dev.mkdir();final=Path(temp)/'final';final.mkdir()
            h,raw=history(df.filter(pl.col('foto_mes')<=201908),cfg,[201904,201905,201906,201908])
            reg=materialize(h,raw,cfg,dev,lambda:None)
            hh,rr=history(df,cfg,[201908,201910]);materialize(hh,rr,cfg,final,lambda:None,reg)
            for arm in ARMS:
                a=pl.read_parquet(dev/f'{arm}.parquet').filter(pl.col('foto_mes')==201908)
                b=pl.read_parquet(final/f'{arm}.parquet').filter(pl.col('foto_mes')==201908)
                self.assertTrue(a.equals(b),arm)
                self.assertTrue(set(reg['B0']['columns'])<=set(reg[arm]['columns']),arm)
            self.assertTrue(set(reg['R4']['columns'])<=set(reg['H_T']['columns']))
            self.assertTrue(set(reg['R4']['columns'])<=set(reg['H_S']['columns']))

    def test_common_budget_identity_and_tie(self):
        ids=np.array([2,1,3]);y=np.array([0,1,0]);p=np.array([.5,.5,.2])
        r,d=payoff(ids,p,y,2)
        self.assertEqual(r,{'contacts':2,'hits':1,'gain':1045000})
        self.assertEqual(int(d.sum()),r['gain'])
        self.assertEqual(payoff(ids,p,y,0)[0]['gain'],0)

    def test_joint_bootstrap_preserves_paired_relations(self):
        x=np.array([[0,0],[2,-2],[-3,3],[2,-2]],dtype=np.int64)
        a=bootstrap_joint(x,2000,31);b=bootstrap_joint(x,2000,31)
        self.assertTrue(np.array_equal(a,b))
        self.assertTrue(np.all(a[:,0]==-a[:,1]))
        self.assertTrue(np.array_equal(bootstrap_joint(np.zeros((8,3),dtype=np.int64),4,1),np.zeros((4,3))))

    def test_feature_generator_rejects_labels(self):
        with self.assertRaises(ValueError):history(pl.DataFrame({'clase_ternaria':['BAJA+2']}),{},[])

if __name__=='__main__':unittest.main()
