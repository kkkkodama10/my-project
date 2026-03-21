# subjectA

## 1. 要件整理

- 機能要件：	
	- ユーザーは社員と経理の二種類
	- 社員は立替経費を申請する
	- 社員は申請した経費を一覧できる
	- 社員が登録する申請内容は以下を含む
    	- 金額（int）
    	- 日付（datetime）
    	- カテゴリ（enum）
    	- メモ（text）
    	- 画像（最大3枚） jpeg/pngのみ
  	- 申請は作成時に申請ステータスが付き、最初はDRAFT
  	- 申請ステータスはDRAFT / SUBMITTED / APPROVED / REJECTED
  	- 社員はDRAFT をSUBMITTEDへ変更が可能
  	- 社員はREJECTEDをDRAFTへ変更が可能
  	- 申請内容の変更は DRAFT のみ可能
	- 申請の削除は DRAFT のみ可能
  	- 経理はすべての社員の申請を一覧できる
  	- 経理はSUBMITTEDになった申請を確認して、APPROVEDかREJECTEDを登録する
  	- 申請は申請IDを持ち、DRAFT、SUBMITTED、APPROVED、REJECTEDの変更履歴を持っていおり、変更履歴は以下を管理
    	- 変更履歴日時：datetime
    	- 変更前ステータス：enum
    	- 変更後ステータス：enum
    	- actor_user_id：Cognito sub
    	- actor_role（enum）
    	- reason（text）
  	- 変更履歴は当該社員と経理は見ることが可能
  	- 社員と経理のユーザー管理は必要
  	- ユーザー管理は以下の情報を登録する
    	- userID,名前、ロール（社員or経理）
    	- 認証情報（ログインID/パスワード）は Cognito
  	- 一覧/詳細のアクセス制御：社員は自分の申請のみ、経理は全件、監査ログも同様
- 非機能要件：
  - 可用性：平日9–18中心の利用、ただし時間外アクセスも拒否しない（運用都合でメンテ時間は許容）
  - 死活監視は最低限（API、エラー率）
  - 申請データは半年間は高頻度をアクセスされる可能性があるが、徐々にアクセス頻度が落ちる
  - 保持期間は7年。7年経過後は低アクセスアーカイブへ移動。削除は論理削除を基本とし、物理削除は別途ポリシーで実施
  - アクセスのピークは平日昼に同時アクセス50
  - セキュリティ要件として、社員と経理のみが利用
  - 常時稼働コストを抑えるためサーバレス優先（Lambda/API Gateway等）
  - すべてのデータ保持期間は7年
  - 単一リージョンで構成
  - データのバックアップは取っておく
  - 認証は Amazon Cognito（User Pool） 
  - 一覧/詳細のアクセス制御：社員は自分の申請のみ、経理は全件、監査ログも同様	
  - データ分類：領収書画像は機密（個人情報含む可能性）→暗号化必須、アクセス制御厳格
- 制約・前提：
  - AWS
  - 社員数300名
  - 経理数10名
  - 月額は数万円以内のランニングコスト
- 仮定
  - アップロード画像は jpeg/pngのみ
  - 画像サイズ上限（例：1枚5MB、最大3枚、合計15MB）
  - 当面はユーザー数は大きく増えない（~500）
  - 一覧のページング・ソート要件（例：最新順、100件/ページ）
  - 監査ログは「ステータス変更のみ」か「項目変更も含む」か（初級はステータスのみでOK）
  - 入退社対応が必要 → Cognitoで無効化、権限変更の運用を想定
- 未確定事項
  - カテゴリは誰が設定するのか？カテゴリの用途は？
  - 申請がAPPROVEDかREJECTEDの状態になったら、社員に通知はいくか？
  - ユーザ登録機能は必要か？
- スコープ外：
	- 経費を口座に支払う機能はなし
	- 既存の人事DB等との連携は当面なし
	- 社員と担当経理を紐づけはなし
	- マルチリージョン
	- 高スループット
	- SSO,MFA
	- 電子帳簿保存法対応の厳密要件

## 2. 概念設計（コンポーネント）

### 2.1 境界

- 利用者領域
  - 社員と経理
- クライアント領域
  - ブラウザ（信頼しない）
- 認証領域
  - Cognito（認証の責任を持つ）
- アプリケーション
  - API/業務ルール（責任を持つ）
- データ領域
  - DB/S3（データ保護の責任を持つ）

