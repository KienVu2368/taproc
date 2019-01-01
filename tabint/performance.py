
import tabint
from tabint.utils import *
from tabint.dataset import *
from tabint.visual import *
from tabint.learner import *
from sklearn import metrics
from sklearn.metrics import *


class TBPerformace(BaseViz):
    @classmethod
    def from_learner(cls, learner, ds, **kargs):
        y_true = ds.y_val
        y_pred = learner.predict(ds.x_val)
        return y_true, y_pred

    @classmethod
    def from_series(cls, **kargs): return cls.calculate(y_true, y_pred, **kargs)


class actual_vs_predict(TBPerformace):
    def __init__(self, data, y_true, y_pred, df):
        super().__init__()
        self.df, self.y_true, self.y_pred = df, y_true, y_pred
        
    @classmethod
    def from_learner(cls, learner, ds):
        y_true, y_pred = TBPerformace.from_learner(learner, ds)
        return cls.from_series(y_true, y_pred, ds.x_val)

    @classmethod
    def from_series(cls, y_true, y_pred, df):
        data = cls.calculate(y_true, y_pred)
        return cls(data, y_true, y_pred, df)
    
    @staticmethod
    def calculate(y_true, y_pred):
        data = pd.DataFrame({'actual':y_true, 'predict':y_pred, 'mse': (y_true-y_pred)**2})
        return ResultDF(data, 'mse')
    
    def plot(self, hue = None, num = 100, **kagrs):
        if hue is not None: hue = self.df[hue]
        concat = np.concatenate([self.y_true, self.y_pred])
        plot_scatter(self.y_true, self.y_pred, xlabel='actual', ylabel='predict', hue=hue)
        plot_bisectrix(np.min(concat), np.max(concat), num)
        if hue is not None: plot_legend()


class ReceiverOperatingCharacteristic(TBPerformace):
    def __init__(self, data, fpr, tpr, roc_auc):
        super().__init__()
        self.fpr, self.tpr, self.roc_auc = fpr, tpr, roc_auc

    @classmethod
    def from_series(cls, y_true, y_pred):
        data, fpr, tpr, roc_auc = cls.calculate(y_true, y_pred)
        return cls(data, fpr, tpr, roc_auc)

    @staticmethod
    def calculate(y_true, y_pred):
        fpr, tpr, threshold = metrics.roc_curve(y_true, y_pred)
        roc_auc = metrics.auc(fpr, tpr)
        data = pd.DataFrame.from_dict({'threshold': threshold, 'tpr':tpr, 'fpr':fpr})
        return cls(data, fpr, tpr, roc_auc)
    
    def plot(self): plot_roc_curve(self.fpr, self.tpr, self.roc_auc)


class PrecisionRecall(TBPerformace):
    def __init__(self, precision, recall, threshold):
        self.precision,self.recall,self.threshold = precision, recall, threshold

    @classmethod
    def from_series(cls, y_true, y_pred):
        precision, recall, threshold = cls.calculate(y_true, y_pred)
        return cls(precision, recall, threshold)

    @staticmethod
    def calculate(y_true, y_pred): return precision_recall_curve(y_true, y_pred)

    def plot(self, **kwargs):
        plot_line([self.threshold]*2, 
                  [self.precision[:-1], self.recall[:-1]], 
                  ['precision', 'recall'], 
                  ["r--", "b-"], 
                  xlabel = "threshold", **kwargs)