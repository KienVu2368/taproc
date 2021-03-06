# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/01_pre-processing.ipynb (unless otherwise specified).

__all__ = ['tabular_proc', 'TBPreProc', 'skip_flds', 'remove_outlier', 'filter_outlier', 'boxnwhisker_value', 'subset',
           'fill_na', 'fix_missing', 'app_cat', 'dummies', 'scale_vars']

# Cell
from .utils import *
from pandas.api.types import is_string_dtype, is_numeric_dtype
from sklearn.preprocessing import StandardScaler
from sklearn_pandas import DataFrameMapper
import pdb

# Cell
#todo use dask, numba and do things in parallel
#immutation https://www.kaggle.com/dansbecker/handling-missing-values
#use sklearn pipeline and transformner??

def tabular_proc(df, y_fld = None, procs = None, ignore_flds=None):
    pp_outp = {}
    df = df.copy()

    if ignore_flds is not None:
        ignored_flds = df.loc[:, ignore_flds]
        df.drop(ignore_flds, axis=1, inplace=True)

    if y_fld is not None:
        if not is_numeric_dtype(df[y_fld]): df[y_fld] = df[y_fld].cat.codes
        y = df[y_fld].values
        df.drop(y_fld, axis=1, inplace=True)

    for f in procs: df = f(df, pp_outp)

    if ignore_flds is not None: df = pd.concat([df, ignored_flds], axis=1)

    if y_fld is not None: return [df, y, pp_outp]
    else: return [df, pp_outp]


class TBPreProc:
    def __init__(self, *args): self.args = args

    def __call__(self, df, pp_outp): return self.func(df, pp_outp, *self.args)

    @staticmethod
    def func(*args): None


class skip_flds(TBPreProc):
    @staticmethod
    def func(df, pp_outp, skip_flds): return df.drop(skip_flds, axis=1)


class remove_outlier(TBPreProc):
    @staticmethod
    def func(df, pp_outp):
        return filter_outlier(df, pp_outp['cons'])[0]


def filter_outlier(df, cons):
    mask =  np.full(df.shape[0], True)
    for v in to_iter(df[cons].values.T):
        Min, _, _, _, Max, _ = boxnwhisker_value(v)
        inlier = np.logical_and(v >= Min, v <= Max)
        mask = np.logical_and(mask, inlier)
    return df[mask], mask


def boxnwhisker_value(values):
    Median = np.median(values)
    Q1, Q3 = np.percentile(values, [25,75])
    IQR = Q3 - Q1
    Min, Max = Q1 - IQR*1.5, Q3 + IQR*1.5
    return max(Min, np.min(values)), Q1, Median, Q3, min(Max,np.max(values)), IQR


class subset(TBPreProc):
    @staticmethod
    def func(df, pp_outp, ss): return df.sample(ss)


class fill_na(TBPreProc):
    @staticmethod
    def func(df, pp_outp, na_dict = None):
        na_dict = {} if na_dict is None else na_dict.copy()
        na_dict_initial = na_dict.copy()
        for n,c in df.items(): na_dict = fix_missing(df, c, n, na_dict)
        if len(na_dict_initial.keys()) > 0:
            df.drop([a + '_na' for a in list(set(na_dict.keys()) - set(na_dict_initial.keys()))], axis=1, inplace=True)
        pp_outp['na_dict'] = na_dict
        return df


def fix_missing(df, col, name, na_dict):
    if is_numeric_dtype(col):
        if pd.isnull(col).sum() or (name in na_dict):
            df[name+'_na'] = pd.isnull(col)
            filler = na_dict[name] if name in na_dict else col.median()
            df[name] = col.fillna(filler)
            na_dict[name] = filler
    return na_dict


class app_cat(TBPreProc):
    @staticmethod
    def func(df, pp_outp, max_n_cat=15):
        cons = []
        for name, value in df.items():
            if is_numeric_dtype(value) and value.dtypes != np.bool:
                if value.nunique()<=max_n_cat:
                    if not np.array_equal(value.unique(), np.array([0, 1])): df[name] = value.astype('category').cat.as_ordered()
                else: cons.append(name)
            else:
                if value.nunique()>max_n_cat: df[name] = value.astype('category').cat.codes+1; cons.append(name)
                elif value.dtypes.name == 'object': df[name] = value.astype('category').cat.as_ordered()
                elif value.dtypes.name == 'category': df[name] = value.cat.as_ordered()
        pp_outp['cons'] = cons
        return df


class dummies(TBPreProc):
    @staticmethod
    def func(df, pp_outp):
        df = pd.get_dummies(df, dummy_na=True)
        if 'cons' in pp_outp.keys(): pp_outp['cats'] = [i for i in df.columns if i not in pp_outp['cons']]
        return df


class scale_vars(TBPreProc):
    @staticmethod
    def func(df, pp_outp, mapper = None):
        warnings.filterwarnings('ignore', category=sklearn.exceptions.DataConversionWarning)
        if mapper is None:
            map_f = [([n],StandardScaler()) for n in df.columns if is_numeric_dtype(df[n])]
            mapper = DataFrameMapper(map_f).fit(df)
        df[mapper.transformed_names_] = mapper.transform(df)
        pp_outp['mapper'] = mapper
        return df