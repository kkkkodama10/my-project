import json
import pytest
from pathlib import Path
import numpy as np
from src.dataset_loader import load_dataset

def test_load_builtin_dataset(tmp_path: Path):
    # built-in（iris）データセットを使用するテスト用 JSON を作成
    datasets_config = {
        "iris": {
            "type": "builtin",
            "loader": "load_iris",
            "params": {}
        }
    }
    config_file = tmp_path / "datasets.json"
    config_file.write_text(json.dumps(datasets_config))
    
    X_train, X_test, y_train, y_test = load_dataset(str(config_file), "iris", test_size=0.3, random_state=42)
    
    # データが読み込まれていることを確認（サイズチェック）
    assert X_train.shape[0] > 0
    assert X_test.shape[0] > 0
    # 少なくとも1つのクラスが存在することを確認
    assert np.unique(y_train).size > 1

def test_invalid_dataset_key(tmp_path: Path):
    datasets_config = {
        "iris": {
            "type": "builtin",
            "loader": "load_iris",
            "params": {}
        }
    }
    config_file = tmp_path / "datasets.json"
    config_file.write_text(json.dumps(datasets_config))
    
    with pytest.raises(ValueError, match="Dataset 'nonexistent' not found"):
        load_dataset(str(config_file), "nonexistent")        
