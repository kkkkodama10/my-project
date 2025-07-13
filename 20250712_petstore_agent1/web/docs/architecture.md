# アーキテクチャ概要

本プロジェクト **Pet Catalog** は、変更に強くテストしやすい設計を目指し、**ポート & アダプタ（ヘキサゴナル）アーキテクチャ** を採用します。ビジネスロジックを中心に据え、外部要素（DB・Web フレームワーク・UI など）への依存を最小限に抑えることで、機能追加・技術置換・自動テストを容易にします。

---

## 1. レイヤ構成

> **依存方向は常にドメイン層へ向かって収束**し、外側の層が内側の詳細を知ることはありません。

| レイヤ / 役割                   | フォルダ                  | 主な責務                                                                        |
| -------------------------- | --------------------- | --------------------------------------------------------------------------- |
| **Domain**                 | `app/domain/`         | *ビジネスルールの中心* となるエンティティ・値オブジェクト・ドメインサービスを保持。外部ライブラリに一切依存しない純粋 Python。        |
| **Ports**                  | `app/ports/`          | ドメインが外部とやり取りするための **抽象インタフェース**（例：`PetRepositoryPort`）。実装詳細を隠蔽し、テストダブルにも利用。 |
| **Adapters**               | `app/adapters/`       | Ports で宣言されたインタフェースを **具象実装**。例：SQLAlchemy による DB アクセス、外部 API クライアント。       |
| **Services (Application)** | `app/services/`       | ユースケース調整層。複数エンティティや外部アダプタを協調させ、トランザクション境界や権限制御を管理。                          |
| **Presentation**           | `app/presentation/`   | Flask ルート・WTForms・テンプレート。HTTP レスポンス/リクエストをアプリケーションサービスへブリッジ。                |
| **Infrastructure**         | `app/infrastructure/` | フレームワーク依存のクロスカット処理（DB セッション生成、設定ロード、Alembic／Flask 初期化など）。                   |

---

## 2. 依存ルール

```
Presentation  ─┐        
Adapters      ─┼────▶  Services ──▶  Domain
Infrastructure ┘            ▲
                            │
                      Ports (抽象)
```

* **内向きの依存**: 外側が内側を import する。逆は禁止。
* **インタフェースの所有権**: ドメイン側（Ports）が保持し、外側で具体実装（Adapters）を与える。

---

## 3. ディレクトリ構成（抜粋）

```text
pet_catalog/
├ app/
│ ├ domain/
│ │ └ models.py            # Pet エンティティ
│ ├ ports/
│ │ └ repository_port.py   # PetRepositoryPort
│ ├ adapters/
│ │ └ sql_alchemy_repo.py  # SQLAlchemyPetRepository
│ ├ services/
│ │ └ pet_service.py       # CRUD ユースケース
│ ├ presentation/
│ │ ├ routes.py            # Flask ルート
│ │ ├ forms.py             # WTForms
│ │ └ templates/
│ └ infrastructure/
│   └ db.py                # セッション/エンジン管理
```

> **テストの置き場所** : `tests/` 直下にレイヤ境界ごとのユニットテストを配置。ドメイン/サービスはスタブリポジトリで DB 依存を排除します。

---

## 4. データフロー例（新規ペット登録）

1. **Presentation**: `/` 画面下の HTML フォーム → POST `/`
2. **Services**: `PetService.create_pet()` を呼び出し入力値を検証
3. **Domain**: `Pet` エンティティ生成（必ずドメイン層で整合性を保証）
4. **Ports**: `PetRepositoryPort.add(pet)` を呼ぶ
5. **Adapters**: `SQLAlchemyPetRepository` が DB 挿入、コミット
6. 成功結果を Presentation 層へ返却し、リダイレクト／Flash

---

## 5. メリット

* **テスト容易**: ドメインとサービスをスタブで検証可能。DB コンテナなしでもユニットテストが動く。
* **技術入替え対応**: SQLAlchemy → async ORM 移行、Flask → FastAPI 置換などが最小影響。
* **明確な責任分離**: 変更理由が層ごとに閉じるため、コードベースが読みやすい。

---

## 6. 注意点 & ベストプラクティス

* ドメイン層は **絶対に外部ライブラリを import しない**。
* Ports には極力 **ビジネス語彙** を出す（DB 用語を避ける）。
* アダプタ実装は 1 つの Ports につき複数存在できる（例: ローカル DB / Mock / HTTP API）。
* トランザクション境界はサービス層でまとめ、一括コミット or ロールバックを管理。

---

## 7. 命名規約

### 7.1 クラス名

* **Controller**: `〇〇Controller`
* **Service**: `〇〇Service`
* **Mapper**: `〇〇Mapper`
* **Model**: テーブル名をキャメルケースにしたクラス名（例: `pets` → `Pet`）
* **DTO**: `〇〇Dto`
* **Form**: `〇〇Form`
* **Configuration**: `〇〇Config`
* **ViewHelper**: `〇〇ViewHelper`

### 7.2 メソッド名

**Controller**

| 操作   | メソッド名    |
| ---- | -------- |
| 一覧表示 | `index`  |
| 詳細表示 | `detail` |
| 作成   | `create` |
| 更新   | `update` |
| 削除   | `delete` |

**Service**

| 操作 | メソッド名      |
| -- | ---------- |
| 取得 | `get〇〇`    |
| 検索 | `search〇〇` |
| 作成 | `create〇〇` |
| 更新 | `update〇〇` |
| 削除 | `delete〇〇` |

---

## 8. 共通コンポーネントの使用規約

### 8.1 例外ハンドリング

* **業務例外**: `BusinessException` を使用
* **システム例外**: `SystemException` を使用
* すべての例外は `ExceptionHandler` で一元管理

### 8.2 トランザクション管理

* `@Transactional` アノテーションを利用
* トランザクション境界は **Service レイヤー**に設定

### 8.3 ログ出力

| レベル     | 用途      |
| ------- | ------- |
| `ERROR` | システムエラー |
| `WARN`  | 業務エラー   |
| `INFO`  | 操作ログ    |
| `DEBUG` | デバッグ情報  |

---

> **これで /web/docs/architecture.md は完成です。**
