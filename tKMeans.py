# v2020.03.20
# simplified version of multi classifier, tree structured KMeans
import numpy as np
import copy
import sklearn
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score

from mylearner import myLearner

class tKMeans():
    def __init__(self, learner, MSE=10, depth=2, min_percent=0.05, split_trial=10):
        self.data = {}
        self.MSE = MSE
        self.num_sample = -1
        self.num_class = -1
        self.learner = learner
        self.depth = depth
        self.min_percent = min_percent
        self.split_trial = split_trial
        self.trained = False
        self.pred= []
        
    def calMSE_(self, nX):
        nMSE = sklearn.metrics.pairwise.euclidean_distances(nX, np.mean(nX, axis=0).reshape(1, -1))
        return nMSE
        
    def check_split_(self):
        k = self.data.copy()
        key = k.keys()
        for k in key:
            if k == 'KMeans':
                continue
            if len(k) <= self.depth and \
                    self.data[k]['X'].shape[0] > self.num_sample and \
                    np.mean(self.calMSE_(self.data[k]['X'])) > self.MSE:
                kmeans = KMeans(n_clusters=2, n_jobs=10, init='k-means++').fit(self.data[k]['X'])
                pred = kmeans.predict(self.data[k]['X'])
                for i in range(2):
                    self.data[k+str(i)] = {'X':self.data[k]['X'][pred == i], 'Y':self.data[k]['Y'][pred == i]}
                self.data[k]['X'] = np.array([1])
                self.data[k]['Y'] = None
                self.data[k]['KMeans'] = kmeans
    
    def train_(self):
        for k in self.data.keys():
            if k == 'KMeans':
                continue
            if self.data[k]['X'].shape[0] < 2:
                continue
            reg = copy.deepcopy(myLearner(self.learner, self.num_class))
            reg.fit(self.data[k]['X'], self.data[k]['Y'])
            self.data[k]['learner'] = reg
            self.data[k]['X'] = np.array([1])
            self.data[k]['Y'] = None
            
    def fit(self, X, Y):
        self.num_class = np.unique(Y).shape[0]
        self.num_sample = X.shape[0] * self.min_percent
        kmeans = KMeans(n_clusters=2, n_jobs=10, init='k-means++').fit(X)
        pred = kmeans.predict(X)
        self.data['KMeans'] = kmeans
        for i in range(2):
            self.data[str(i)] = {'X':X[pred == i], 'Y':Y[pred == i]}
        for i in range(self.split_trial):
            self.check_split_()
        self.train_()
        self.trained = True

    def test_(self, key, X):
        if 'KMeans' in self.data[key].keys():
            pred = self.data[key]['KMeans'].predict(X)
            self.test_(key+str(pred[0]), X)
        elif 'learner' in self.data[key].keys():
            pred = self.data[key]['learner'].predict(X)
            self.pred.append(pred[0])
        else:
            assert (False), "Unknown error!"
        
    def predict(self, X):
        assert (self.trained == True), "Must call fit first!"
        self.pred = []
        for i in range(X.shape[0]):
            pred = self.data['KMeans'].predict(X[i].reshape(1,-1))
            self.test_(str(pred[0]), X[i].reshape(1,-1))
        self.pred = np.array(self.pred)
        return self.pred
    
    def score(self, X, Y):
        assert (self.trained == True), "Must call fit first!"
        pred = self.predict(X)
        return accuracy_score(Y, pred)
            
################################# Test #################################
if __name__ == "__main__":
    from sklearn.linear_model import LogisticRegression
    from sklearn import datasets
    from sklearn.model_selection import train_test_split
    print(" > This is a test example: ")
    digits = datasets.load_digits()
    X = digits.images.reshape((len(digits.images), -1))
    print(" input feature shape: %s"%str(X.shape))
    X_train, X_test, y_train, y_test = train_test_split(X, digits.target, test_size=0.2,  stratify=digits.target)
    
    clf = tKMeans(MSE=10, learner=LogisticRegression(random_state=0, solver='liblinear', multi_class='ovr', n_jobs=20, max_iter=1000))
    clf.fit(X_train, y_train)
    print(" --> train acc: %s"%str(clf.score(X_train, y_train)))
    print(" --> test acc.: %s"%str(clf.score(X_test, y_test)))
    print("------- DONE -------\n")