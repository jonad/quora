import pickle
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.metrics import accuracy_score, f1_score
from utils.utils import save_result



class XgbModel(object):
    ''' XGBoost model for sentence pair similarity.'''
    
    def __init__(self):
        self._model = None
        self._model_weights = None
        self._bestparams = {}
        
    @classmethod
    def from_weights(cls, model_weights):
        '''
        Alternate constructor for XgbModel class, create an Xgb model from pre-trained weights.
        :param model_weights:
        :return: An instance of XgbModel class.
        '''
        self = cls()
        self._model = pickle.load(open(model_weights, 'rb'))
        self._model_weights = model_weights
        return self
    
    @classmethod
    def from_params(cls, X_train, y_train,
                num_folds, param_grid,
                scoring, seed):
        '''
        Alternate constructor for XgbModel class, create an instance of XgbModel class with best parameters obtained
        after having performed k-folds cross-validation on 'param_grid'.
        :param X_train: Numpy ndarray,  input training data.
        :param y_train: Numpy ndarray, target data.
        :param num_folds: Integer, the number of folds for cross-validation.
        :param param_grid: Dictionary of cross-validation parameters.
        :param scoring: List of evaluation metrics.
        :param seed: Integer, a random seed.
        :return: An instance of XgbModel class.
        '''
        self = cls()
        _, self._bestparams = self.search_xgb_params(X_train, y_train,
                num_folds, param_grid,
                scoring, seed)
        self._model = xgb.XGBClassifier(nthread=-1, **self._bestparams)
        pickle.dump(self._model, open(self._model_weights, "wb"))
        return self
    
    def search_xgb_params(self, X_train, y_train,
                num_folds, param_grid,
                scoring, seed):
        '''
        Performs a k-folds cross-validation to find the best parameters from the parameter grid.
        :param X_train: Numpy ndarray, a list of training data.
        :param y_train: Numpy ndarray, a list of target data
        :param num_folds: Integer, the number of folds.
        :param param_grid: Dictionary of parameters to evaluate.
        :param scoring: String, Evaluation metric.
        :param seed: Integer, the seed.
        :return: Tuple of best score and best parameters.
        '''

        model = xgb.XGBClassifier(n_thread=-1)
        kfold = StratifiedKFold(n_splits=num_folds, shuffle=True, random_state=seed)
        grid_search = GridSearchCV(model, param_grid=param_grid, scoring=scoring, n_jobs=-1, verbose=10, cv=kfold)
        grid_result = grid_search.fit(X_train, y_train)
        best_params = grid_result.best_params_
        best_score = grid_result.best_score_
        results = []
        mean_test_score = grid_result.cv_results_['mean_test_score']
        mean_train_score = grid_result.cv_results_['mean_train_score']
        for i, elt in enumerate(grid_result.cv_results_['params']):
            elt['mean_test_score'] = mean_test_score[i]
            elt['mean_train_score'] = mean_train_score[i]
            results.append(elt)
        save_result('data/xgb_results.csv', results)
        return best_score, best_params
        
    def train(self, X_train, y_train):
        '''
        Trains the model.
        :param X_train: Numpy ndarray, list of training data.
        :param y_train: Numpy ndarray, list of target data.
        '''
        self._model.fit(X_train, y_train)
            
    
    def evaluate(self, y_test, predictions):
        '''
        Evaluates the model on the test data.
        :param y_test: Numpy ndaray, actual outputs.
        :param predictions: Numpy ndarray, the predictions generated by our model.
        :return: Accuracy and f1 score.
        '''
        accuracy = accuracy_score(y_test, predictions)
        f1 = f1_score(y_test, predictions)
        
        return accuracy, f1
    
    def predict(self, X):
        '''
        Performs predictions on new data.
        :param X: Numpy ndarray, input data to predict.
        :return: Float, similarity score.
        '''
        
        y_pred = self._model.predict(X)
        return y_pred
