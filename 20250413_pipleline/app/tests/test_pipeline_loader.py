import json
import pytest
from pathlib import Path
from src.pipeline_loader import load_pipeline

def test_load_valid_pipeline(tmp_path: Path):
    # 有効なパイプライン設定のテスト用 JSON を作成
    pipeline_config = {
        "test_pipeline": [
            {"type": "StandardScaler", "params": {}},
            {"type": "SelectKBest", "params": {"k": 2}},
            {"type": "SVC", "params": {"C": 1.0, "kernel": "linear"}}
        ]
    }
    config_file = tmp_path / "pipelines.json"
    config_file.write_text(json.dumps(pipeline_config))
    
    pipeline = load_pipeline(str(config_file), "test_pipeline")
    # 最後のステップがpredictメソッドを持つか確認（Estimatorであるか）
    assert hasattr(pipeline.steps[-1][1], "predict")

def test_invalid_component(tmp_path: Path):
    # 存在しないコンポーネントを指定した場合のエラー確認
    pipeline_config = {
        "test_pipeline": [
            {"type": "NonExistentComponent", "params": {}},
            {"type": "SVC", "params": {"C": 1.0, "kernel": "linear"}}
        ]
    }
    config_file = tmp_path / "pipelines.json"
    config_file.write_text(json.dumps(pipeline_config))
    
    with pytest.raises(ValueError, match="Unknown component"):
        load_pipeline(str(config_file), "test_pipeline")

def test_missing_pipeline_key(tmp_path: Path):
    # 指定したキーが存在しない場合のエラー確認
    pipeline_config = {
        "some_other_pipeline": [
            {"type": "StandardScaler", "params": {}},
            {"type": "SVC", "params": {"C": 1.0, "kernel": "linear"}}
        ]
    }
    config_file = tmp_path / "pipelines.json"
    config_file.write_text(json.dumps(pipeline_config))
    
    with pytest.raises(ValueError, match="Pipeline 'test_pipeline' not found"):
        load_pipeline(str(config_file), "test_pipeline")