### 2.2 主要コンポーネント

- クライアント（webブラウザ）：申請入力、画像アップロード、一覧表示、申請提出/承認操作
- DB：申請一覧、変更履歴一覧
- ファイルストレージ：領収書画像の保存（暗号化、アクセス制御）
- API：申請CRUD、権限チェック、ステータス変更、JWT検証（署名/期限）、業務ルール
- Cognito：認証、トークン発行、ロール付与
- 運用ログ：APIログ

### 2.3 データフロー

- ログイン
  - web-> cognito -> JWT -> web
- ステータスの境界（フロー）
  - 作成・編集可能：DRAFT
  - 提出：DRAFT→SUBMITTED
  - 承認/却下：SUBMITTED→APPROVED/REJECTED
  - 下書きに戻す：REJECTED→DRAFT
- 画像アップロード
  - Web→署名付きURLを取得→S3へPUT→申請APIへ画像キー紐付け
- 申請提出
  - Web→申請API→DB更新+監査ログ
- 承認・却下
  - Web→申請API→DB更新+監査ログ

## 3. 論理設計（重要な判断）

- データストア選定方針（RDB/NoSQL/…のどれにするか＆理由）：
- 画像保管・配信方針：
- 認証認可の方針（誰が何にアクセスできるか）：
- 非機能（可用性/運用/コスト）を満たすための工夫：


### Q1 — 申請DB

- ストア候補：RDS（Aurora PostgreSQL系）
- 理由：
  - 一覧／絞り込み／ソート（経理の未処理一覧など）が中心で、RDB が得意な処理であるため
  - 申請・画像キー・履歴の関係をテーブル設計しやすい
  - 状態遷移の一貫性を保ちやすい（制約やトランザクションで整合性を担保できる）

### Q2 — 監査ログ

- ストア方針：同じ RDS の別テーブル（追記のみ）
- 理由：
  - 監査ログは業務データとして検索や画面表示が必要であり、申請と同じストアにあると実装が簡単になる
  - ストアが増えないため運用・権限制御が単純になる
  - “追記のみ”の運用ルールにより改ざんリスクを下げられる（必要に応じてさらに強化可能）

### Q3 DB設計

- claims
  - claim_id(ulid) *PK 
  - employee_id(ulid)  *FK
  - status_id(ulid) *FK
  - amount(int)
  - expense_date(datetime)
  - created_at(datetime)
  - updated_at(datetime)
  - category_id(ulid) *FK
  - memo(str)
- employees
  - id(ulid) *PK
  - name(str)
  - role_id(ulid) *FK
  - cognito_id *UK
- roles
  - id(ulid) *PK
  - name(str) *UK
- categories
  - id(ulid) *PK
  - name(str) *UK
- claim_status
  - id(ulid) *PK
  - name(str) *UK

- status_id
  - audit_event_id(ulid) *PK
  - claim_id(ulid)  *FK
  - from_status_id *FK
  - to_status_id *FK
  - occurred_at(datetime)
  - actor_employee_id(ulid) *FK
  - reason(str)
(status_update_logs は UPDATE/DELETEを禁止（アプリケーションからはINSERTのみ）)

# Q4

1. 経理の「未処理一覧（SUBMITTED）」を速くするため、claims にどんなINDEXを貼る？
   - claims(status_id, created_at DESC)
2. 社員の「自分の申請一覧（最新順）」のINDEXは？
   - claims(employee_id, created_at DESC)
3.	監査ログを「申請詳細画面で時系列表示」するためのINDEXは？
   - status_id(occurred_at, claim_id DESC)


## 4. トレードオフ

- 迷った案Aと不採用理由：
- 迷った案Bと不採用理由：
- リスクと緩和策：

--

# subjectB

## 1. 要件整理

