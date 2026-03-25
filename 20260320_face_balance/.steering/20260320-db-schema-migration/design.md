# 設計書

## アーキテクチャ概要

SQLAlchemy 2.0 の宣言的マッピング（`DeclarativeBase`）を使用。全モデルが共通の `Base` を継承し、`alembic/env.py` の `target_metadata` に登録することでマイグレーション自動生成が可能になる。

## モデル設計方針

### Base クラス
```python
# app/models/__init__.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

### 共通カラム
- PK: `UUID` (`server_default=text("gen_random_uuid()")`)
- タイムスタンプ: `TIMESTAMP WITH TIME ZONE`（`server_default=text("now()")`）

### Enum の定義
Python の `enum.Enum` ではなく SQLAlchemy の `Enum` 型として定義し、PostgreSQL の ENUM 型として作成する。

```python
import enum

class ImageStatus(str, enum.Enum):
    uploaded = "uploaded"
    validating = "validating"
    analyzing = "analyzing"
    analyzed = "analyzed"
    error = "error"
```

### FLOAT[] の実装
PostgreSQL の `FLOAT[]` 型は SQLAlchemy で `ARRAY(Float)` として定義する。

```python
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Float

raw_vector: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=True)
```

### JSONB の実装
```python
from sqlalchemy.dialects.postgresql import JSONB

metadata_: Mapped[dict] = mapped_column("metadata", JSONB, server_default=text("'{}'::jsonb"))
```

## テーブル設計

### persons
```
id          UUID PK  gen_random_uuid()
name        VARCHAR(100) NOT NULL
created_at  TIMESTAMPTZ  now()
updated_at  TIMESTAMPTZ  now()
```

### images
```
id              UUID PK
person_id       UUID FK→persons CASCADE DELETE
storage_path    VARCHAR(500) NOT NULL
thumbnail_path  VARCHAR(500) NULL
status          ENUM(ImageStatus) NOT NULL DEFAULT 'uploaded'
metadata        JSONB DEFAULT '{}'
created_at      TIMESTAMPTZ now()
```

### features
```
id            UUID PK
image_id      UUID FK→images CASCADE DELETE  UNIQUE
model_version VARCHAR(50) NOT NULL
landmarks     JSONB NOT NULL
raw_vector    FLOAT[] NOT NULL
created_at    TIMESTAMPTZ now()
```

### person_features
```
id             UUID PK
person_id      UUID FK→persons CASCADE DELETE  UNIQUE
method         ENUM('average','single','median') NOT NULL DEFAULT 'average'
feature_vector FLOAT[] NOT NULL
image_count    INTEGER NOT NULL
created_at     TIMESTAMPTZ now()
```

### comparisons
```
id                UUID PK
person_a_id       UUID FK→persons CASCADE DELETE
person_b_id       UUID FK→persons CASCADE DELETE
similarity_method ENUM('cosine','euclidean','procrustes') NOT NULL DEFAULT 'cosine'
score             FLOAT NOT NULL
is_valid          BOOLEAN NOT NULL DEFAULT true
created_at        TIMESTAMPTZ now()
UNIQUE(person_a_id, person_b_id, similarity_method)
```

## マイグレーション方針

- `alembic revision --autogenerate` で自動生成した後、内容を確認・調整
- Enum 型は PostgreSQL の `CREATE TYPE` で作成される（Alembic が自動処理）
- `downgrade()` で全テーブルを `DROP TABLE` + `DROP TYPE` できることを確認

## ディレクトリ追加

```
backend/app/models/
├── __init__.py        # Base, 全モデル import
├── person.py
├── image.py
├── feature.py
├── person_feature.py
└── comparison.py

backend/alembic/versions/
└── 001_initial_schema.py
```
