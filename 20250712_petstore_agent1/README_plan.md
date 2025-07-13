**1. 概要**  
本システムは、ペット情報の登録・一覧表示・詳細表示・編集・削除を行うCRUD Webアプリです。Flaskを用いたサーバーサイドレンダリング、PostgreSQLによるデータ永続化、BootstrapによるUI構築を行います。  
ユーザーはWeb画面からペット情報を操作でき、各操作はバリデーション・エラーハンドリング・CSRF保護を備えます。API経由でのCRUDもサポートします。

---

**2. クラス図**  
```marmaid
classDiagram
namespace web.src.models {
    class Pet {
        +int id
        +str name
        +str species
        +str sex
        +datetime created_at
        +datetime updated_at
    }
}

namespace web.src.forms {
    class PetForm {
        +StringField name
        +StringField species
        +SelectField sex
        +validate()
    }
}

namespace web.src.routes {
    class PetRoutes {
        +list_pets()
        +create_pet()
        +get_pet(id)
        +edit_pet(id)
        +delete_pet(id)
    }
}

namespace web.src.templates {
    class index.html
    class detail.html
    class edit.html
    class confirm_delete.html
}

PetRoutes --> Pet : uses
PetRoutes --> PetForm : uses
PetRoutes --> index.html : renders
PetRoutes --> detail.html : renders
PetRoutes --> edit.html : renders
PetRoutes --> confirm_delete.html : renders
```

---

**3. シーケンス図**  

**(A) 一覧表示イベント**  
```marmaid
sequenceDiagram
participant User
participant PetRoutes
participant Pet
participant index.html

User ->> PetRoutes: (1) GET /
PetRoutes ->> Pet: (2) query all pets (order by created_at desc)
Pet -->> PetRoutes: (3) ペット一覧
PetRoutes ->> index.html: (4) render (pets, PetForm)
index.html -->> User: (5) 一覧画面表示
```

**(B) 新規登録イベント**  
```marmaid
sequenceDiagram
participant User
participant PetRoutes
participant PetForm
participant Pet
participant index.html

User ->> PetRoutes: (1) POST /
PetRoutes ->> PetForm: (2) validate_on_submit()
alt バリデーションOK
    PetRoutes ->> Pet: (3) create & commit
    Pet -->> PetRoutes: (4) 新規ペット
    PetRoutes ->> User: (5) redirect /
else バリデーションNG
    PetRoutes ->> index.html: (6) render (errors)
    index.html -->> User: (7) エラー表示
end
```

**(C) 詳細表示イベント**  
```marmaid
sequenceDiagram
participant User
participant PetRoutes
participant Pet
participant detail.html

User ->> PetRoutes: (1) GET /pets/<id>
PetRoutes ->> Pet: (2) get by id
Pet -->> PetRoutes: (3) ペット情報
PetRoutes ->> detail.html: (4) render (pet)
detail.html -->> User: (5) 詳細画面表示
```

**(D) 編集イベント**  
```marmaid
sequenceDiagram
participant User
participant PetRoutes
participant PetForm
participant Pet
participant edit.html

User ->> PetRoutes: (1) GET /pets/<id>/edit
PetRoutes ->> Pet: (2) get by id
Pet -->> PetRoutes: (3) ペット情報
PetRoutes ->> PetForm: (4) populate form
PetRoutes ->> edit.html: (5) render (form, pet)
edit.html -->> User: (6) 編集画面表示

User ->> PetRoutes: (7) POST /pets/<id>/edit
PetRoutes ->> PetForm: (8) validate_on_submit()
alt バリデーションOK
    PetRoutes ->> Pet: (9) update & commit
    Pet -->> PetRoutes: (10) 更新済みペット
    PetRoutes ->> User: (11) redirect /pets/<id>
else バリデーションNG
    PetRoutes ->> edit.html: (12) render (errors)
    edit.html -->> User: (13) エラー表示
end
```

