import pandas as pd
import numpy as np
from .eda import *
from .plot import *
from .utils import *
import lightgbm as lgb
import pickle


##psedou labeling??
#denoising autoencoder?? https://www.kaggle.com/c/porto-seguro-safe-driver-prediction/discussion/44629
##function do drop and check feature
##time dependency check https://youtu.be/3jl2h9hSRvc?t=48m50s

class BaseLearner:
    def __init__(self): None
        #model
        #data
        #crit
        #lrs learning rate
        #callback?

    def fit(self): None

    def predict(self): None

    def load(self): None
        
    def save(self): None


class LGBLearner:
    def __init__(self, fn = 'LGB_Model.pkl'):
        self.fn = fn
        self.score = []

    def fit(self, params, x_trn, y_trn, x_val, y_val, ctn = False, save = True, early_stopping_rounds=100, verbose_eval = 100, **kargs):
        self.md = None 
        if ctn: self.load()
        lgb_trn, lgb_val = self.build_ds(x_trn, y_trn, x_val, y_val)
        self.md = lgb.train(params = params,
                            train_set = lgb_trn,
                            valid_sets = [lgb_trn, lgb_val],
                            init_model = self.md, 
                            early_stopping_rounds = early_stopping_rounds, 
                            verbose_eval = verbose_eval, **kargs)

        self.score.append(self.md.best_score)
        if save: self.save()
    
    @staticmethod
    def build_ds(x_trn, y_trn, x_val, y_val):
        lgb_trn = lgb.Dataset(x_trn, y_trn)
        lgb_val = lgb.Dataset(x_val, y_val, free_raw_data=False, reference=lgb_trn)
        return lgb_trn, lgb_val
    
    def predict(self, df, **kargs): return self.md.predict(df, **kargs)

    def load(self): 
        with open(self.fn, 'rb') as fin: self.md = pickle.load(fin)
        
    def save(self, fn = None):
        fn = isNone(fn, self.fn)
        with open(fn, 'wb') as fout: pickle.dump(self.md, fout)

