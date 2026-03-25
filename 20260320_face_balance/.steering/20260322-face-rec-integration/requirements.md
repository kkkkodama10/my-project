# 要求定義: face_rec (dlib 128次元埋め込み) 本番統合

## 背景

PoC で face_recognition ライブラリ (dlib 128次元埋め込み) が
現行の15次元手設計特徴量と比較して圧倒的に高い識別精度を示した。

- AUC: 0.824 → 0.952
- EER: 22.0% → 7.3%
- d': 1.30 → 2.18

## 要求

1. バックエンドの分析パイプラインで、特徴量抽出器を dlib 128次元埋め込みに切り替える
2. MediaPipe ランドマーク検出はランドマーク可視化用に維持する
3. DB スキーマは変更しない（FLOAT[] は次元数非依存）
4. 既存の DistanceRatioExtractor はロールバック用に残す
5. Docker 環境で dlib がビルド・実行できるようにする
6. 既存の analyzed 画像を新 extractor で再分析するスクリプトを提供する

## 参考ドキュメント

- `docs/new-features/face_rec_dlib_128dim.md` — 詳細設計・実装計画
- `poc/README.md` — PoC 結果と全アルゴリズム比較

## 制約

- API エンドポイント・フロントエンドの変更は不要
- ComparisonService のコサイン類似度計算ロジックは変更不要
- model_version で新旧の特徴量を区別する
