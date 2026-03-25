# 設計: 顔解析パイプライン

## ディレクトリ構成

```
backend/app/services/analysis/
├── __init__.py
├── pipeline.py                  # AnalysisPipeline メインフロー
├── detectors/
│   ├── __init__.py
│   ├── base.py                  # LandmarkDetector Protocol + LandmarkResult
│   └── mediapipe_detector.py    # MediaPipe Face Mesh 実装
└── extractors/
    ├── __init__.py
    ├── base.py                  # FeatureExtractor Protocol
    └── distance_ratio.py        # IPD 正規化距離比率特徴量（15次元）
```

## 変更ファイル

- `storage/minio_client.py`: `download(key) -> bytes` メソッド追加
- `routers/images.py`: BackgroundTasks 引数追加・pipeline.process 起動
- `services/image_service.py`: NOTEコメント削除

## ランドマークインデックス（MediaPipe Face Mesh 468点）

| 部位 | インデックス |
|------|-------------|
| 左目外角（IPD基準L） | 33 |
| 右目外角（IPD基準R） | 263 |
| 鼻先 | 4 |
| 鼻根 | 168 |
| 鼻下 | 2 |
| 口左角 | 61 |
| 口右角 | 291 |
| 左頬 | 234 |
| 右頬 | 454 |
| 額 | 10 |
| 顎 | 152 |
| 左眉内端 | 55 |
| 右眉内端 | 285 |
| 左眉外端 | 105 |

## パイプライン実行フロー

```
uploaded → validating（MinIOからDL・顔数チェック）
    → 0個 or 2個以上 → error + metadata.error
    → 1個 → analyzing（ランドマーク検出・特徴量抽出）
              → features 保存 → analyzed
              → person_features 再統合
              → comparisons 無効化
```

背景タスクは新規 AsyncSession で実行（リクエストセッションは終了済みのため）。

## 特徴量計算（distance_ratio.py）- 15次元

座標は正規化済み (0-1)。IPD = euclidean_2d(33, 263) で除算。

**距離 (5)**: 鼻長・口幅・顔幅・眉間距離・目口垂直距離 ÷ IPD
**角度 (3)**: 左目外角-鼻先-右目外角・口左-鼻先-口右・左眉外端-左目外角-鼻根
**比率 (7)**: 顔縦横比・目幅/顔幅・鼻長/顔高・口幅/IPD・上/中/下顔比率
