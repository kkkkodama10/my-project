#!/bin/bash

# スクリプトが存在するディレクトリを取得
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# API仕様ファイル（スクリプトのあるディレクトリを基準に設定）
SPEC_FILE="${SCRIPT_DIR}/api-spec.yaml"

# 出力ディレクトリ（スクリプトのあるディレクトリを基準に設定）
OUTPUT_DIR="${SCRIPT_DIR}/../backend"

# -d でディレクトリの存在をチェック
if [ ! -d "$OUTPUT_DIR" ]; then
  mkdir -p "$OUTPUT_DIR"
  echo "Directory '$OUTPUT_DIR' created."
else
  echo "Directory '$OUTPUT_DIR' already exists."
fi

# OpenAPI Generatorのコマンド
GENERATOR="python-flask"

# エラー時にスクリプトを停止
set -e

# メッセージ表示
echo "Generating Python Flask server from $SPEC_FILE..."

# コード生成
openapi-generator-cli generate -i "$SPEC_FILE" -g "$GENERATOR" -o "$OUTPUT_DIR" -p packageName=base

# 成功メッセージ
echo "Server generated successfully in $OUTPUT_DIR"
