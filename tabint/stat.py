import random
import matplotlib.pyplot as plt
import seaborn as sns
import tabint
from .utils import *

class Permutation_test:
    def __init__(self, x, y, func = np.mean, num_samples = 10000):
        self.x, self.y = list_to_np_array(x), list_to_np_array(y)
        self.nx, self.ny = len(x), len(y)
        self.xy = np.hstack([x,y])
        self.func = func
        self.num_samples = num_samples
        self.ground_truth = self.compute_difference(False)
        self.permutation_result = self.run_permutation()
        self.p_value_calculation()
    
    def random_shuffle(self, random_shuffle = True):
        if random_shuffle: np.random.shuffle(self.xy)
        return self.xy[:self.nx], self.xy[-self.ny:]
        
    def compute_difference(self, random_shuffle = True):
        x_p, y_p = self.random_shuffle(random_shuffle = random_shuffle)
        return self.func(x_p) - self.func(y_p)
    
    def run_permutation(self): 
        ground_truth = []
        for i in range(self.num_samples): ground_truth.append(self.compute_difference())
        return list_to_np_array(ground_truth)
    
    def p_value_calculation(self):
        self.p_value_one_side = (len(np.where(self.permutation_result <= self.ground_truth)[0]) if self.ground_truth < 0 else len(np.where(self.permutation_result >= self.ground_truth)[0]))/self.num_samples
        self.p_value_two_sides = len(np.where(np.abs(self.permutation_result) >= np.abs(self.ground_truth))[0])/self.num_samples
            
    def distribution_plot(self):
        #pdb.set_trace()
        permutation_result_pos = self.permutation_result[self.permutation_result >= 0]
        permutation_result_neg = np.abs(self.permutation_result[self.permutation_result < 0])
        
        print("Ground truth:", '%.2f' % self.ground_truth, '\n')
        print("P-value one sided:", self.p_value_one_side, '\n')
        print("P-value two sided:", self.p_value_two_sides)

        sns.distplot(permutation_result_pos, hist = False, kde_kws={"shade": True}, label = "pos")
        sns.distplot(permutation_result_neg, hist = False, kde_kws={"shade": True}, label = "neg")
        plt.axvline(np.abs(self.ground_truth), 0, 1, c = "Blue" if self.ground_truth >= 0 else "Orange")
        plt.legend(bbox_to_anchor=(1.04,1), loc="upper left")
        plt.show()   
