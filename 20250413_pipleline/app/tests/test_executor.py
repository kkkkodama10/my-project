import json
import pytest
from pathlib import Path
from src.executor import execute

def test_executor_runs(tmp_path: Path, capsys):
    # パイプライン設定用 JSON（テストパイプライン）を作成
    pipeline_config = {
        "test_pipeline": [
            {"type": "StandardScaler", "params": {}},
            {"type": "SelectKBest", "params": {"k": 2}},
            {"type": "SVC", "params": {"C": 1.0, "kernel": "linear"}}
        ]
    }
    pipeline_file = tmp_path / "pipelines.json"
    pipeline_file.write_text(json.dumps(pipeline_config))
    
    # データセット設定用 JSON（irisデータセット）を作成
    datasets_config = {
        "iris": {
            "type": "builtin",
            "loader": "load_iris",
            "params": {}
        }
    }
    datasets_file = tmp_path / "datasets.json"
    datasets_file.write_text(json.dumps(datasets_config))
    
    # execute 関数でパイプライン実行
    execute(str(pipeline_file), str(datasets_file), pipeline_key="test_pipeline", dataset_key="iris")
    
    # 出力に "Accuracy:" が含まれているかをチェック
    captured = capsys.readouterr().out
    assert "Accuracy:" in captured
