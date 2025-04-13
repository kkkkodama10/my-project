#!/usr/bin/env python3
import argparse
from src.executor import execute

def main():
    parser = argparse.ArgumentParser(
        description="Execute a machine learning pipeline defined in JSON configurations."
    )
    parser.add_argument(
        "--pipeline",
        type=str,
        default="default_pipeline",
        help="The key of the pipeline configuration to run (as specified in configs/pipelines.json)."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="iris",
        help="The key of the dataset configuration to load (as specified in configs/datasets.json)."
    )
    args = parser.parse_args()

    # パイプラインとデータセット設定ファイルのパス（プロジェクトルートからの相対パス）
    pipeline_config_path = "configs/pipelines.json"
    dataset_config_path = "configs/datasets.json"

    # executor.py 内の execute 関数でパイプラインの構築と実行を行う
    execute(pipeline_config_path, dataset_config_path, pipeline_key=args.pipeline, dataset_key=args.dataset)

if __name__ == "__main__":
    main()