- 機能要件：	
	- アプリユーザーは顧客と管理者の二種類
	- 顧客は注文を作成できる
  	- 注文には以下の情報を含む
    	- order_id
    	- order_contents
        	- item_id
        	- counts
      	- customer_id
      	- 配送先
      	- 連絡先
      	- payment_id
      	- ステータス
	- 顧客は自分の注文を一覧できる
	- 管理者はすべての顧客の注文を一覧できる
  	- ステータスは以下を含む
    	- CREATED / PAID /  SHIPPED / CANCELED
  	- 支払い通知はpayment_webhook_eventsで管理する
    	- webhook_event_id UK
    	- payment_id
    	- order_id
    	- received_at
    	- processed_at
    	- status（RECEIVED/PROCESSED/FAILED）
    	- result（succeeded/failed）
    	- raw_payload
  	- succeeded / failed は orderがCREATEDのときだけ適用
	- succeeded を受け取ったら CREATED -> PAID
	- failed を受け取ったら CREATED -> CANCELED
	- 発送されたら PAID -> SHIPPED
    	- PAIDになった注文は外部の出荷依頼を倉庫システムへ送る
  	- payment_webhook_events.statusは今回は使わないが将来のためにさくせい
  	- ステータスの変更は履歴として残す
    	- status_event_id
    	- order_id
    	- status_from
    	- status_to
    	- occurred_at
    	- actor(payment-webhook, admin_user_id)
    	- reason
- 非機能要件：
    - 利用規模：
      - 日次注文 1,000件
      - ピーク時 1分あたり 50件の注文作成
    - 可用性：24/7
    - 目標：注文作成APIは p95 300ms 程度
    - 障害：倉庫システムが落ちる/遅いことがある（数分〜数時間）のでキューシステムを使う
    - データ保持：注文データ 7年（監査）
    - コスト最適化のため将来アーカイブを検討
    - セキュリティ：顧客は自分の注文のみ閲覧、管理者は全件
    - 運用：SREなし、開発者運用。マネージド優先
    - webhookから同じ通知が重複して届く可能性があるため、payment_webhook_eventsのevent_idに重複がある場合は無視する、DBには初回のイベントのみ記録
    - 冪等性は event_id で担保する+すでに同じ payment_id が紐付いていれば二重処理しない
- 制約・前提：
  - AWS
  - コスト：小さく開始（目安：月数万円〜十数万円以内）
- 仮定
  - 決済確定通知は外部からバックエンドに送信され、バックエンドが注文を PAID に更新する
- 未確定事項
  - webhookとのやりとりのインターフェースは？
  - 倉庫へのメッセージのインターフェースは？
  - 倉庫側が同一出荷依頼を重複受信しても冪等に処理できるか
- スコープ外：
  - 商品の一覧
  - 決済システムの開発
  - 倉庫システムの開発
  - ユーザー登録/パスワード管理等の実装（認証はCognito前提）

## 2. 概念設計（コンポーネント）

### 2.1 境界

- 利用者領域
  - 顧客と管理者
- アプリケーション
  - 注文API
  - 決済Webhook受信ハンドラ
  - 出荷依頼ワーカー
- データ領域
  - DB（データ保護の責任を持つ）
- キュー領域
  - 出荷依頼キュー（SQS）＋DLQ
- クライアント領域
  - ブラウザ（信頼しない）
- 認証領域
  - Cognito（認証の責任を持つ）
- 外部領域
  - 決済Webhook送信元
  - 倉庫システム


### 2.2 主要コンポーネント

- DB：
  - orders：注文本体（顧客ID、配送先、状態、payment_id等）
  - payment_webhook_events：受信イベント（冪等性キー、処理状態）
  - status_events：状態遷移監査（追記のみ）
- API：
  - 注文CRUD API
  - 注文ステータス変更API
- 決済Webhook受信ハンドラ
  - payment_webhook_events (webhook_event_id UK) にINSERTして重複排除する
  - Webhookハンドラが PAID 確定後に enqueue
- 出荷依頼ワーカー：SQSを消費して倉庫へ送信（失敗時リトライ、最終DLQ）
- SQS（出荷依頼）＋DLQ：倉庫不調時もためる・後で再送
- 運用ログ/監視：CloudWatch（エラー、DLQ滞留）

### 2.3 データフロー

- 注文作成（同期）
  - 顧客→注文API→orders（status=CREATED）＋status_events（actor=customer）
- 決済（非同期）
  - 決済webhook送信元（外部領域）→決済Webhook受信ハンドラ
    - payment_webhook_events (webhook_event_id UK) にINSERT（重複排除）
    - resultがsucceededの場合、
      - ordersのpayment_idを設定＆ステータスをPAIDに更新
      - PAIDに更新が成功したら、WebhookハンドラがSQSにenqueue
      - PAIDに更新が成功したら、status_events（actor=payment-webhook）にCREATED→PAID追記
    - resultがfailedの場合、
      - ordersのステータスをCANCELEDに更新
      - CANCELEDに更新したら、status_events（actor=payment-webhook）にCREATED→CANCELD追記
