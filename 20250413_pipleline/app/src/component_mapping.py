# component_mapping.py

from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, Normalizer, OneHotEncoder
from sklearn.decomposition import PCA, TruncatedSVD, NMF
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.feature_selection import SelectKBest, f_classif, SelectFromModel, VarianceThreshold, RFE
from sklearn.preprocessing import PolynomialFeatures

# Preprocessors：前処理を担当
PREPROCESSORS = {
    "StandardScaler": StandardScaler,
    "MinMaxScaler": MinMaxScaler,
    "RobustScaler": RobustScaler,
    "Normalizer": Normalizer,
    "OneHotEncoder": OneHotEncoder,
}

# Transformers：特徴量変換（次元削減など）
TRANSFORMERS = {
    "PCA": PCA,
    "TruncatedSVD": TruncatedSVD,
    "NMF": NMF,
    "PolynomialFeatures": PolynomialFeatures,
}

# Feature Selectors：特徴量選択
FEATURE_SELECTORS = {
    "SelectKBest": lambda **params: SelectKBest(score_func=f_classif, **params),
    "SelectFromModel": SelectFromModel,
    "VarianceThreshold": VarianceThreshold,
    "RFE": RFE,
}

# Estimators：学習器/分類器
ESTIMATORS = {
    "RandomForestClassifier": RandomForestClassifier,
    "SVC": SVC,
    "LogisticRegression": LogisticRegression,
    "DecisionTreeClassifier": DecisionTreeClassifier,
    "KNeighborsClassifier": KNeighborsClassifier,
    "GaussianNB": GaussianNB,
    "GradientBoostingClassifier": GradientBoostingClassifier,
    "ExtraTreesClassifier": ExtraTreesClassifier,
}

# カテゴリごとに分割したものを統合して一つのマッピングを作成
COMPONENT_MAPPING = {**PREPROCESSORS, **TRANSFORMERS, **FEATURE_SELECTORS, **ESTIMATORS}
