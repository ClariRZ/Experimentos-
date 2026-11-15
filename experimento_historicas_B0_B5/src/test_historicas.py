import unittest
import numpy as np
import pandas as pd
from historicas import exact_lags, summaries, ratio, labels, gain

class HistoricalTests(unittest.TestCase):
    def test_calendar_and_clients(self):
        f=pd.DataFrame({'numero_de_cliente':[1,1,1,2], 'foto_mes':[201912,202001,202003,202003], 'x':[10.,20.,50.,99.]})
        l1,l2=exact_lags(f,['x'])
        self.assertEqual(l1.x.iloc[1],10)
        self.assertTrue(np.isnan(l1.x.iloc[2]))
        self.assertEqual(l2.x.iloc[2],20)
        self.assertTrue(np.isnan(l1.x.iloc[3]))
        self.assertEqual(f.x.iloc[2]-l2.x.iloc[2],30)
    def test_summaries(self):
        a=np.array([3.,5.,1.,3.]);b=np.array([2.,5.,2.,np.nan]);c=np.array([1.,5.,3.,1.])
        avg,slope=summaries(a,b,c)
        np.testing.assert_allclose(avg,[2,5,2,2])
        np.testing.assert_allclose(slope,[1,0,-1,1])
        avg,slope=summaries(np.array([1.]),np.array([np.nan]),np.array([np.nan]))
        self.assertTrue(np.isnan(avg[0]) and np.isnan(slope[0]))
    def test_ratios(self):
        r=ratio(np.array([1.,0.,-4.,np.nan]),np.array([0.,2.,2.,1.]))
        np.testing.assert_allclose(r,[np.nan,0,-2,np.nan],equal_nan=True)
    def test_future_invariance(self):
        f=pd.DataFrame({'numero_de_cliente':[1]*4,'foto_mes':[201901,201902,201903,201904],'x':[1.,2.,3.,4.]})
        before=exact_lags(f,['x'])
        f.loc[3,'x']=99999
        after=exact_lags(f,['x'])
        for a,b in zip(before,after):pd.testing.assert_frame_equal(a,b)
    def test_labels_censor(self):
        f=pd.DataFrame({'numero_de_cliente':[1,1,1,2,2,3], 'foto_mes':[201910,201911,201912,201910,201911,201910]})
        self.assertEqual(list(labels(f)),['CONTINUA',None,None,'BAJA+2','BAJA+1','BAJA+1'])
    def test_gain(self):
        self.assertEqual(gain(['BAJA+2'])[0],1072500)
        self.assertEqual(gain(['BAJA+1'])[0],-27500)
        self.assertEqual(gain(['CONTINUA'])[0],-27500)
        self.assertEqual(gain(['BAJA+2','BAJA+1','CONTINUA']).sum(),1017500)
        self.assertEqual(gain([]).sum(),0)

if __name__=='__main__':unittest.main()
