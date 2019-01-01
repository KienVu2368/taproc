from .utils import *
import pandas as pd
import numpy as np
from pandas.api.types import is_string_dtype, is_numeric_dtype
from sklearn.preprocessing import StandardScaler
from sklearn_pandas import DataFrameMapper
import warnings
import sklearn
from sklearn.exceptions import DataConversionWarning
import pdb


#todo: only apply for some features


class TBStep:
    def __init__(self, **kargs): pass
    
    def fit(self, *args,**kargs): pass
    
    def transform(self, df, **kargs): pass
    
    def fit_transform(self, df):
        self.fit(df)
        return self.transform(df)


class noop_step(TBStep):
    def transform(self, df): return df


class TBTransform:
    def __init__(self, steps):
        self.steps = steps
        self.features = None
        
    def __repr__(self):
        return '\n'.join([str(pos) + ' - '+ str(step) for pos, step in enumerate(self.steps)])
    
    def fit(self, df):
        for step in self.steps: step.fit(df)
    
    def transform(self, df):
        df = df.copy()
        for step in self.steps: df = step.transform(df)
        if self.features is None:
            self.features = df.columns
            self.cons = []; self.cats = []
            for feature, value in df.items(): 
                if np.array_equal(np.sort(value.unique()), np.array([0, 1])) or np.array_equal(np.sort(value.unique()), np.array([0])): self.cats.append(feature) 
                else: self.cons.append(feature)
        return df
    
    def append(self, steps): self.steps.append(steps)
    
    def insert(self, index, steps): self.steps.insert(index, steps)
        
    def pop(self, n_pop): self.steps.pop(n_pop)


noop_transform = TBTransform([noop_step()])


class drop_features(TBStep):
    def __init__(self, features = None):
        self.features = features
        
    def __repr__(self):
        print_features = ', '.join(to_iter(self.features))
        return f'drop {print_features}'
    
    def fit(self, df, tfms_out): 
        tfms_out['features'] = [i for i in df.columns if i not in self.features]
        tfms_out['cons'] = [i for i in tfms_out['cons'] if i not in self.features]
    
    def transform(self, df): return df.drop(self.features, axis=1)


class remove_outlier(TBStep): 
    def __init__(self, features = None):
        self.features = features
        
    def __repr__(self):
        print_features = ', '.join(to_iter(self.features))
        return f'remove outlier of {print_features}'
        
    def fit(self, df):
        self.bw_dict = {}
        if self.features is None: self.features = df.columns
        mask =  np.full(df.shape[0], True)
        for feature, value in df[self.features].items():
            if is_numeric_dtype(value):
                self.bw_dict[feature] = {}
                Min, _, _, _, Max, _ = boxnwhisker_value(value)
                inlier = np.logical_and(value >= Min, value <= Max)
                mask = np.logical_and(mask, inlier)
        self.mask = mask
        
    def transform(self, df): return df[self.mask]


def boxnwhisker_value(values):
    Median = np.median(values)
    Q1, Q3 = np.percentile(values, [25,75])
    IQR = Q3 - Q1
    Min, Max = Q1 - IQR*1.5, Q3 + IQR*1.5
    return max(Min, np.min(values)), Q1, Median, Q3, min(Max,np.max(values)), IQR


class subset(TBStep): 
    def __init__(self, n_sample = None, ratio = 0.3):
        self.n_sample = n_sample
        self.ratio = ratio
        
    def __repr__(self): return f'select subset with {self.n_sample} samples'
    
    def fit(self, df):
        if self.n_sample is None: self.n_sample = self.ratio*df.shape[0]
        
    def transform(self, df): return df.sample(self.n_sample)


class app_cat(TBStep):
    def __init__(self, max_n_cat=15, features = None):
        self.max_n_cat = max_n_cat
        self.features = features
        
    def __repr__(self): return f'apply category with maximum number of distinct value is {self.max_n_cat}'
    
    def fit(self, df):
        if self.features is None: self.features = df.columns
        self.app_cat_dict = {}
        for feature, value in df[self.features].items():
            if is_numeric_dtype(value) and value.dtypes != np.bool:
                if value.nunique()<=self.max_n_cat:
                    if not np.array_equal(value.unique(), np.array([0, 1])): 
                        self.app_cat_dict[feature] = self.as_category_as_order
            else:
                if value.nunique()>self.max_n_cat: self.app_cat_dict[feature] = self.as_category_as_codes
                elif value.dtypes.name == 'object': self.app_cat_dict[feature] = self.as_category_as_order
                elif value.dtypes.name == 'category': self.app_cat_dict[feature] = self.cat_as_order
    
    @staticmethod
    def cat_as_order(x): return x.cat.as_ordered()
    
    @staticmethod
    def as_category_as_codes(x): return x.astype('category').cat.codes+1
    
    @staticmethod
    def as_category_as_order(x): return x.astype('category').cat.as_ordered()
        
    def transform(self, df):
        df = df.copy()
        for key in self.app_cat_dict.keys(): df[key] = self.app_cat_dict[key](df[key])
        return df


class dummies(TBStep):
    def __init__(self, dummy_na = True):
        self.dummy_na = dummy_na

    def __repr__(self): return 'get dummies'
        
    def transform(self, df):
        df = df.copy()
        df = pd.get_dummies(df, dummy_na=True)
        return df


class scale_vars(TBStep):
    def __init__(self, features = None):
        warnings.filterwarnings('ignore', category=sklearn.exceptions.DataConversionWarning)
        self.features= features
        
    def __repr__(self): return 'scale features'
    
    def fit(self, df):
        if self.features is None: self.features = df.columns        
        self.features = [i for i in self.features if is_numeric_dtype(df[i])]
        map_f = [([n],StandardScaler()) for n in df[self.features].columns]
        self.mapper = DataFrameMapper(map_f).fit(df[self.features].dropna(axis=0))
        
    def transform(self, df):
        df = df.copy()
        df[self.mapper.transformed_names_] = self.mapper.transform(df[self.features])
        return df


class fill_na(TBStep):
    def __init__(self, features = None):
        self.na_dict = {}
        self.features = features
        
    def __repr__(self):
        return 'fill na'    
    
    def fit(self, df):        
        if self.features is None: self.features = df.columns
        for feature in self.features:
            if is_numeric_dtype(df[feature].values):
                if pd.isnull(df[feature]).sum(): 
                    self.na_dict[feature] = df[feature].median()
    
    def transform(self, df):
        df = df.copy()
        for key in self.na_dict.keys(): df[key] = df[key].fillna(self.na_dict[key])
        return(df)


class select(TBStep):
    def __init__(self, features):
        self.features = features
        
    def __repr__(self):
        print_features = ', '.join(to_iter(self.features))
        return f'select {print_features}'
    
    def fit(self, df, tfms_out): 
        tfms_out['features'] = self.features
    
    def transform(self, df): return df[self.features]


class apply_function(TBStep):
    def __init__(self, function_dict): self.function_dict = function_dict
        
    def __repr__(self): 
        keys = ', '.join(self.function_dict.keys())
        return f'apply function for {keys}'
    
    def transform(self, df): 
        df = df.copy()
        for key in self.function_dict.keys(): df[key] = self.function_dict[key](df)
        return df