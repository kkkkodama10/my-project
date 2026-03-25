# タスクリスト: 顔解析パイプライン（BackgroundTasks + MediaPipe）

## フェーズ1: services/analysis/ ディレクトリ・基底クラス

- [x] `services/analysis/__init__.py` 作成（空）
- [x] `services/analysis/detectors/__init__.py` 作成（空）
- [x] `services/analysis/extractors/__init__.py` 作成（空）
- [x] `services/analysis/detectors/base.py` 作成（LandmarkDetector Protocol + LandmarkResult dataclass）
- [x] `services/analysis/extractors/base.py` 作成（FeatureExtractor Protocol）

## フェーズ2: MediaPipe ランドマーク検出器

- [x] `services/analysis/detectors/mediapipe_detector.py` 作成（MediaPipeLandmarkDetector 実装）

## フェーズ3: distance_ratio 特徴量抽出器（15次元）

- [x] `services/analysis/extractors/distance_ratio.py` 作成（DistanceRatioExtractor 実装）
  - [x] 距離特徴量 5次元（鼻長・口幅・顔幅・眉間距離・目口垂直距離 ÷ IPD）
  - [x] 角度特徴量 3次元（目頭-鼻尖-目頭・口角-鼻尖-口角・眉端-目頭-鼻根）
  - [x] 比率特徴量 7次元（顔縦横比・目幅/顔幅・鼻長/顔高・口幅/IPD・三分割比上中下）

## フェーズ4: AnalysisPipeline メインフロー

- [x] `services/analysis/pipeline.py` 作成
  - [x] `process(image_id)` 非同期メソッド
  - [x] ステータス遷移: uploaded → validating → analyzing → analyzed / error
  - [x] MinIO から画像ダウンロード → MediaPipe で顔数チェック
  - [x] 顔0個 or 2個以上 → error + metadata.error メッセージ設定
  - [x] 顔1個 → ランドマーク検出 → 特徴量抽出 → features テーブル保存
  - [x] person_features 再計算・upsert（既存画像の平均統合）
  - [x] その人物を含む comparisons を is_valid=False に更新
  - [x] 背景タスク用に AsyncSessionLocal を直接使用（新規セッション）

## フェーズ5: MinIO download() メソッド追加

- [x] `storage/minio_client.py` に `download(key) -> bytes` メソッド追加

## フェーズ6: routers/images.py 更新

- [x] `routers/images.py` に BackgroundTasks 引数追加
- [x] アップロード後に `pipeline.process(image.id)` をバックグラウンドタスクとして登録
- [x] `services/image_service.py` の NOTE コメント削除

## フェーズ7: 動作確認

- [x] Docker Compose 再ビルド（mediapipe 依存追加確認）— Dockerfile に libgl1/libglib2.0-0 を追加
- [x] 画像アップロード後に status が analyzed に遷移することを確認
- [x] 顔なし画像で status=error + metadata.error を確認
- [x] features テーブルに 15次元ベクトルが保存されることを確認

## フェーズ8: 振り返り

- [x] tasklist.md に振り返り記録

---

## 実装後の振り返り

**実装完了日**: 2026-03-20

**計画と実績の差分**:
- `Dockerfile` への `libgl1`/`libglib2.0-0` 追加が当初計画になかったが必須だった（python:3.11-slim に libGL がない）
- `_FACE_MESH` をモジュールレベルのグローバルとして初期化（プロセス起動時に1回のみロード）— スレッドセーフ性を確認済み（static_image_mode=True は並行処理可能）
- `mediapipe_detector.py` で `max_num_faces=2` を設定して「2個以上」を検出可能に

**学んだこと**:
- `python:3.11-slim` ベースでは `libgl1`（OpenGL）と `libglib2.0-0`（GLib）が不足しており、mediapipe/OpenCV のインポートで失敗する
- PostgreSQL の `INSERT ... ON CONFLICT DO UPDATE`（upsert）は SQLAlchemy で `pg_insert().on_conflict_do_update()` を使う
- BackgroundTasks では FastAPI のリクエストセッションが終了しているため `AsyncSessionLocal()` で新規セッションを開く必要がある

**実装検証後の修正**:
- `pipeline.py`: DB更新順序を「features → person_features → comparisons → analyzed」の1コミットに修正（ガイドライン準拠）
- `pipeline.py`: `db: Any` → `db: AsyncSession` に型修正
- `mediapipe_detector.py`: `_FACE_MESH` をモジュールレベルからクラス `__init__` に移動し `threading.Lock` を追加
- `distance_ratio.py`: 未使用変数 `face_aspect`（デッドコード）を削除

**次回への改善提案**:
- `_FACE_MESH` のグローバルインスタンスはワーカープロセス数が増えると各プロセスでモデルをロードする（メモリ使用増）。将来的にはモデルのロードを遅延化するか専用ワーカーへの委譲を検討
- 類似度計算 API では `person_features.feature_vector` を使ってコサイン類似度を算出する
