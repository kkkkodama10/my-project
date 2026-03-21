# 技術スタック構成図（Pet Catalog）

```mermaid
flowchart TD
    subgraph Presentation[Presentation層]
        A1[Flaskルート<br>WTForms<br>Jinja2テンプレート<br>Bootstrap]
    end

    subgraph Services[Services層]
        B1[PetService<br>（ユースケース調整）]
    end

    subgraph Domain[Domain層]
        C1[Petエンティティ<br>値オブジェクト]
    end

    subgraph Ports[Ports層]
        D1[PetRepositoryPort<br>（抽象リポジトリ）]
    end

    subgraph Adapters[Adapters層]
        E1[SQLAlchemyPetRepository<br>（DB実装）]
    end

    subgraph Infrastructure[Infrastructure層]
        F1[DBセッション管理<br>設定ロード<br>Flask/Alembic初期化]
    end

    A1 --> B1
    B1 --> D1
    D1 <--> E1
    E1 --> F1
    B1 --> C1

    E1 -.->|DBアクセス| G1[(PostgreSQL<br>またはSQLite)]
    F1 -.->|設定/初期化| H1[(OS/環境変数)]
```

---

## レイヤ対応ディレクトリ

| レイヤ             | フォルダ                  | 主な責務例                       |
|--------------------|---------------------------|----------------------------------|
| Presentation       | `app/presentation/`       | Flaskルート・WTForms・テンプレート|
| Services           | `app/services/`           | ユースケース調整・トランザクション|
| Domain             | `app/domain/`             | エンティティ・値オブジェクト      |
| Ports              | `app/ports/`              | 抽象リポジトリ                   |
| Adapters           | `app/adapters/`           | DB実装・外部APIクライアント      |
| Infrastructure     | `app/infrastructure/`     | DBセッション管理・
