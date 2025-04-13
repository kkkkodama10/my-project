# pipeline_loader.py

import json
from sklearn.pipeline import Pipeline

from .component_mapping import COMPONENT_MAPPING  # 別ファイルからインポート

def load_pipeline(config_path, pipeline_key):
    """
    JSON設定ファイルから指定キーのパイプラインを構築し、
    最終ステップがEstimator（predictメソッドを持つクラス）であることを検証する。
    """
    with open(config_path, "r") as f:
        config = json.load(f)

    if pipeline_key not in config:
        raise ValueError(f"Pipeline '{pipeline_key}' not found in configuration.")

    steps = []
    for step_cfg in config[pipeline_key]:
        cls_name = step_cfg["type"]
        cls_params = step_cfg.get("params", {})
        if cls_name not in COMPONENT_MAPPING:
            raise ValueError(f"Unknown component: '{cls_name}'")
        component_builder = COMPONENT_MAPPING[cls_name]
        component = component_builder(**cls_params) if callable(component_builder) else component_builder(**cls_params)
        steps.append((cls_name, component))

    # 最終ステップが predict メソッドを持っているかチェック
    if not hasattr(steps[-1][1], "predict"):
        raise ValueError("The final component in the pipeline must be an Estimator (with a 'predict' method).")

    return Pipeline(steps)