- 配送（非同期）
  - SQS→出荷依頼ワーカー→倉庫システム（外部）
  - 出荷依頼ワーカーをキューを取るのが失敗：自動リトライ、数回失敗五はDLQへ

### 2.4 質問

1.	DBは RDS と DynamoDB どっちにしますか？（理由1〜2行）
  - RDB
  - Aurora Serverless v2 (PostgreSQL互換) など（小規模開始＋24/7でもコスト/運用を抑えやすい）
    - ordersは日付、ステータスでソートしうる。payment_webhook_events・status_eventsは追加のみなので、DynamoDBでもいいが、複数ストアにするとトランザクション整合性・運用（バックアップ/権限/監視）が増えるため、初期はRDSに統一する

2.	冪等性のUK（webhook_event_id）はどう実装しますか？（ユニーク制約 or 条件付きPut）
  - 決済Webhook受信ハンドラが受信時に受信したwebhook_event_idがpayment_webhook_eventsに存在しない場
  合は、INSERTして、存在する場合は処理をしないようにすることで冪等性を保つ
  - payment_webhook_events.webhook_event_id に UNIQUE制約をもたせて、Webhook受信時は とにかくINSERTを試みる
    - 成功 → 初回なので処理続行
    - UNIQUE違反 → 重複なので処理終了（200を返して良い）

3.	SQSのDLQ到達条件：最大受信回数を何回にする？（例：5回）＋DLQ後の再処理（手動で再投入 等）
  - 再処理に回すまでの時間を増やしながら、最大5回再送する。DLQ後は手動で再投入する想定。
  - maxReceiveCount = 5
  - 失敗時はLambdaが例外を投げ、SQS再配信（Visibility Timeout調整）
  - DLQ到達後：管理者が原因確認し、必要なら再投入（再ドライブ）

# subject3

## 1. ネットワーク（VPC）

- VPC
  - VPC：10.0.0.0/16
  - 理由：サブネット分割と将来拡張の余裕。/20でも可だが今回は簡単に/16
- AZ
  - 2AZ（ap-northeast-1a / 1c等）
  - 理由：24/7、RDS Multi-AZ、NAT冗長性
- Subnet
  - Public Subnet（2AZ）：IGWへのルートあり（0.0.0.0/0 → IGW）
    - NAT Gateway（各AZに1つ or 片AZに1つでコスト優先）
  - Private App Subnet（2AZ）：0.0.0.0/0 → NAT GW
    - Lambda（注文API/Webhook/ワーカーのVPC接続）
  - Private DB Subnet（2AZ）：
    - RDS（Multi-AZ）
- NAT
  - 使う
    - 理由：ワーカーがAWS外の倉庫へHTTP送信するため
    - AWS向け通信をEndpointに逃がして、NATは“倉庫向け外部通信だけ”に限定する
- 使うもの
  - AWSサービスとして使う：SQS, CloudWatch Logs, Secrets Manager, KMS
  - VPC Endpointとして使う：SQS, CloudWatch Logs, Secrets Manager, KMS（※全部Interface Endpoint）
  - 設計方針：WorkerはVPC内

## 2. Webhook防御

- Webhookの入口：API Gateway構成（同一or分離）,WAF：ルール案（レート制限、IP allowlist、Managed rules…）
  - API GatewayにWAFをアタッチし、Managed Rule（Common / KnownBadInputs / SQLi）を有効化する
    - AWSManagedRulesCommonRuleSet（よくある攻撃パターン：悪性UA、既知の脆弱性スキャン等）
    - AWSManagedRulesKnownBadInputsRuleSet（既知の悪い入力）
    - AWSManagedRulesSQLiRuleSet（SQLインジェクション系）
