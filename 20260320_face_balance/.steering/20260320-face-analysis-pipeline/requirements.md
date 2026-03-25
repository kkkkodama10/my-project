# 要求仕様: 顔解析パイプライン（BackgroundTasks + MediaPipe）

## 概要

FaceGraph MVP の顔解析パイプライン（PRD §コア機能3・4・5）を実装する。
画像アップロード後にバックグラウンドで自動実行され、ランドマーク検出・特徴量抽出・person_features 統合を行う。

## 受け入れ条件（PRD より）

- [ ] 画像アップロード後、FastAPI の BackgroundTasks で自動的に解析パイプラインが起動する
- [ ] ステータス遷移: `uploaded → validating → analyzing → analyzed`（エラー時は `error`）
- [ ] 顔が 0 個: `status = "error"`, `metadata.error = "顔が検出されませんでした"`
- [ ] 顔が 2 個以上: `status = "error"`, `metadata.error = "複数の顔が検出されました。1人だけ写っている画像を使用してください"`
- [ ] MediaPipe Face Mesh で 468 点のランドマーク座標を検出する
- [ ] IPD 正規化距離比率ベクトルを算出し `features` テーブルに保存する
- [ ] 解析完了後、`person_features`（複数画像の平均統合）を更新する
- [ ] 解析完了後、その人物を含む `comparisons` を `is_valid = false` に更新する

## 特徴量定義（15次元）

- **距離特徴量（5）**: 鼻の長さ・口幅・顔幅・眉間距離・目口垂直距離 ÷ IPD
- **角度特徴量（3）**: 目頭-鼻尖-目頭・口角-鼻尖-口角・眉端-目頭-鼻根
- **比率特徴量（7）**: 顔縦横比・目幅/顔幅・鼻長/顔高・口幅/IPD・三分割比（上中下）
- model_version: `"mediapipe_v0.10_distance_ratio_v1"`
