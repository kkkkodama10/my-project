# 要求仕様: サムネイルの表示 & ランドマークの可視化

## 概要

2つの問題を解決する:

1. **サムネイル未表示の修正**: `ImageListResponse.thumbnail_path` が MinIO 内部キー（`thumbnails/...`）のままで、ブラウザがアクセスできない。API エンドポイントを介してサムネイルを配信する。

2. **ランドマーク可視化**: 解析済み画像に対して、MediaPipe が検出した468点のランドマーク（顔パーツ）と顔バウンディングボックスを元画像に重ねた画像を確認できる。

## 受け入れ条件

### サムネイル表示

- [ ] `GET /api/images/{id}/thumbnail` でサムネイル画像（JPEG）をストリーミング返却する
- [ ] `ImageListResponse.thumbnail_path` は `/api/images/{id}/thumbnail` の形式の URL を返す（MinIO キーを直接返さない）
- [ ] サムネイルが存在しない場合は `thumbnail_path: null` のまま
- [ ] フロントエンドの人物詳細ページでサムネイルが表示される

### ランドマーク可視化

- [ ] `GET /api/images/{id}/landmarks` で元画像 + ランドマーク描画済み JPEG を返す
- [ ] 468点のランドマークを緑の小さな点で描画する
- [ ] 顔バウンディングボックスを赤い矩形で描画する（ランドマークの min/max xy から算出）
- [ ] 顔が未検出の場合（status が error 等）も元画像を返す（"No face detected" テキストを重ねる）
- [ ] フロントエンドの人物詳細ページ、各画像カードに「ランドマーク確認」ボタンを追加する
- [ ] ボタンクリックで新しいタブに可視化画像が開く
- [ ] analyzed 済みの画像でのみボタンを表示する（error/uploading 中は非表示）

## 非機能要件

- 描画ロジックは `services/analysis/visualizer.py` に分離する
- エンドポイントは同期処理（CPU-bound）なので `run_in_executor` は不要（MVP規模では許容）
- 返却する画像は JPEG（品質85）
