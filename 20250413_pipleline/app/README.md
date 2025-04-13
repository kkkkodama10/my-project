# 📦 ML Pipeline Runner

これは scikit-learn ベースの柔軟な機械学習パイプライン実行フレームワークです。  
パイプライン構成やデータセットは JSON で定義されており、CLI から簡単に切り替えて実行できます。

---

## 💠 セットアップ

### 1. 仮想環境作成と有効化

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

## 🚀 実行方法（main.py）

### 例：SVMパイプライン × Irisデータセット

```bash
python main.py --pipeline svm_pipeline --dataset iris
```

### 引数

| 引数         | 説明                                  | デフォルト           |
|--------------|---------------------------------------|----------------------|
| `--pipeline` | JSONで定義されたパイプライン名              | `"default_pipeline"` |
| `--dataset`  | JSONで定義されたデータセット名              | `"iris"`             |

### 結果出力例

```bash
Pipeline 'svm_pipeline' on Dataset 'iris': Accuracy = 0.9667, F1 Score = 0.9652
```

---

## 🧪 テストの実行

プロジェクトルートで以下を実行：

```bash
pytest
```

または特定のテストだけ：

```bash
pytest tests/test_pipeline_loader.py
```

---

## 📁 ディレクトリ構成

```
project/
├── configs/              # JSON形式の設定ファイル（パイプライン・データセット）
│   ├── pipelines.json
│   └── datasets.json
├── src/                  # 実装モジュール群
│   ├── component_mapping.py
│   ├── pipeline_loader.py
│   ├── dataset_loader.py
│   └── executor.py
├── tests/                # pytestによる自動テスト
│   ├── test_pipeline_loader.py
│   ├── test_dataset_loader.py
│   └── test_executor.py
└── main.py               # エントリーポイント（CLI実行）
```