**(E) 削除イベント**  
```marmaid
sequenceDiagram
participant User
participant PetRoutes
participant Pet
participant confirm_delete.html

User ->> PetRoutes: (1) GET /pets/<id>/delete
PetRoutes ->> Pet: (2) get by id
Pet -->> PetRoutes: (3) ペット情報
PetRoutes ->> confirm_delete.html: (4) render (pet)
confirm_delete.html -->> User: (5) 削除確認画面

User ->> PetRoutes: (6) POST /pets/<id>/delete
PetRoutes ->> Pet: (7) delete & commit
Pet -->> PetRoutes: (8) 削除完了
PetRoutes ->> User: (9) redirect /
```

---

**4. 実装計画**  

---

### ～一覧表示イベント: 
- **ステップ 1: Petモデルの作成**  
  - **編集対象ファイル:** `web/src/models/pet.py`  
  - **目的:** ペット情報をDBで管理できるようにする  
  - **内容:** SQLAlchemyでPetモデルを定義（id, name, species, sex, created_at, updated_at）  
  - **活用するクラス・メソッド:**  
    - `db.Model`（Flask-SQLAlchemy）  
  - **ポイント:** バリデーションや制約（NOT NULL, 文字数）をDBレベルでも設定

- **ステップ 2: 一覧取得ルートの実装**  
  - **編集対象ファイル:** `web/src/routes/pet.py`  
  - **編集対象のメソッド:** `list_pets()`  
  - **目的:** 一覧画面で全ペットを表示  
  - **内容:** Petモデルから全件取得し、created_at降順でテンプレートへ渡す  
  - **活用するクラス・メソッド:**  
    - `Pet.query.order_by(Pet.created_at.desc()).all()`  
  - **ポイント:** ページ下部に新規登録フォームも渡す

- **ステップ 3: 一覧テンプレートの作成**  
  - **編集対象ファイル:** `web/src/templates/index.html`  
  - **目的:** 一覧画面のUIを構築  
  - **内容:**  
    - テーブル（名前／種別／性別／登録日／操作ボタン）  
    - 各行に「詳細」「編集」「削除」ボタン  
    - 下部に新規登録フォーム  
  - **ポイント:** Bootstrapで見やすく配置

---

### ～新規登録イベント: 
- **ステップ 1: PetFormの作成**  
  - **編集対象ファイル:** `web/src/forms/pet_form.py`  
  - **目的:** 入力バリデーションを実装  
  - **内容:**  
    - name: StringField, 必須, 最大50文字  
    - species: StringField, 必須, 最大30文字  
    - sex: SelectField, 必須, 選択肢（male/female/unknown）  
  - **活用するクラス・メソッド:**  
    - `FlaskForm`, `wtforms.validators`  
  - **ポイント:** エラー時は各項目下に赤字でメッセージ

- **ステップ 2: 登録ルートの実装**  
  - **編集対象ファイル:** `web/src/routes/pet.py`  
  - **編集対象のメソッド:** `create_pet()`  
  - **目的:** 新規登録処理  
  - **内容:**  
    - POST時にPetFormでバリデーション  
    - OKならPetモデルを作成しDB保存  
    - NGならエラーをテンプレートに渡す  
  - **活用するクラス・メソッド:**  
    - `PetForm.validate_on_submit()`  
    - `db.session.add()` / `db.session.commit()`  
  - **ポイント:** 成功時はFlashメッセージとリダイレクト

- **ステップ 3: 一覧テンプレートでフォーム表示**  
  - **編集対象ファイル:** `web/src/templates/index.html`  
  - **目的:** 新規登録フォームのUI  
  - **内容:**  
    - ラベル例・プレースホルダー例を明記  
    - エラー時は該当項目下に赤字表示  
  - **ポイント:** Bootstrapのform-controlを利用

---

### ～詳細表示イベント: 
- **ステップ 1: 詳細ルートの実装**  
  - **編集対象ファイル:** `web/src/routes/pet.py`  
  - **編集対象のメソッド:** `get_pet(id)`  
  - **目的:** ペット詳細画面の表示  
  - **内容:**  
    - idでPetを取得し、テンプレートへ渡す  
    - 見つからない場合は404  
  - **活用するクラス・メソッド:**  
    - `Pet.query.get_or_404(id)`  
  - **ポイント:** 詳細・編集・削除・戻るボタンを配置

