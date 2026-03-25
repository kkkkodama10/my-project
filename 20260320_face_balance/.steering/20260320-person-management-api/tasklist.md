# タスクリスト: 人物管理 API

## 🚨 タスク完全完了の原則
全てのタスクを`[x]`にすること。未完了タスクを残したまま作業を終了しない。

---

## フェーズ1: Pydantic スキーマ作成

- [x] `backend/app/schemas/__init__.py` を作成する
- [x] `backend/app/schemas/person.py` を作成する（PersonCreate, PersonResponse, PersonListResponse）

## フェーズ2: PersonService 作成

- [x] `backend/app/services/__init__.py` を作成する
- [x] `backend/app/services/person_service.py` を作成する（create, list_all, get, delete）

## フェーズ3: ルーター作成

- [x] `backend/app/routers/__init__.py` を作成する
- [x] `backend/app/routers/persons.py` を作成する（POST/GET/DELETE エンドポイント）

## フェーズ4: main.py にルーター登録

- [x] `backend/app/main.py` にルーター登録を追加する

## フェーズ5: 動作確認

- [x] `docker compose exec backend python -c "from app.routers.persons import router; print('OK')"` でインポートエラーがないことを確認する
- [x] `curl -X POST http://localhost:8000/api/persons -H 'Content-Type: application/json' -d '{"name":"太郎"}' | jq` で 201 が返ることを確認する
- [x] `curl http://localhost:8000/api/persons | jq` で一覧が返ることを確認する
- [x] `curl http://localhost:8000/api/persons/{id} | jq` で詳細が返ることを確認する
- [x] `curl -X DELETE http://localhost:8000/api/persons/{id}` で 204 が返ることを確認する
- [x] `curl http://localhost:8000/api/persons/{存在しないid}` で 404 が返ることを確認する

## フェーズ6: 振り返り記録

- [x] 実装後の振り返りを記録する

---

## 実装後の振り返り

### 実装完了日
2026-03-20

### 計画と実績の差分
- **計画通り**: 4エンドポイント（POST/GET一覧/GET詳細/DELETE）を設計書通りに実装
- **差分なし**: レイヤードアーキテクチャ（routers → services → models）を踏守
- **補足**: `PersonListResponse` の `image_count` は subquery + `func.coalesce` で効率的に取得（N+1クエリなし）

### 学んだこと
- Pydantic v2 では `from_orm=True` → `ConfigDict(from_attributes=True)` + `model_validate()` を使う
- SQLAlchemy の `func.coalesce` で LEFT OUTER JOIN 時の NULL（画像ゼロの人物）を 0 に変換できる
- FastAPI の `Depends(get_db)` + 非同期ジェネレータで DB セッション管理が自然に書ける
- インポートエラーは `docker compose exec backend python -c "from ..."` で手軽に確認できる

### バリデーター指摘対応
- `GET /api/persons/{id}` に `image_count` が欠如していた → `PersonResponse` に追加し、`get_with_count` メソッドを実装して対応（スペック requirements.md に準拠）
- `POST /api/persons` も `image_count: 0` を返すよう修正（新規作成直後は画像なし）
- `--reload` による自動リロードが効かなかったため `docker compose restart backend` で確認

### 次回への改善提案
- 画像アップロード API（次のフィーチャー）では `PersonService.get()` を再利用して 404 チェックを共有できる
- `PersonService` はシングルトン（`_service = PersonService()`）として使用しているが、DI コンテナが必要になったら `Depends(PersonService)` に移行する
- uvicorn `--reload` はファイルシステム監視であり、コンテナ内ではホットリロードの反映が遅延する場合がある。変更が反映されない場合は `docker compose restart backend` を使う
