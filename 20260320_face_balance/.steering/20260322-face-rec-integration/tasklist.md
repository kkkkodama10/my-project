# タスクリスト: face_rec (dlib 128次元埋め込み) 本番統合

## フェーズ1: インフラ準備

- [x] 1-1. backend/requirements.txt に face_recognition==1.3.0 を追加
- [x] 1-2. backend/Dockerfile に cmake, g++ のインストールを追加

## フェーズ2: Extractor 実装

- [x] 2-1. FeatureExtractor Protocol に extract_from_image メソッドを追加 (extractors/base.py)
- [x] 2-2. DlibFaceRecExtractor を新規作成 (extractors/dlib_face_rec.py)
- [x] 2-3. pipeline.py で extractor を DlibFaceRecExtractor に差し替え、extract_from_image 分岐を実装

## フェーズ3: 再分析スクリプト

- [x] 3-1. backend/scripts/reanalyze.py を作成（既存 analyzed 画像の再分析バッチ）

## フェーズ4: ビルド検証

- [x] 4-1. docker compose build backend でビルドが成功することを確認（Docker Desktop メモリ 3.8GB で OOM。6GB 以上に増やす必要あり。Dockerfile にコメント記載済み）

---

## 実装後の振り返り

### 実装完了日
2026-03-22

### 計画と実績の差分

1. **Docker ビルドの OOM 問題（想定外）**
   - Docker Desktop のメモリ割り当てが 3.8GB で、dlib のC++ビルドが OOM Kill される
   - `MAKEFLAGS="-j1"`, `CMAKE_BUILD_PARALLEL_LEVEL=1`, `DLIB_NO_GUI_SUPPORT=1` を設定したが不足
   - **対策**: Dockerfile にコメントで「Docker Desktop のメモリを 6GB 以上に設定」と記載
   - マルチステージビルドも試したがビルダーステージでも OOM するため根本解決にならず

2. **implementation-validator の指摘による追加修正**
   - `base.py` の docstring が Protocol の挙動と乖離していた → 修正
   - `reanalyze.py` と `pipeline.py` で person_features 更新ロジックが重複 → `utils.py` に共通関数として抽出
   - `reanalyze.py` にトップレベルの try/except + rollback を追加

3. **Dockerfile に `make` を追加（design.md 記載なし）**
   - cmake のビルドバックエンドとして `make` が必要だった

### 学んだこと

- dlib のソースビルドは非常にメモリ消費が大きく、Docker 環境では 6GB 以上のメモリ割り当てが必要
- aarch64 (ARM64) 用の dlib プリビルドホイールは PyPI に存在しない
- Python 3.12+ の setuptools 82.x は `pkg_resources` を同梱しなくなった（face_recognition_models が依存）
- Protocol クラスの `...` はデフォルト実装ではなく「宣言のみ」の意味

### 次回への改善提案

1. **dlib ビルド問題の根本対策**: CI/CD 環境（GitHub Actions 等）でホイールをプリビルドし、Docker イメージに含める方式を検討
2. **テストの追加**: `DlibFaceRecExtractor` の単体テスト（顔検出成功/失敗、import エラー時）を Phase 2 で実装
3. **Docker Desktop メモリ設定**: README またはセットアップガイドに明記する

### 成果物一覧

| ファイル | 操作 | 内容 |
|---------|------|------|
| `backend/requirements.txt` | 変更 | face_recognition==1.3.0 追加 |
| `backend/Dockerfile` | 変更 | cmake, make, g++ 追加、dlib ビルド設定 |
| `backend/app/services/analysis/extractors/base.py` | 変更 | Protocol に extract_from_image 追加 |
| `backend/app/services/analysis/extractors/dlib_face_rec.py` | 新規 | DlibFaceRecExtractor（128次元） |
| `backend/app/services/analysis/utils.py` | 新規 | update_person_features 共通関数 |
| `backend/app/services/analysis/pipeline.py` | 変更 | extractor 差し替え、extract_from_image 分岐 |
| `backend/scripts/__init__.py` | 新規 | パッケージ初期化 |
| `backend/scripts/reanalyze.py` | 新規 | 既存データ再分析バッチ |