- **ステップ 2: 詳細テンプレートの作成**  
  - **編集対象ファイル:** `web/src/templates/detail.html`  
  - **目的:** 詳細画面のUI  
  - **内容:**  
    - ペット情報表示  
    - 「編集」「削除」「戻る」ボタン  
  - **ポイント:** Bootstrapで整形

---

### ～編集イベント: 
- **ステップ 1: 編集ルートの実装**  
  - **編集対象ファイル:** `web/src/routes/pet.py`  
  - **編集対象のメソッド:** `edit_pet(id)`  
  - **目的:** 編集画面の表示・更新処理  
  - **内容:**  
    - GET時: idでPet取得し、フォームに値をセット  
    - POST時: バリデーションOKなら更新・保存  
    - NGならエラー表示  
  - **活用するクラス・メソッド:**  
    - `PetForm(obj=pet)`  
    - `db.session.commit()`  
  - **ポイント:** プリフィル済みフォーム、戻るボタン

- **ステップ 2: 編集テンプレートの作成**  
  - **編集対象ファイル:** `web/src/templates/edit.html`  
  - **目的:** 編集画面のUI  
  - **内容:**  
    - プリフィル済みフォーム  
    - 「更新」「戻る」ボタン  
    - エラー時は各項目下に赤字表示  
  - **ポイント:** Bootstrapで整形

---

### ～削除イベント: 
- **ステップ 1: 削除確認ルートの実装**  
  - **編集対象ファイル:** `web/src/routes/pet.py`  
  - **編集対象のメソッド:** `delete_pet(id)`  
  - **目的:** 削除確認画面の表示・削除処理  
  - **内容:**  
    - GET時: 削除確認画面を表示  
    - POST時: CSRF保護の上で削除し、一覧へリダイレクト  
  - **活用するクラス・メソッド:**  
    - `db.session.delete()` / `db.session.commit()`  
  - **ポイント:** 「削除」「キャンセル」ボタン

- **ステップ 2: 削除確認テンプレートの作成**  
  - **編集対象ファイル:** `web/src/templates/confirm_delete.html`  
  - **目的:** 削除確認画面のUI  
  - **内容:**  
    - ペット情報表示  
    - 「削除」「キャンセル」ボタン  
  - **ポイント:** Bootstrapで整形

---

### ～APIイベント: 
- **ステップ 1: APIルートの実装**  
  - **編集対象ファイル:** `web/src/routes/api.py`（新規）  
  - **目的:** REST APIエンドポイントの提供  
  - **内容:**  
    - GET /pets, POST /pets, GET /pets/<id>, PUT /pets/<id>, DELETE /pets/<id>  
    - JSONリクエスト/レスポンス、バリデーション・エラー時のJSON返却  
  - **活用するクラス・メソッド:**  
    - `flask.jsonify`, `request.get_json()`  
  - **ポイント:** バリデーション・エラー時は例示通りのJSONを返す

---

### ～エラーハンドリング: 
- **ステップ 1: エラー表示の実装**  
  - **編集対象ファイル:** 各テンプレート（`index.html`, `edit.html` など）  
  - **目的:** バリデーション・DBエラー時の画面表示  
  - **内容:**  
    - バリデーションエラーは各フォーム項目下に赤字で表示  
    - DBやAPI通信エラーは画面上部に赤色アラートで表示  
  - **活用するクラス・メソッド:**  
    - Flaskの`flash()`、`get_flashed_messages()`  
  - **ポイント:** UI例・メッセージ例をREADME通りに

---

**補足:**  
- 既存のクラス・メソッドは積極的に活用し、命名・フィールド名は設計書と統一してください。
- テンプレートのUI要素（ボタン名・ラベル・配置）はREADMEの記載例に従ってください。
- APIのリクエスト/レスポンス例・エラー例もREADMEの例を厳守してください。