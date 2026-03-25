# 要求仕様: 人物管理 API

## 概要

FaceGraph MVP の人物管理機能 (PRD §コア機能1) を REST API として実装する。

## 要求内容

### エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/api/persons` | 人物を新規作成 |
| GET | `/api/persons` | 人物一覧を取得 |
| GET | `/api/persons/{person_id}` | 人物詳細を取得 |
| DELETE | `/api/persons/{person_id}` | 人物を削除（連鎖削除） |

### 受け入れ条件（PRD より）

- [ ] 名前（最大100文字、1文字以上）を入力して人物を作成できる
- [ ] 人物一覧に各人物の画像枚数が含まれる
- [ ] 人物を削除すると、関連する画像・特徴量・比較結果が連鎖削除される（DB の CASCADE により自動）
- [ ] 存在しない人物へのアクセスは 404 を返す
- [ ] 名前が空または100文字超過の場合は 422 を返す

### レスポンス形式

**POST /api/persons リクエスト**:
```json
{ "name": "太郎" }
```
**レスポンス (201)**:
```json
{ "id": "uuid", "name": "太郎", "created_at": "2026-03-20T00:00:00Z", "updated_at": "2026-03-20T00:00:00Z" }
```

**GET /api/persons レスポンス (200)**:
```json
[
  { "id": "uuid", "name": "太郎", "image_count": 3, "created_at": "..." }
]
```

**GET /api/persons/{id} レスポンス (200)**:
```json
{ "id": "uuid", "name": "太郎", "image_count": 3, "created_at": "...", "updated_at": "..." }
```

**DELETE /api/persons/{id} レスポンス (204)**: No Content

## 対象範囲

- バックエンドのみ（フロントエンドは別機能で実装）
- `routers/persons.py`、`services/person_service.py`、`schemas/person.py` を新規作成
- `main.py` にルーターを登録
