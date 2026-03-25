# 設計: 人物管理 API

## ディレクトリ構成（新規作成ファイル）

```
backend/app/
├── schemas/
│   ├── __init__.py          # 新規
│   └── person.py            # 新規: Pydantic リクエスト/レスポンス
├── services/
│   ├── __init__.py          # 新規
│   └── person_service.py    # 新規: PersonService
├── routers/
│   ├── __init__.py          # 新規
│   └── persons.py           # 新規: /api/persons エンドポイント
└── main.py                  # 更新: ルーター登録追加
```

## Pydantic スキーマ設計 (schemas/person.py)

```python
class PersonCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class PersonResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PersonListResponse(BaseModel):
    id: str
    name: str
    image_count: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

## PersonService 設計 (services/person_service.py)

```python
class PersonService:
    async def create(self, db: AsyncSession, name: str) -> Person
    async def list_all(self, db: AsyncSession) -> list[tuple[Person, int]]
    async def get(self, db: AsyncSession, person_id: str) -> Person
    async def delete(self, db: AsyncSession, person_id: str) -> None
```

- `list_all`: subquery または scalar_subquery で image_count を効率的に取得
- `get`: `db.get()` + 404 raise
- `delete`: `db.delete()` + commit（CASCADE は DB 側で実行）

## ルーター設計 (routers/persons.py)

- prefix: `/api/persons`
- tags: `["persons"]`
- 依存注入: `db: AsyncSession = Depends(get_db)`
- status_code 明示: 201 (create), 200 (list/get), 204 (delete)

## main.py 変更

```python
from app.routers import persons
app.include_router(persons.router)
```

## アーキテクチャ方針

- routers は薄く: バリデーション → service 呼び出し → レスポンス整形のみ
- ビジネスロジックはすべて PersonService に集約
- 404 エラーは service 層で raise（router では再 raise しない）
- `from_attributes=True` で SQLAlchemy モデルから直接 Pydantic モデルへ変換