- パス分離・リクエストサイズ制限
  - /orders/*
    - POST /orders：1250 req / 5min / IP
      - 要件は1分あたり 50件の注文作成のためその5倍
    - GET /orders：10000 req / 5min / IP
      - 様子見で調整
  - /webhook/payment/*
    - POST /webhook: 1250 req / 5min / IP
      - まずCountで確認→Block」
    - 決済事業者が送信元IPレンジを提供できる場合は /webhook/payment/* にIP allowlist（未確
- リクエストサイズ制限
  - POSTのみ
  - 64KB以下

## 3. IAM（最小権限）

- OrderApiRole（注文API Lamda）
  - allow
    - CloudWatch Logs:ログ出力
    - Secret Manager: DB接続Secret取得
    - KMS: Decrypt
  - not allow
    - SQS：送受信
- PaymentWebhookRole（Webhook受信Lambda）
  -  allow
    - CloudWatch Logs:ログ出力
    - Secret Manager: DB接続Secret取得
    - KMS: Decrypt
    - SQS：送信（SendMessage：出荷依頼Queueのみ）
  - not allow
    - SQS: 受信/削除
    - DLQ操作（Opsのみ）
- ShipmentWorkerRole：
  -  allow
    - CloudWatch Logs:ログ出力
    - SQS：受信＋削除＋可視性変更（出荷依頼Queueのみ）
      - ReceiveMessage / DeleteMessage / ChangeMessageVisibility / GetQueueAttributes
    - KMS: Decrypt
    - Secret Manager: DB接続Secret取得
  - not allow
    - SQS: 送信
    - DLQ操作（Opsのみ）
- OpsRole（運用者）：
  -  allow
    - CloudWatch Logs:ログ確認
    - DLQ：手動処理（再投入、削除、調査）
      - 元のQueueへ SendMessage
  - not allow
    - KMS
    - Secret Manager

## 4. 暗号化・秘密情報
- RDS暗号化：
  - KMSを有効化
  - DB接続はTLSを使用
- SQS暗号化：
  - SSE有効化（AWS管理キーを使う）
    - 初期は運用簡素化のためAWS管理キー。要件（監査/鍵分離）が厳しくなったらCMKに切替検討
- Secrets管理：
  - DB認証情報はSecrets Managerで管理（KMSはAWS管理キー）
    - Secretsは OrderApiRole / PaymentWebhookRole / ShipmentWorkerRole のみに GetSecretValue を許可
- raw_payloadの扱い（保存する/しない、保存するなら方針）
  - 保存しない（DBを修正する）

# subject4

## 1. DB設計

### orders

- order_id:ULID *PK
- customer_id:ULID *FK
- shipping_zip_code: str
- shipping_address: str
- contact_mail_address:str
- contact_phone_number: str
- payment_id:ULID/null
- order_status:enum -> CREATED / PAID /  SHIPPED / CANCELED
- created_at:datetime
- updated_at: datetime

- 要件：
  - 顧客は自分の注文のみ一覧、管理者は全件一覧。
    - order_id:ULID
    - item_id:ULID
	- counts:int

### order_items

- order_id (FK -> orders.order_id) *PK
- item_id *PK
- quantity

- 同じorder_idで複数のアイテムを持てる設計

### payment_webhook_events

- webhook_event_id:ULID *PK
- payment_id:ULID
- order_id:ULID *FK
- received_at: datetime
- processed_at: datetime
- process_result:enum ->succeeded/failed

- 要件：
  - 冪等性はINSERT時にUKで判断
  - succeeded / failed は orderがCREATEDのときだけ適用
  - succeeded を受け取ったら CREATED -> PAID
  - failed を受け取ったら CREATED -> CANCELED
- 備考：statusは直近は使わない

### status_events　*追記のみ

- status_event_id:ULID *PK
- order_id:ULID
- status_from:enum  -> CREATED / PAID /  SHIPPED / CANCELED
- status_to:enum  -> CREATED / PAID /  SHIPPED / CANCELED
- occurred_at: datetime
- actor_type:enum -> customer / payment-webhook / admin
- actor_id：nullable（customer_id や admin_user_id）
- reason:str

- 要件
  - 発送されたら PAID -> SHIPPED

## 2. インデックス設計

- orders
  - PK: (order_id)
  - 顧客の注文一覧（customer_idで絞って新しい順）
    - INDEX: (customer_id, created_at DESC)
  - 管理者の注文一覧（status + 期間で絞って新しい順）
    - INDEX: (order_status, created_at DESC)
- payment_webhook_events
  - 冪等性
    - UNIQUE: (webhook_event_id)
- status_events
  - 注文単位の監査ログ表示
    - INDEX: (order_id, occurred_at DESC)

## 3. 冪等性のDB実装

1. INSERT INTO payment_webhook_events(...) VALUES (...) ON CONFLICT DO NOTHING;
   - ここで 挿入できたか（inserted=true/false） を判定
   - inserted=false（重複）なら 終了（以降やらない）
2.	UPDATE orders SET status = CASE ... , payment_id=? WHERE order_id=? AND status='CREATED';
   - process_result='succeeded' なら PAID
   - process_result='failed' なら CANCELED
   - 更新件数（rows_affected）を取得
3.	IF rows_affected = 1 THEN INSERT INTO status_events(...) VALUES (...);
   - orders更新できた場合のみ監査ログ追記（重複や不整合で増えない）
4.	IF rows_affected = 1 AND process_result='succeeded' THEN SQSにSendMessage;
   - 初回の成功のみ出荷依頼

## 4. データ保持期間

- 7年保持。7年経過後は物理削除。
- orders/status_eventsは月次パーティショニングし、直近（例：0〜12ヶ月）をRDSでオンライン検索対象とする。
- 1年以上前のデータは月次でS3へエクスポート（CSV/Parquet）し、監査・調査はAthenaで参照できるようにする。RDS側は必要に応じて古いパーティションを読み取り専用/縮退させコスト最適化する。
- アーカイブジョブは EventBridge（定期）→ Lambda で実行し、結果をCloudWatch Logsへ記録、失敗時はリトライ/通知する。


# subject5

- Q1：エンドポイント
  - このシステムの最小APIとして、外部公開するエンドポイントを3つだけ挙げてください（パス＋メソッド）。
    - 条件：顧客用2つ＋Webhook1つ
- A1:
  - /orders + GET (自分の注文一覧)
  - /orders/<order_id> + GET（自分の注文詳細）
  - /payment_webhook_events/<webhook_event_id> + POST（決済：支払い確定通知）

- Q2：認証/認可（顧客）
  - GET /orders と GET /orders/{order_id} で、**「自分の注文だけ」**を保証する方法は？
    - JWTのどの情報（例：sub, custom:role）を使う？
    - DBのどの列と突合する？
- A2: 
  - JWTの sub を customer_id として扱い、orders.customer_id = sub の条件で一覧/詳細を取得する

- Q3：認証/認可（管理者）
  - 管理者だけが全件検索できるようにするには、JWTのどのクレームをどう見る？
    - 例：Cognito Group / custom:role など
- A3: 
  - JWTの cognito:groups に admins が含まれる場合のみ管理者APIを許可（それ以外403）

- Q4：注文作成APIのRequest/Response（最小）
  - POST /orders の request body と response を「必須フィールドだけ」で書いてください。
- A4:
  - Request：items[], shipping_*, contact_*
  - Response：order_id, status=CREATED, created_at

- Q5：注文一覧のページング（最小）
  - GET /orders は cursor方式にします。
  - cursorに何を入れますか？（例：created_at と order_id）
  - また response に何を返しますか？（items / next_cursor）
- A5: 
  - cursor：(created_at, order_id)をエンコードした文字列
  - response：items[] と next_cursor(null)

- Q6：注文作成の冪等性（重要）
  - POST /orders で二重注文を防ぐ方式を1つ選んで書いてください：
    - A Idempotency-Key ヘッダ
    - B client_order_id をbodyに含める
  - どこに保存して、重複時はどう返す？（201? 200?）
- A6:
  - 方式：A Idempotency-Keyヘッダ（もしくはBでもOK）
  - 保存先：ordersに idempotency_key 列を追加して UNIQUE(customer_id, idempotency_key)
  - 初回作成時は201, 重複時は200

- Q7：Webhookの最低限の防御（アプリ側）
  - WAF以外で、POST /webhook/payment のアプリ側で必ずやるチェックを2つ挙げてください。
  - 例：payload schema / 署名検証 / event_id存在 / order_id存在
- A7:
  - 本当の決済事業者かは署名検証で確認
  - スキーマ検証
    - webhook_event_id
    - payment_id	
    - order_id

- Q8：Webhookの冪等性（超重要）
  - Webhook処理で「初回だけ注文をPAIDにして出荷依頼を送る」を保証する要点を2行で書いてください。
  - ヒント：UK INSERT + 条件付きUPDATE + update成功時だけenqueue
- A8:
  - webhook_event_idをUK、PKとしてINSERT
  - 重複はINSERTできない
  - orders を WHERE status='CREATED' の条件付きUPDATEし、DBが持つ更新件数=1のときだけ status_events 追記＋SQS enqueue

- Q9：SQSメッセージ（最小スキーマ）
  - 出荷依頼Queueに送るメッセージJSONを、必須4項目だけで作ってください。
  - order_id, payment_id, webhook_event_id, requested_at
- A9:

	```
	{
	"order_id": "01J...",
	"payment_id": "pay_...",
	"webhook_event_id": "evt_...",
	"requested_at": "2025-12-31T12:34:56Z"
	}
	```

- Q10：エラー設計（本質だけ）

  - 次のケースはHTTP何番で返しますか？（番号だけでOK）
  	1.	他人の注文を見ようとした -> 403
  	2.	無効な入力（quantity=0） -> 400
  	3.	orderがCREATED以外なのに webhook succeeded が来た（状態不整合） -> 409
  	4.	レート制限に引っかかった（WAF/アプリどちらでも）-> 429


### APIレスポンス

- 400：入力がおかしい（バリデーションNG、必須不足）
- 401：認証できない（トークンなし/無効）
- 403：認証はOKだが権限なし（他人の注文、管理者権限なし）
- 404：存在しない（or 情報漏えい防止で「存在しない」に見せることも）
- 409：状態が衝突（不正な状態遷移、すでに処理済みで矛盾）
- 429：レート制限
- 5xx：サーバ側の失敗（DB落ち、タイムアウト等）

# subject6

- Q1：最大のリスクは何？このシステムで「最も避けたい事故」を1つ選んで理由も1行で。
  - 例：二重出荷 / 出荷漏れ / 誤キャンセル / 監査ログ欠落
- A1
  - 出荷漏れ
  - 出荷自体が漏れることは困る。出荷ワーカーはシステムが落ちる可能性があるため、システム的にリスクを回避する必要がある
  - 二重出荷は「冪等性キー＋倉庫側/こちら側の重複排除」で抑えやすい
  - 出荷漏れは「検知しないと永遠に気づけない」ので、最優先で潰すべき

- Q2：少なくとも一度 vs ちょうど一度
  - 出荷依頼は at-least-once（少なくとも1回）で良い？ exactly-once が必要？
  - どちらを採用するか＋理由1行
- A2
  - at-least-once
  - 冪等性処理を入れれば、同じ出荷依頼を複数出しても解決が可能
  - SQS/Lambdaは再配信が起きうる前提なので at-least-once とし、shipment_request_id（例：order_id）で冪等にする

- Q3：DB更新とSQS送信の“ギャップ”はどう埋める？
  - 次のどれを採用する？（A/B/Cから1つ）
    - A：失敗したらWebhookを失敗させて再送に任せる
    - B：Outboxテーブルで確実に送る（推奨）
    - C：EventBridge/CDC
  - 採用理由を2行で。
- A3
  - B?
  - PAID更新とoutbox書き込みを同一トランザクションにして出荷漏れを防ぐ。SQS送信失敗時もoutboxから再送でき復旧可能。


- Q4：Outboxにするなら、outboxテーブルの最小カラムは？（Aを選んだ人も“設計練習”として書いてOK）
  - 例：outbox_id, event_type, payload, status, created_at, sent_at, retry_count
- A4
  - 

- Q5：ワーカーの冪等性キーは何にする？
  - 倉庫へ送る「重複排除キー（idempotency key）」は何にする？
  - 例：shipment_request_id = order_id など
- A5
  - 

- Q6：SQSの主要パラメータを決めて（根拠も1行）
	•	Visibility Timeout：何秒？
	•	maxReceiveCount：何回？
	•	DLQ後：どうする？（再投入/破棄/調査）

- Q7：ワーカーのタイムアウトと外部HTTPタイムアウトは？
	•	Lambda timeout：何秒？
	•	倉庫HTTP timeout：何秒？
	•	リトライは “どこで” する？（HTTP内部/ワーカー再実行/SQS再配信）

- Q8：Webhookは失敗したら何を返す？
	次のケースでWebhookに返すHTTPを決めてください。
		1.	署名NG
		2.	JSON不正（スキーマNG）
		3.	DB一時障害
		4.	SQS送信失敗（A案 or B案で変わる）

- Q9：DLQが増えたら、最初に何を見る？
	DLQ到達時の一次切り分け（見る順）を3つ挙げてください。
		•	例：エラーログ→対象order_id→倉庫応答…

- Q10：二重出荷と出荷漏れをどう検知する？
	“メトリクス/ログ/DB状態”のいずれかで、各1つずつ。
		•	二重出荷の検知1つ
		•	出荷漏れの検知1つ