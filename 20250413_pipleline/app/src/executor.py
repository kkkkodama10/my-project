# src/executor.py
from .pipeline_loader import load_pipeline
from .dataset_loader import load_dataset
from sklearn.metrics import accuracy_score

def execute(pipeline_cfg_path, dataset_cfg_path, pipeline_key, dataset_key):
    # データセットを読み込み
    X_train, X_test, y_train, y_test = load_dataset(dataset_cfg_path, dataset_key)

    # パイプラインを構築
    pipeline = load_pipeline(pipeline_cfg_path, pipeline_key)

    # 学習
    pipeline.fit(X_train, y_train)

    # 予測
    predictions = pipeline.predict(X_test)

    # 評価
    accuracy = accuracy_score(y_test, predictions)
    print(f"Dataset: {dataset_key}, Pipeline: {pipeline_key}, Accuracy: {accuracy:.4f}")
