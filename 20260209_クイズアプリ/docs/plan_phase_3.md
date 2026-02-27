# Phase 3 技術計画 — AWS 本番構成

## 0. 目的

Phase 2（ローカル本格版）で完成したクイズアプリを AWS 上にデプロイし、HTTPS で外部公開する。
水平スケール可能なアーキテクチャとし、同時接続 100〜1,000 人規模に対応する。

---

## 1. ターゲットアーキテクチャ

```
                         ┌──────────────────────────────────────┐
                         │           AWS Cloud (ap-northeast-1) │
                         │                                      │
  Browser ──HTTPS──→  CloudFront ──→ S3 (React SPA + 画像)     │
     │                   │                                      │
     └──HTTPS/WSS──→  ALB ──→ ECS Fargate (FastAPI × N)        │
                         │         ↕                            │
                         │    RDS PostgreSQL (Multi-AZ)         │
                         │         ↕                            │
                         │    ElastiCache Valkey (Multi-AZ)    │
                         │                                      │
                         │    ECR (Docker イメージ)              │
                         │    Secrets Manager (環境変数)         │
                         │    CloudWatch (ログ・メトリクス)       │
                         └──────────────────────────────────────┘
```

### 1.1 サービス一覧と役割

| AWSサービス | 用途 | 補足 |
|---|---|---|
| **VPC** | ネットワーク分離 | パブリック/プライベートサブネット |
| **ALB** | ロードバランサー | HTTPS 終端、WebSocket 対応 |
| **ECS Fargate** | バックエンド実行 | コンテナベース、サーバーレス |
| **ECR** | Docker イメージ保管 | プライベートリポジトリ |
| **RDS PostgreSQL** | データベース | Multi-AZ、SQLite からの移行 |
| **ElastiCache Valkey** | セッション・WS Pub/Sub | マルチインスタンス連携 |
| **S3** | SPA ホスティング・画像保存 | 静的ファイル配信 |
| **CloudFront** | CDN | HTTPS 終端、S3 前段キャッシュ |
| **Route 53** | DNS（任意） | カスタムドメイン使用時 |
| **ACM** | SSL/TLS 証明書 | 無料の AWS 証明書 |
| **Secrets Manager** | シークレット管理 | DB パスワード等 |
| **CloudWatch** | ログ・監視 | コンテナログの集約 |

---

## 2. 前提条件

### 2.1 必要なもの

- [ ] AWS アカウント（クレジットカード登録済み）
- [ ] AWS CLI v2 インストール済み（ECR プッシュ・S3 アップロード等で使用）
- [ ] Docker Desktop インストール済み（ローカルでのイメージビルド用）
- [ ] （任意）独自ドメイン（Route 53 or 他のレジストラ）

### 2.2 リージョン

**ap-northeast-1（東京）** を使用する。
AWS コンソール右上のリージョン選択で「アジアパシフィック (東京)」を選ぶ。

### 2.3 推定コスト（月額目安）

| サービス | 構成 | 月額目安 |
|---|---|---|
| ECS Fargate | 0.25 vCPU / 0.5 GB × 1 タスク | 約 $10 |
| RDS PostgreSQL | db.t4g.micro, Single-AZ（開発時） | 約 $15 |
| ElastiCache Valkey | cache.t4g.micro, Single Node（開発時） | 約 $13 |
| ALB | 1 ALB | 約 $18 |
| S3 + CloudFront | 数 GB 程度 | 約 $1〜 |
| その他（VPC, CloudWatch 等） | - | 約 $3〜 |
| **合計（開発構成）** | | **約 $60/月** |

> **注意**: Multi-AZ 構成にするとコストは約 1.5〜2 倍になります。
> 最初は Single-AZ（開発構成）で始め、本番運用時に Multi-AZ に切り替えることを推奨します。

---

## 3. 実装マイルストーン

| MS | 名称 | 内容 | 依存 |
|---|---|---|---|
| MS1 | AWS 基盤構築 | VPC・サブネット・セキュリティグループ | - |
| MS2 | データベース構築 | RDS PostgreSQL + ElastiCache Redis | MS1 |
| MS3 | バックエンド改修 | PostgreSQL / Redis 対応のコード変更 | - |
| MS4 | コンテナ化 & ECR | Dockerfile 修正・ECR プッシュ | MS3 |
| MS5 | ECS Fargate デプロイ | タスク定義・サービス作成・ALB 接続 | MS1, MS2, MS4 |
| MS6 | フロントエンドデプロイ | S3 + CloudFront で SPA 配信 | MS5 |
| MS7 | HTTPS & ドメイン設定 | ACM 証明書・CloudFront / ALB の HTTPS 化 | MS6 |
| MS8 | 動作検証 & 本番調整 | E2E テスト・負荷テスト・監視設定 | MS7 |

---

## 4. MS1: AWS 基盤構築（VPC・ネットワーク）

### 4.1 全体構成

```
VPC (10.0.0.0/16)
├── パブリックサブネット A (10.0.1.0/24) — AZ: ap-northeast-1a
│   └── ALB, NAT Gateway
├── パブリックサブネット C (10.0.2.0/24) — AZ: ap-northeast-1c
│   └── ALB（冗長）
├── プライベートサブネット A (10.0.10.0/24) — AZ: ap-northeast-1a
│   └── ECS Fargate, RDS, ElastiCache
└── プライベートサブネット C (10.0.20.0/24) — AZ: ap-northeast-1c
    └── ECS Fargate, RDS, ElastiCache（冗長）
```

### 4.2 AWS CLI の初期設定

AWS コンソール（UI）を主に使いますが、ECR プッシュや S3 アップロード等で CLI も必要です。
先に CLI をセットアップしておきます。

```bash
# AWS CLI がインストールされているか確認
aws --version

# インストールされていない場合（macOS）
brew install awscli
```

**IAM アクセスキーの作成（コンソール操作）:**

1. AWS コンソールにログイン
2. 右上のアカウント名 → **「セキュリティ認証情報」**
3. 「アクセスキー」セクション → **「アクセスキーを作成」**
4. ユースケース: 「コマンドラインインターフェイス (CLI)」を選択
5. アクセスキー ID とシークレットアクセスキーを控える

```bash
# 取得したキーで CLI を設定
aws configure
# AWS Access Key ID: （発行したアクセスキーID）
# AWS Secret Access Key: （発行したシークレットキー）
# Default region name: ap-northeast-1
# Default output format: json
```

### 4.3 VPC の作成

**コンソール操作: VPC → お使いの VPC → VPC を作成**

1. AWS コンソール上部の検索バーで **「VPC」** と入力して VPC サービスを開く
2. 左メニュー **「お使いの VPC」** → **「VPC を作成」** ボタン

| 設定項目 | 値 |
|---|---|
| 作成するリソース | **「VPC のみ」** |
| 名前タグ | `quiz-app-vpc` |
| IPv4 CIDR ブロック | `10.0.0.0/16` |
| IPv6 CIDR ブロック | なし |
| テナンシー | デフォルト |

3. **「VPC を作成」** ボタンを押す

**DNS ホスト名の有効化（RDS で必要）:**

4. 作成した VPC の詳細画面 → **「アクション」** → **「VPC の設定を編集」**
5. **「DNS ホスト名を有効化」** にチェック → **保存**

> **メモ**: VPC ID（`vpc-xxxxxxxxx`）を控えておく。以降の手順で使います。

<details>
<summary>CLI で実行する場合</summary>

```bash
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=quiz-app-vpc}]' \
  --query 'Vpc.VpcId' --output text

aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames '{"Value":true}'
```
</details>

### 4.4 サブネットの作成

**コンソール操作: VPC → サブネット → サブネットを作成**

1. VPC 画面の左メニュー **「サブネット」** → **「サブネットを作成」**

4 つのサブネットを順に作成します。「新しいサブネットを追加」ボタンで一度に追加できます。

| # | 名前タグ | VPC | AZ | CIDR | 用途 |
|---|---|---|---|---|---|
| 1 | `quiz-public-a` | quiz-app-vpc | ap-northeast-1**a** | `10.0.1.0/24` | ALB・NAT GW |
| 2 | `quiz-public-c` | quiz-app-vpc | ap-northeast-1**c** | `10.0.2.0/24` | ALB（冗長） |
| 3 | `quiz-private-a` | quiz-app-vpc | ap-northeast-1**a** | `10.0.10.0/24` | ECS・RDS・Redis |
| 4 | `quiz-private-c` | quiz-app-vpc | ap-northeast-1**c** | `10.0.20.0/24` | ECS・RDS・Redis（冗長） |

2. **「サブネットを作成」** ボタンを押す

**パブリックサブネットの自動 IP 割り当てを有効化:**

3. `quiz-public-a` を選択 → **「アクション」** → **「サブネットの設定を編集」**
4. **「パブリック IPv4 アドレスの自動割り当てを有効にする」** にチェック → **保存**
5. `quiz-public-c` にも同様の設定を行う

<details>
<summary>CLI で実行する場合</summary>

```bash
# パブリックサブネット A
aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 \
  --availability-zone ap-northeast-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=quiz-public-a}]'

# パブリックサブネット C
aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 \
  --availability-zone ap-northeast-1c \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=quiz-public-c}]'

# プライベートサブネット A
aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.10.0/24 \
  --availability-zone ap-northeast-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=quiz-private-a}]'

# プライベートサブネット C
aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.20.0/24 \
  --availability-zone ap-northeast-1c \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=quiz-private-c}]'

# パブリックサブネットの自動 IP 割り当て
aws ec2 modify-subnet-attribute --subnet-id $PUBLIC_SUBNET_A --map-public-ip-on-launch
aws ec2 modify-subnet-attribute --subnet-id $PUBLIC_SUBNET_C --map-public-ip-on-launch
```
</details>

### 4.5 インターネットゲートウェイの作成

パブリックサブネットからインターネットに出るためのゲートウェイです。

**コンソール操作: VPC → インターネットゲートウェイ → インターネットゲートウェイの作成**

1. 左メニュー **「インターネットゲートウェイ」** → **「インターネットゲートウェイの作成」**
2. 名前タグ: `quiz-igw` → **「インターネットゲートウェイの作成」**
3. 作成直後の画面で **「アクション」** → **「VPC にアタッチ」**
4. VPC: `quiz-app-vpc` を選択 → **「インターネットゲートウェイのアタッチ」**

<details>
<summary>CLI で実行する場合</summary>

```bash
aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=quiz-igw}]' \
  --query 'InternetGateway.InternetGatewayId' --output text

aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID
```
</details>

### 4.6 ルートテーブルの設定

#### パブリック用ルートテーブル

**コンソール操作: VPC → ルートテーブル → ルートテーブルの作成**

1. 左メニュー **「ルートテーブル」** → **「ルートテーブルの作成」**
2. 名前: `quiz-public-rt`、VPC: `quiz-app-vpc` → **作成**
3. 作成されたルートテーブルを選択 → 下部の **「ルート」** タブ → **「ルートを編集」**
4. **「ルートを追加」** をクリック:
   - 送信先: `0.0.0.0/0`
   - ターゲット: **「インターネットゲートウェイ」** → `quiz-igw` を選択
5. **「変更を保存」**
6. **「サブネットの関連付け」** タブ → **「サブネットの関連付けを編集」**
7. `quiz-public-a` と `quiz-public-c` にチェック → **保存**

#### NAT Gateway の作成

プライベートサブネットの ECS タスクが外部（ECR からのイメージ取得等）に通信するために必要です。

**コンソール操作: VPC → NAT ゲートウェイ → NAT ゲートウェイを作成**

1. 左メニュー **「NAT ゲートウェイ」** → **「NAT ゲートウェイを作成」**

| 設定項目 | 値 |
|---|---|
| 名前 | `quiz-nat` |
| サブネット | `quiz-public-a`（パブリックサブネットに置く） |
| 接続タイプ | パブリック |
| Elastic IP | **「Elastic IP を割り当て」** ボタンを押して新規作成 |

2. **「NAT ゲートウェイを作成」** → ステータスが **Available** になるまで 1〜2 分待つ

#### プライベート用ルートテーブル

3. **「ルートテーブル」** → **「ルートテーブルの作成」**
4. 名前: `quiz-private-rt`、VPC: `quiz-app-vpc` → **作成**
5. **「ルート」** タブ → **「ルートを編集」** → **「ルートを追加」**:
   - 送信先: `0.0.0.0/0`
   - ターゲット: **「NAT ゲートウェイ」** → `quiz-nat` を選択
6. **「変更を保存」**
7. **「サブネットの関連付け」** タブ → `quiz-private-a` と `quiz-private-c` にチェック → **保存**

<details>
<summary>CLI で実行する場合</summary>

```bash
# パブリック用ルートテーブル
aws ec2 create-route-table --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=quiz-public-rt}]' \
  --query 'RouteTable.RouteTableId' --output text

aws ec2 create-route --route-table-id $PUBLIC_RT_ID \
  --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID

aws ec2 associate-route-table --route-table-id $PUBLIC_RT_ID --subnet-id $PUBLIC_SUBNET_A
aws ec2 associate-route-table --route-table-id $PUBLIC_RT_ID --subnet-id $PUBLIC_SUBNET_C

# NAT Gateway
aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text
aws ec2 create-nat-gateway --subnet-id $PUBLIC_SUBNET_A --allocation-id $EIP_ALLOC_ID \
  --tag-specifications 'ResourceType=natgateway,Tags=[{Key=Name,Value=quiz-nat}]'
aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_ID

# プライベート用ルートテーブル
aws ec2 create-route-table --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=quiz-private-rt}]' \
  --query 'RouteTable.RouteTableId' --output text

aws ec2 create-route --route-table-id $PRIVATE_RT_ID \
  --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_GW_ID

aws ec2 associate-route-table --route-table-id $PRIVATE_RT_ID --subnet-id $PRIVATE_SUBNET_A
aws ec2 associate-route-table --route-table-id $PRIVATE_RT_ID --subnet-id $PRIVATE_SUBNET_C
```
</details>

### 4.7 セキュリティグループの作成

セキュリティグループは「どの通信を許可するか」のファイアウォールルールです。
4 つ作成します。

**コンソール操作: VPC → セキュリティグループ → セキュリティグループを作成**

#### (1) ALB 用: `quiz-alb-sg`

| 設定項目 | 値 |
|---|---|
| 名前 | `quiz-alb-sg` |
| 説明 | `ALB security group` |
| VPC | `quiz-app-vpc` |

**インバウンドルール:**

| タイプ | ポート | ソース | 説明 |
|---|---|---|---|
| HTTP | 80 | `0.0.0.0/0`（Anywhere） | HTTP アクセス |
| HTTPS | 443 | `0.0.0.0/0`（Anywhere） | HTTPS アクセス |

#### (2) ECS タスク用: `quiz-ecs-sg`

| 設定項目 | 値 |
|---|---|
| 名前 | `quiz-ecs-sg` |
| 説明 | `ECS tasks security group` |
| VPC | `quiz-app-vpc` |

**インバウンドルール:**

| タイプ | ポート | ソース | 説明 |
|---|---|---|---|
| カスタム TCP | 8000 | `quiz-alb-sg`（セキュリティグループ指定） | ALB からのみ許可 |

> **ポイント**: ソースにセキュリティグループを指定すると、そのグループに属するリソースからのみ通信を許可できます。IP アドレスではなく **`quiz-alb-sg` を選択** してください。

#### (3) RDS 用: `quiz-rds-sg`

| 設定項目 | 値 |
|---|---|
| 名前 | `quiz-rds-sg` |
| 説明 | `RDS security group` |
| VPC | `quiz-app-vpc` |

**インバウンドルール:**

| タイプ | ポート | ソース | 説明 |
|---|---|---|---|
| PostgreSQL | 5432 | `quiz-ecs-sg`（セキュリティグループ指定） | ECS からのみ許可 |

#### (4) ElastiCache Valkey 用: `quiz-redis-sg`

| 設定項目 | 値 |
|---|---|
| 名前 | `quiz-redis-sg` |
| 説明 | `ElastiCache Valkey security group` |
| VPC | `quiz-app-vpc` |

**インバウンドルール:**

| タイプ | ポート | ソース | 説明 |
|---|---|---|---|
| カスタム TCP | 6379 | `quiz-ecs-sg`（セキュリティグループ指定） | ECS からのみ許可 |

<details>
<summary>CLI で実行する場合</summary>

```bash
# ALB 用
aws ec2 create-security-group --group-name quiz-alb-sg --description "ALB security group" --vpc-id $VPC_ID
aws ec2 authorize-security-group-ingress --group-id $ALB_SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $ALB_SG_ID --protocol tcp --port 443 --cidr 0.0.0.0/0

# ECS 用
aws ec2 create-security-group --group-name quiz-ecs-sg --description "ECS tasks security group" --vpc-id $VPC_ID
aws ec2 authorize-security-group-ingress --group-id $ECS_SG_ID --protocol tcp --port 8000 --source-group $ALB_SG_ID

# RDS 用
aws ec2 create-security-group --group-name quiz-rds-sg --description "RDS security group" --vpc-id $VPC_ID
aws ec2 authorize-security-group-ingress --group-id $RDS_SG_ID --protocol tcp --port 5432 --source-group $ECS_SG_ID

# Redis 用
aws ec2 create-security-group --group-name quiz-redis-sg --description "ElastiCache security group" --vpc-id $VPC_ID
aws ec2 authorize-security-group-ingress --group-id $REDIS_SG_ID --protocol tcp --port 6379 --source-group $ECS_SG_ID
```
</details>

### 4.8 確認

VPC ダッシュボードで以下が作成されていることを確認:

- [ ] VPC: `quiz-app-vpc` (10.0.0.0/16)
- [ ] サブネット: 4 つ（public-a, public-c, private-a, private-c）
- [ ] インターネットゲートウェイ: `quiz-igw`（VPC にアタッチ済み）
- [ ] NAT ゲートウェイ: `quiz-nat`（Available 状態）
- [ ] ルートテーブル: public-rt（IGW 向き）、private-rt（NAT 向き）
- [ ] セキュリティグループ: 4 つ（alb, ecs, rds, redis）

---

## 5. MS2: データベース構築

### 5.1 RDS PostgreSQL

#### Step 1: DB サブネットグループの作成

**コンソール操作: RDS → サブネットグループ → DB サブネットグループを作成**

1. AWS コンソール上部の検索バーで **「RDS」** と入力して RDS サービスを開く
2. 左メニュー **「サブネットグループ」** → **「DB サブネットグループを作成」**

| 設定項目 | 値 |
|---|---|
| 名前 | `quiz-db-subnet` |
| 説明 | `Quiz app DB subnet group` |
| VPC | `quiz-app-vpc` |

3. **「サブネットを追加」** セクション:
   - アベイラビリティーゾーン: `ap-northeast-1a` と `ap-northeast-1c` を選択
   - サブネット: `quiz-private-a` (10.0.10.0/24) と `quiz-private-c` (10.0.20.0/24) を選択
4. **「作成」**

#### Step 2: マスターパスワードの準備

RDS のマスターパスワードを決めておきます。安全な文字列を使ってください。

> **推奨**: Secrets Manager に保存しておくと、後で ECS タスクから安全に取得できます。
>
> **コンソール操作: Secrets Manager → 新しいシークレットを保存する**
> 1. 検索バーで **「Secrets Manager」** を開く
> 2. **「新しいシークレットを保存する」**
> 3. シークレットのタイプ: **「その他のシークレットのタイプ」**
> 4. キー: `password`、値: （安全なパスワード文字列）
> 5. シークレットの名前: `quiz-app/rds-password` → **保存**

#### Step 3: RDS インスタンスの作成

**コンソール操作: RDS → データベース → データベースの作成**

1. **「データベースの作成」** ボタン

| 設定項目 | 値 |
|---|---|
| データベース作成方法 | **標準作成** |
| エンジンタイプ | **PostgreSQL** |
| エンジンバージョン | 16.x（最新の 16 系） |
| テンプレート | **無料利用枠**（対象の場合）or **開発/テスト** |
| DB インスタンス識別子 | `quiz-app-db` |
| マスターユーザー名 | `quizadmin` |
| マスターパスワード | （Step 2 で決めたパスワード） |

2. **インスタンスの設定:**

| 設定項目 | 値 |
|---|---|
| DB インスタンスクラス | **db.t4g.micro**（バースト可能） |
| ストレージタイプ | gp3 |
| ストレージ割り当て | 20 GiB |
| ストレージの自動スケーリング | 有効（最大 100 GiB） |

3. **接続:**

| 設定項目 | 値 |
|---|---|
| VPC | `quiz-app-vpc` |
| DB サブネットグループ | `quiz-db-subnet` |
| パブリックアクセス | **いいえ**（重要! セキュリティのため） |
| VPC セキュリティグループ | **既存の選択** → `quiz-rds-sg` |
| アベイラビリティーゾーン | 指定なし |

4. **追加設定:**

| 設定項目 | 値 |
|---|---|
| 最初のデータベース名 | `quizapp` |
| バックアップ保持期間 | 7 日 |
| 暗号化 | 有効 |
| マルチ AZ 配置 | **いいえ**（開発構成。本番時に変更） |

5. **「データベースの作成」** → 作成完了まで **5〜10 分** 待つ

6. ステータスが **「利用可能」** になったら、**エンドポイント**（ホスト名）を控える:
   - 例: `quiz-app-db.xxxxxxxxxxxx.ap-northeast-1.rds.amazonaws.com`
   - 以降 `$RDS_ENDPOINT` として参照

<details>
<summary>CLI で実行する場合</summary>

```bash
aws rds create-db-subnet-group \
  --db-subnet-group-name quiz-db-subnet \
  --db-subnet-group-description "Quiz app DB subnet group" \
  --subnet-ids $PRIVATE_SUBNET_A $PRIVATE_SUBNET_C

aws rds create-db-instance \
  --db-instance-identifier quiz-app-db \
  --db-instance-class db.t4g.micro \
  --engine postgres --engine-version 16.4 \
  --allocated-storage 20 --storage-type gp3 \
  --master-username quizadmin \
  --master-user-password "YOUR_PASSWORD" \
  --db-name quizapp \
  --vpc-security-group-ids $RDS_SG_ID \
  --db-subnet-group-name quiz-db-subnet \
  --no-publicly-accessible \
  --backup-retention-period 7 --no-multi-az --storage-encrypted

aws rds wait db-instance-available --db-instance-identifier quiz-app-db

aws rds describe-db-instances --db-instance-identifier quiz-app-db \
  --query 'DBInstances[0].Endpoint.Address' --output text
```
</details>

### 5.2 ElastiCache Valkey

#### Step 1: Valkey サブネットグループの作成

**コンソール操作: ElastiCache → サブネットグループ → サブネットグループの作成**

1. 検索バーで **「ElastiCache」** を開く
2. 左メニュー **「サブネットグループ」** → **「サブネットグループの作成」**

| 設定項目 | 値 |
|---|---|
| 名前 | `quiz-valkey-subnet` |
| 説明 | `Quiz app Valkey subnet group` |
| VPC | `quiz-app-vpc` |

3. サブネット: `quiz-private-a` と `quiz-private-c` を追加 → **作成**

#### Step 2: Valkey クラスターの作成

**コンソール操作: ElastiCache → Valkey キャッシュ → Valkey キャッシュを作成**

1. **「Valkey キャッシュを作成」** ボタン

| 設定項目 | 値 |
|---|---|
| デプロイオプション | **独自キャッシュを設計** |
| 作成方法 | **クラスターキャッシュ** |
| クラスターモード | **無効** |
| 名前 | `quiz-app-valkey` |
| エンジン | **Valkey** |
| エンジンバージョン | 7.2（最新の Valkey 版） |
| ノードのタイプ | **cache.t4g.micro** |
| レプリカ数 | 0（開発構成。本番時に 1 以上） |

2. **接続:**

| 設定項目 | 値 |
|---|---|
| サブネットグループ | `quiz-redis-subnet` |
| セキュリティグループ | `quiz-redis-sg` |

3. **「作成」** → 作成完了まで **3〜5 分** 待つ

4. ステータスが **「available」** になったら、クラスター名をクリックして **エンドポイント** を控える:
   - **プライマリエンドポイント** の値（ポート番号は除く）
   - 例: `quiz-app-valkey.xxxx.0001.apne1.cache.amazonaws.com`
   - 以降 `$REDIS_ENDPOINT` として参照（Valkey も Redis 互換の接続 URL を使用）

> **注記**: Valkey は Redis と互換性があるため、アプリケーション側の `REDIS_URL` 設定はそのまま使用できます。
> **重要**: ElastiCache Valkey はデフォルトで **TLS（転送中の暗号化）が有効** です。そのため `REDIS_URL` は `redis://` ではなく **`rediss://`**（s が 2 つ）を指定してください。`redis://` のままだと接続がタイムアウトします。

<details>
<summary>CLI で実行する場合</summary>

```bash
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name quiz-valkey-subnet \
  --cache-subnet-group-description "Quiz app Valkey subnet group" \
  --subnet-ids $PRIVATE_SUBNET_A $PRIVATE_SUBNET_C

aws elasticache create-cache-cluster \
  --cache-cluster-id quiz-app-valkey \
  --cache-node-type cache.t4g.micro \
  --engine valkey --engine-version 7.2 \
  --num-cache-nodes 1 \
  --cache-subnet-group-name quiz-valkey-subnet \
  --security-group-ids $REDIS_SG_ID

aws elasticache wait cache-cluster-available --cache-cluster-id quiz-app-valkey

aws elasticache describe-cache-clusters --cache-cluster-id quiz-app-valkey \
  --show-cache-node-info \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' --output text
```
</details>

---

## 6. MS3: バックエンド改修

Phase 2 のコードをそのまま AWS で動かせるように、以下の変更を行う。

### 6.1 依存パッケージの追加

`requirements.txt` に以下を追加:

```
# Phase 3 追加
asyncpg>=0.29.0          # PostgreSQL 非同期ドライバ
redis[hiredis]>=5.0.0     # Redis クライアント
boto3>=1.34.0             # AWS SDK（S3 画像アップロード用）
```

### 6.2 データベース接続の変更

`app/config.py` を更新して、環境変数で DB URL を切り替え可能にする:

```python
# DATABASE_URL の例:
# ローカル: sqlite+aiosqlite:///data/quiz.db
# AWS:     postgresql+asyncpg://quizadmin:PASSWORD@RDS_ENDPOINT:5432/quizapp
```

Phase 2 では SQLAlchemy を使っているため、**DB URL を変更するだけ**で PostgreSQL に接続できる。
主な注意点:

| 項目 | SQLite | PostgreSQL | 対応 |
|---|---|---|---|
| ドライバ | `aiosqlite` | `asyncpg` | `DATABASE_URL` の変更のみ |
| BOOLEAN 型 | INTEGER (0/1) | native BOOLEAN | SQLAlchemy が吸収 |
| 日時型 | TEXT | TIMESTAMP | SQLAlchemy Column 型を `DateTime` に統一 |
| 自動採番 | ROWID | SERIAL / SEQUENCE | UUID を使用しているため影響なし |
| JSON 型 | TEXT | JSONB | `payload` カラムは TEXT のままでも可 |

### 6.3 Valkey 対応（WebSocket Pub/Sub）

`app/ws/` に Valkey ベースのマネージャーを追加:

```
app/ws/
├── manager.py           # 既存（インメモリ接続管理）— ローカル用
└── valkey_manager.py    # 新規（Valkey Pub/Sub）— AWS 用
```

**Valkey の用途:**

| 用途 | キー例 | 説明 |
|---|---|---|
| WebSocket Pub/Sub | `channel:event:{event_id}` | 複数 ECS タスク間でイベントをブロードキャスト（Valkey Pub/Sub） |
| セッションストア | `session:{session_id}` | （任意）DB のセッションテーブルの代替 |
| 問題配信時刻 | `delivered:{event_id}:{question_id}:{user_id}` | `delivered_at` のユーザ別記録 |

### 6.4 S3 画像アップロード

Phase 2 ではローカルの `/uploads/` に保存していた画像を S3 に保存するように変更する。

```python
# app/services/image_service.py（変更イメージ）
import boto3

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'quiz-app-assets')

async def upload_image(file) -> str:
    key = f"images/{uuid4()}{ext}"
    s3.upload_fileobj(file, BUCKET_NAME, key, ExtraArgs={'ContentType': content_type})
    return f"https://{CLOUDFRONT_DOMAIN}/{key}"
```

### 6.5 ヘルスチェックエンドポイント

ALB のターゲットグループで使用するヘルスチェック用エンドポイントを追加:

```python
# app/routers/health.py
@router.get("/health")
async def health():
    return {"status": "ok"}
```

### 6.6 Alembic マイグレーション

```bash
cd backend

# Alembic 初期化（未実施の場合）
alembic init alembic

# alembic/env.py を編集して SQLAlchemy モデルを読み込む
# マイグレーションファイルを自動生成
alembic revision --autogenerate -m "initial schema"

# マイグレーション実行（AWS デプロイ時）
alembic upgrade head
```

---

## 7. MS4: コンテナ化 & ECR

### 7.1 Dockerfile の修正

バックエンドの `Dockerfile` を本番向けに調整:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

EXPOSE 8000

# 本番では workers を増やす（CPU コア数に合わせる）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### 7.2 ECR リポジトリの作成

**コンソール操作: ECR → リポジトリ → リポジトリを作成**

1. 検索バーで **「ECR」**（Elastic Container Registry）を開く
2. **「リポジトリを作成」** ボタン

| 設定項目 | 値 |
|---|---|
| 可視性 | **プライベート** |
| リポジトリ名 | `quiz-app-backend` |
| イメージスキャン | **プッシュ時にスキャン** を有効化 |

3. **「リポジトリを作成」**
4. 作成されたリポジトリの **URI** を控える:
   - 例: `123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/quiz-app-backend`
   - 以降 `$ECR_URI` として参照

### 7.3 Docker イメージのビルド & プッシュ

ECR のリポジトリ画面で **「プッシュコマンドの表示」** ボタンを押すと、
そのまま使えるコマンドが表示されます。以下はその内容です:

```bash
# 1. ECR にログイン（コンソールの「プッシュコマンドの表示」からコピー推奨）
aws ecr get-login-password --region ap-northeast-1 | \
  docker login --username AWS --password-stdin 123456789012.dkr.ecr.ap-northeast-1.amazonaws.com

# 2. Docker イメージをビルド（M1/M2 Mac の場合は --platform を指定）
docker build --platform linux/amd64 -t quiz-app-backend ./backend

# 3. タグ付け
docker tag quiz-app-backend:latest $ECR_URI:latest

# 4. プッシュ
docker push $ECR_URI:latest
```

> **M1/M2 Mac の注意**: `--platform linux/amd64` を必ず指定してください。
> ECS Fargate は x86_64 で動作するため、ARM イメージでは起動しません。

---

## 8. MS5: ECS Fargate デプロイ

### 8.0 ECS Service Linked Role の作成（必須）

ECS クラスターを作成する前に、**ECS service linked role** を作成する必要があります。このロールは AWS が ECS サービス自体を実行するために使用します。

#### 方法 1: CLI で作成（推奨）

```bash
aws iam create-service-linked-role --aws-service-name ecs.amazonaws.com

# 出力例：
# {
#   "Role": {
#     "Arn": "arn:aws:iam::ACCOUNT_ID:role/aws-service-role/ecs.amazonaws.com/AWSServiceRoleForECS"
#   }
# }
```

> **注**: ロールが既に存在する場合は「already exists」というエラーが表示されます。その場合は無視して次に進んでください。

#### 方法 2: コンソールから作成

1. AWS コンソール → 検索バーで **「IAM」** を開く
2. 左メニュー **「ロール」** → **「ロールを作成」**
3. 信頼されたエンティティタイプ: **「AWS のサービス」**
4. ユースケース: 検索バーで **「ECS」** と入力
5. **「Elastic Container Service」** を選択 → **「次へ」**
6. **「次へ」** → ロール名: **`AWSServiceRoleForECS`** → **「ロールを作成」**

---

### 8.1 IAM ロールの作成（ECS タスク用）

> **前提**: セクション 8.0 で ECS service linked role を作成済みであることを確認してください。

ECS タスクには **2 つの IAM ロール** が必要です（これは 8.0 の service linked role とは別です）。

**コンソール操作: IAM → ロール → ロールを作成**

1. 検索バーで **「IAM」** を開く → 左メニュー **「ロール」** → **「ロールを作成」**

#### (1) タスク実行ロール: `quiz-ecs-execution-role`

ECS 自身がイメージ取得やログ送信に使うロールです。

| 設定項目 | 値 |
|---|---|
| 信頼されたエンティティタイプ | **AWS のサービス** |
| ユースケース | **Elastic Container Service** → **Elastic Container Service Task** |

2. **「次へ」** → 許可ポリシーの検索で以下を追加:
   - `AmazonECSTaskExecutionRolePolicy`（検索してチェック）
3. ロール名: `quiz-ecs-execution-role` → **「ロールを作成」**

**Secrets Manager アクセスポリシーの追加（任意）:**

4. 作成したロールを開く → **「許可を追加」** → **「インラインポリシーを作成」**
5. **JSON** タブに切り替えて以下を貼り付け:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": "arn:aws:secretsmanager:ap-northeast-1:*:secret:quiz-app/*"
    }
  ]
}
```

6. ポリシー名: `SecretsManagerAccess` → **「ポリシーの作成」**

#### (2) タスクロール: `quiz-ecs-task-role`

アプリケーション自身が S3 等にアクセスするためのロールです。

1. **「ロールを作成」** → 信頼されたエンティティ: **AWS のサービス** → **Elastic Container Service Task**
2. 許可ポリシー: 何も追加せずに **「次へ」**
3. ロール名: `quiz-ecs-task-role` → **「ロールを作成」**

**S3 アクセスポリシーの追加:**

4. 作成したロールを開く → **「許可を追加」** → **「インラインポリシーを作成」**
5. JSON:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::quiz-app-assets-*/*"
    }
  ]
}
```

6. ポリシー名: `S3Access` → **「ポリシーの作成」**

<details>
<summary>CLI で実行する場合</summary>

```bash
# 信頼ポリシー
cat > /tmp/ecs-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "ecs-tasks.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# 実行ロール
aws iam create-role --role-name quiz-ecs-execution-role \
  --assume-role-policy-document file:///tmp/ecs-trust-policy.json
aws iam attach-role-policy --role-name quiz-ecs-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# タスクロール
aws iam create-role --role-name quiz-ecs-task-role \
  --assume-role-policy-document file:///tmp/ecs-trust-policy.json
```
</details>

### 8.2 CloudWatch ロググループの作成

**コンソール操作: CloudWatch → ロググループ → ロググループの作成**

1. 検索バーで **「CloudWatch」** を開く
2. 左メニュー **「ログ」** → **「ロググループ」** → **「ロググループの作成」**
3. ロググループ名: `/ecs/quiz-app-backend` → **「作成」**

### 8.3 ECS クラスターの作成

**コンソール操作: ECS → クラスター → クラスターの作成**

1. 検索バーで **「ECS」**（Elastic Container Service）を開く
2. **「クラスターの作成」**

| 設定項目 | 値 |
|---|---|
| クラスター名 | `quiz-app-cluster` |
| インフラストラクチャ | **AWS Fargate** のみチェック |

3. **「作成」**

### 8.4 タスク定義の作成

**コンソール操作: ECS → タスク定義 → 新しいタスク定義の作成**

1. 左メニュー **「タスク定義」** → **「新しいタスク定義の作成」**

#### 基本設定

| 設定項目 | 値 |
|---|---|
| タスク定義ファミリー | `quiz-app-backend` |
| 起動タイプ | **AWS Fargate** |
| OS / アーキテクチャ | Linux/X86_64 |
| タスクサイズ — CPU | **0.25 vCPU** |
| タスクサイズ — メモリ | **0.5 GB** |
| タスク実行ロール | `quiz-ecs-execution-role` |
| タスクロール | `quiz-ecs-task-role` |

#### コンテナの定義

**「コンテナ - 1」** セクション:

| 設定項目 | 値 |
|---|---|
| コンテナ名 | `backend` |
| イメージ URI | `（ECR の URI）:latest` |
| コンテナポート | `8000`、プロトコル: TCP |

**環境変数** （「環境変数を追加」で 1 つずつ追加）:

| キー | 値 |
|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://quizadmin:PASSWORD@（RDS エンドポイント）:5432/quizapp` |
| `REDIS_URL` | `rediss://（Valkey エンドポイント）:6379/0` |
| `S3_BUCKET_NAME` | `quiz-app-assets-（アカウントID）` |
| `CORS_ORIGINS` | `https://（CloudFront ドメイン）` |
| `ADMIN_PASSWORD` | （初期管理者パスワード） |

> **重要**: `PASSWORD` は実際の RDS マスターパスワードに置き換えてください。
>
> **重要**: `CORS_ORIGINS` には CloudFront のディストリビューションドメイン（例: `https://dxxxxxxxxxx.cloudfront.net`）を設定してください。プレースホルダーのままだと、ブラウザが Cookie を保存できず Admin API が 401 になります。
>
> **重要**: `REDIS_URL` は `rediss://`（s が 2 つ）を指定してください。ElastiCache Valkey はデフォルトで TLS 有効のため、`redis://` では接続がタイムアウトします。

**ログ設定:**

| 設定項目 | 値 |
|---|---|
| ログドライバー | `awslogs` |
| awslogs-group | `/ecs/quiz-app-backend` |
| awslogs-region | `ap-northeast-1` |
| awslogs-stream-prefix | `ecs` |

**ヘルスチェック:**

| 設定項目 | 値 |
|---|---|
| コマンド | `CMD-SHELL, python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1` |
| 間隔 | 30 |
| タイムアウト | 5 |
| 再試行回数 | 3 |
| 開始期間 | 60 |

2. **「作成」**

### 8.5 ALB（ロードバランサー）の作成

**コンソール操作: EC2 → ロードバランサー → ロードバランサーの作成**

1. 検索バーで **「EC2」** を開く → 左メニュー **「ロードバランサー」**
2. **「ロードバランサーの作成」** → **Application Load Balancer** を選択

| 設定項目 | 値 |
|---|---|
| 名前 | `quiz-app-alb` |
| スキーム | **インターネット向け** |
| IP アドレスタイプ | IPv4 |
| VPC | `quiz-app-vpc` |
| マッピング | `ap-northeast-1a` → `quiz-public-a`、`ap-northeast-1c` → `quiz-public-c` |
| セキュリティグループ | `quiz-alb-sg` |

3. **「リスナーとルーティング」** セクション:
   - プロトコル: HTTP、ポート: 80
   - **「ターゲットグループの作成」** リンクをクリック（新しいタブで開く）

#### ターゲットグループの作成

| 設定項目 | 値 |
|---|---|
| ターゲットタイプ | **IP アドレス**（Fargate では IP タイプが必要） |
| ターゲットグループ名 | `quiz-app-tg` |
| プロトコル / ポート | HTTP / 8000 |
| VPC | `quiz-app-vpc` |
| ヘルスチェックパス | `/api/health` |
| ヘルスチェック間隔 | 30 秒 |
| 正常のしきい値 | 2 |
| 異常のしきい値 | 3 |

4. **「次へ」** → ターゲットの登録はスキップ（ECS サービスが自動登録する） → **「ターゲットグループの作成」**

5. ALB 作成画面に戻り、リスナーのターゲットグループで `quiz-app-tg` を選択
6. **「ロードバランサーの作成」**

**維持設定の有効化（WebSocket 用）:**

7. **「ターゲットグループ」** → `quiz-app-tg` を選択
8. **「ターゲット選択設定」** セクションを下にスクロール → **「編集」**
9. **「維持設定をオンにする」** にチェック:
   - クロスゾーン負荷分散: ロードバランサー属性から設定を継承
   - Cookie タイプ: ロードバランサー生成 Cookie
   - 継続時間: `86400` 秒（1 日）
10. **保存**

> **メモ**: ALB の **DNS 名**（例: `quiz-app-alb-xxx.ap-northeast-1.elb.amazonaws.com`）を控えておく。

<details>
<summary>CLI で実行する場合</summary>

```bash
aws elbv2 create-load-balancer --name quiz-app-alb \
  --subnets $PUBLIC_SUBNET_A $PUBLIC_SUBNET_C \
  --security-groups $ALB_SG_ID --scheme internet-facing --type application

aws elbv2 create-target-group --name quiz-app-tg \
  --protocol HTTP --port 8000 --vpc-id $VPC_ID --target-type ip \
  --health-check-path /api/health --health-check-interval-seconds 30

aws elbv2 modify-target-group-attributes --target-group-arn $TG_ARN \
  --attributes Key=stickiness.enabled,Value=true Key=stickiness.type,Value=lb_cookie \
  Key=stickiness.lb_cookie.duration_seconds,Value=86400

aws elbv2 create-listener --load-balancer-arn $ALB_ARN \
  --protocol HTTP --port 80 --default-actions Type=forward,TargetGroupArn=$TG_ARN
```
</details>

### 8.6 ECS サービスの作成

> **重要**: セクション 8.3「ECS クラスターの作成」とセクション 8.6「ECS サービスの作成」は異なる概念です。
> - **8.3**: コンテナを実行する基盤（箱）を作成
> - **8.6**: その基盤の中で、実際にアプリケーション（タスク）を何個実行するか、ALB と接続するかなどを定義
>
> つまり、8.3 → 8.6 の順番に設定していきます。

**コンソール操作: ECS → クラスター → quiz-app-cluster → サービスを作成**

1. ECS → **「クラスター」** → `quiz-app-cluster` を開く
2. **「サービス」** タブ → **「作成」**

| 設定項目 | 値 |
|---|---|
| 起動タイプ | **FARGATE** |
| タスク定義 — ファミリー | `quiz-app-backend` |
| タスク定義 — リビジョン | **LATEST**（または空白）|
| サービス名 | `quiz-app-backend` |
| 必要なタスク | `1` |

> **重要**: リビジョンは **「LATEST」** または **空白** にしてください。特定の数字（例：「1」）を入力すると、タスク定義を更新してもそのリビジョンが固定されます。

3. **「ネットワーキング」** セクション:

| 設定項目 | 値 |
|---|---|
| VPC | `quiz-app-vpc` |
| サブネット | `quiz-private-a`、`quiz-private-c` |
| セキュリティグループ | **既存のセキュリティグループ** → `quiz-ecs-sg` |
| パブリック IP | **オフ** |

4. **「ロードバランシング」** セクション:

| 設定項目 | 値 |
|---|---|
| ロードバランサータイプ | **Application Load Balancer** |
| ロードバランサー | **`quiz-app-alb`**（8.5 で作成済み） |
| リスナー | **「既存のリスナーを使用」** → **HTTP:80** |
| コンテナ | `backend:8000` |
| ターゲットグループ | **「既存のターゲットグループを使用」** → **`quiz-app-tg`**（8.5 で作成済み） |

> **注意**: リスナーは **「既存のリスナーを使用」** を選択してください。「新しいリスナーを作成」は選ばないでください。ALB はセクション 8.5 で既に作成済みであり、HTTP ポート 80 のリスナーも存在します。

5. **「作成」** → サービスがデプロイされ、タスクが起動するまで待つ

### 8.7 動作確認

1. ECS → `quiz-app-cluster` → **「タスク」** タブでタスクが **RUNNING** になっていることを確認
2. EC2 → **「ターゲットグループ」** → `quiz-app-tg` → **「ターゲット」** タブで **healthy** を確認
3. ブラウザまたは curl で ALB の DNS 名にアクセス:

```bash
curl http://quiz-app-alb-xxx.ap-northeast-1.elb.amazonaws.com/api/health
# → {"status":"ok"} が返れば成功!
```

> **トラブルシューティング**: タスクがすぐ停止する場合は、
> CloudWatch → ロググループ `/ecs/quiz-app-backend` でエラーログを確認してください。

---

## 9. MS6: フロントエンドデプロイ（S3 + CloudFront）

### 9.1 S3 バケットの作成

**コンソール操作: S3 → バケット → バケットを作成**

1. 検索バーで **「S3」** を開く → **「バケットを作成」**

#### (1) SPA ホスティング用バケット

| 設定項目 | 値 |
|---|---|
| バケット名 | `quiz-app-frontend-（アカウントID）` |
| リージョン | ap-northeast-1 |
| パブリックアクセスのブロック | **全てブロック（デフォルトのまま）** |

> バケット名はグローバルで一意にする必要があるため、アカウント ID を末尾に付けます。

2. **「バケットを作成」**

#### (2) 画像アセット用バケット

同様に作成:

| 設定項目 | 値 |
|---|---|
| バケット名 | `quiz-app-assets-（アカウントID）` |

### 9.2 フロントエンドのビルドとアップロード

```bash
cd frontend

# API のベース URL を設定してビルド
VITE_API_BASE_URL=https://your-domain.com npm run build

# S3 にアップロード
aws s3 sync dist/ s3://quiz-app-frontend-（アカウントID）/ --delete

# index.html のキャッシュ制御（SPA なので no-cache）
aws s3 cp dist/index.html s3://quiz-app-frontend-（アカウントID）/index.html \
  --cache-control "no-cache, no-store, must-revalidate"
```

#### アップロード完了を確認

```bash
# S3 バケット内のファイルを確認
aws s3 ls s3://quiz-app-frontend-（アカウントID）/ --recursive
```

**期待される出力（例）:**
```
2026-02-18 23:25:50       2090 assets/index-B67iGfBa.css
2026-02-18 23:25:50     235880 assets/index-DhP4I7VT.js
2026-02-18 23:27:56        393 index.html
```

ファイルが表示されれば、S3 へのアップロード成功です。 ✅

### 9.3 CloudFront ディストリビューションの作成

**コンソール操作: CloudFront → ディストリビューション → ディストリビューションを作成**

1. 検索バーで **「CloudFront」** を開く → **「ディストリビューションを作成」**

#### オリジン 1（S3 — SPA 配信）

| 設定項目 | 値 |
|---|---|
| オリジンドメイン | `quiz-app-frontend-（アカウントID）.s3.ap-northeast-1.amazonaws.com`（ドロップダウンから選択） |
| オリジンアクセス | **Origin Access Control settings (recommended)** |
| OAC | **「コントロール設定を作成」** → デフォルトで OK |

#### デフォルトのキャッシュビヘイビア

| 設定項目 | 値 |
|---|---|
| ビューワープロトコルポリシー | **Redirect HTTP to HTTPS** |
| キャッシュポリシー | **CachingOptimized** |

#### 設定

| 設定項目 | 値 |
|---|---|
| デフォルトルートオブジェクト | `index.html` |
| 代替ドメイン名（CNAME） | （カスタムドメインがあれば設定。なければ空欄） |
| SSL 証明書 | （カスタムドメインがあれば ACM 証明書。なければデフォルト） |

2. **「ディストリビューションを作成」**

> 作成後、**S3 バケットポリシーの更新が必要** という青いバナーが表示されます。
> **「ポリシーをコピー」** ボタンを押して、S3 バケットのバケットポリシーに貼り付けてください。

#### S3 バケットポリシーの設定

3. S3 → `quiz-app-frontend-（アカウントID）` → **「アクセス許可」** タブ
4. **「バケットポリシー」** → **「編集」** → CloudFront が生成したポリシーを貼り付け → **保存**

#### カスタムエラーレスポンスの設定（SPA フォールバック）

React SPA ではどのパスでも `index.html` を返す必要があります。

5. CloudFront → 作成したディストリビューション → **「エラーページ」** タブ
6. **「カスタムエラーレスポンスを作成」** を 2 回実行:

| HTTP エラーコード | レスポンスページのパス | HTTP レスポンスコード |
|---|---|---|
| **403** | `/index.html` | **200** |
| **404** | `/index.html` | **200** |

#### API 用オリジンとビヘイビアの追加

CloudFront で API リクエストも同一ドメインで処理する場合:

7. **「オリジン」** タブ → **「オリジンを作成」**

| 設定項目 | 値 |
|---|---|
| オリジンドメイン | ALB の DNS 名（例: `quiz-app-alb-xxx.ap-northeast-1.elb.amazonaws.com`） |
| プロトコル | **HTTP のみ** |
| HTTP ポート | 80 |

8. **「ビヘイビア」** タブ → **「ビヘイビアを作成」**

| 設定項目 | 値 |
|---|---|
| パスパターン | `/api/*` |
| オリジン | ALB オリジン |
| ビューワープロトコルポリシー | **Redirect HTTP to HTTPS** |
| キャッシュポリシー | **CachingDisabled** |
| オリジンリクエストポリシー | **AllViewer** |

> **WebSocket について**: CloudFront は WebSocket をネイティブにサポートしていません。
> WebSocket は ALB に直接接続する構成を推奨します（下記参照）。

#### WebSocket 接続先について

**方式 A: WebSocket は ALB に直接接続（推奨・シンプル）**

| 通信 | 接続先 |
|---|---|
| SPA | `https://（CloudFront ドメイン）/` |
| API | `https://（CloudFront ドメイン）/api/` |
| WebSocket | `wss://（ALB ドメイン）/api/ws`（ALB に直接接続） |

ALB にも ACM 証明書を設定して HTTPS/WSS 対応が必要です（MS7 で設定）。

> **メモ**: CloudFront のディストリビューション ID と ドメイン名を控えておく。
> ドメイン名の例: `dxxxxxxxxxx.cloudfront.net`

<details>
<summary>CLI で S3 バケットポリシーを設定する場合</summary>

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)

cat > /tmp/s3-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipal",
      "Effect": "Allow",
      "Principal": { "Service": "cloudfront.amazonaws.com" },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::quiz-app-frontend-${ACCOUNT_ID}/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::${ACCOUNT_ID}:distribution/${CF_DIST_ID}"
        }
      }
    }
  ]
}
EOF

aws s3api put-bucket-policy \
  --bucket quiz-app-frontend-$ACCOUNT_ID \
  --policy file:///tmp/s3-policy.json
```
</details>

---

## 10. MS7: HTTPS & ドメイン設定

> **⚠️ 重要**: カスタムドメイン（`kodama.com` など）を所有していない場合は、**このセクション 10.1～10.3 全体をスキップ** してください。
> AWS CloudFront のデフォルトドメイン（`dxxxxxx.cloudfront.net`）は、AWS が自動で HTTPS サポートしているため、追加の証明書設定は不要です。
>
> **スキップ条件：**
> - CloudFront: `dxxxxxx.cloudfront.net`（AWS 自動 HTTPS）
> - ALB: HTTP のまま使用
> - フロント ← CloudFront → ALB のルーティングは 9.3 で設定済み
>
> → **次へ進む：セクション 11（MS8: 動作検証）**

### 10.1 ACM 証明書の取得

#### カスタムドメインがある場合

**SSL/TLS 証明書の役割：**

| 通信経路 | 役割 | 検証者 |
|---|---|---|
| **ブラウザ ← → CloudFront** | ユーザーとの通信を暗号化 | ブラウザが検証（🔒 マーク表示） |
| **CloudFront ← → ALB** | サーバー間通信を暗号化 | CloudFront が検証（ユーザーには見えない） |

つまり、ブラウザが確認するのは CloudFront の証明書だけ。ALB の証明書は CloudFront が内部で検証しています。

---

**コンソール操作: ACM → 証明書をリクエスト**

> **重要**: CloudFront 用の証明書は **バージニア北部（us-east-1）** で作成する必要があります。
> ALB 用の証明書は **東京（ap-northeast-1）** で作成します。

##### CloudFront 用証明書（us-east-1 で作成）

1. コンソール右上のリージョンを **「バージニア北部」** に変更
2. 検索バーで **「ACM」**（Certificate Manager）を開く
3. **「証明書をリクエスト」**

| 設定項目 | 値 |
|---|---|
| 証明書タイプ | **パブリック証明書** |
| ドメイン名 | `your-domain.com` |
| 別名を追加 | `*.your-domain.com` |
| 検証方法 | **DNS 検証** |

4. **「リクエスト」**
5. 証明書の詳細画面に **CNAME レコード** が表示される
6. DNS レジストラ（お名前.com、Route 53 等）で CNAME レコードを追加
7. 検証完了まで数分〜数十分待つ（ステータスが **「発行済み」** になれば OK）

##### ALB 用証明書（ap-northeast-1 で作成）

8. リージョンを **「東京」** に戻す
9. 同様に証明書をリクエスト（ドメイン: `api.your-domain.com` or `your-domain.com`）

#### カスタムドメインがない場合

**このセクション全体をスキップしてください。** ✅

**理由：**
- CloudFront のデフォルトドメイン（`dxxxxxx.cloudfront.net`）は AWS が HTTPS を自動提供
- ALB は HTTP のままで OK（CloudFront → ALB は内部通信）
- セクション 9.3 で `/api/*` ビヘイビアを設定済み → CORS は不要（同一ドメイン扱い）

**次へ進む：セクション 11（MS8: 動作検証）**

### 10.2 ALB に HTTPS リスナーを追加

**コンソール操作: EC2 → ロードバランサー → quiz-app-alb → リスナーの追加**

1. EC2 → **「ロードバランサー」** → `quiz-app-alb` を選択
2. **「リスナーとルール」** タブ → **「リスナーの追加」**

| 設定項目 | 値 |
|---|---|
| プロトコル | HTTPS |
| ポート | 443 |
| デフォルトアクション | 転送先: `quiz-app-tg` |
| セキュリティポリシー | デフォルト（推奨ポリシー） |
| SSL/TLS 証明書 | ACM から `your-domain.com` の証明書を選択 |

3. **「追加」**

**HTTP → HTTPS リダイレクトの設定:**

4. 既存の HTTP:80 リスナーを選択 → **「リスナーの編集」**
5. デフォルトアクションを **「リダイレクト先」** に変更:
   - プロトコル: HTTPS
   - ポート: 443
   - ステータスコード: 301
6. **保存**

### 10.3 DNS レコードの設定

#### Route 53 の場合

**コンソール操作: Route 53 → ホストゾーン → レコードを作成**

| レコード名 | タイプ | ルーティング | 値 |
|---|---|---|---|
| `your-domain.com` | A（エイリアス） | - | CloudFront ディストリビューション |
| `api.your-domain.com` | A（エイリアス） | - | ALB |

#### 他のレジストラの場合

| レコード名 | タイプ | 値 |
|---|---|---|
| `your-domain.com` | CNAME | `dxxxxxxxxxx.cloudfront.net` |
| `api.your-domain.com` | CNAME | `quiz-app-alb-xxx.ap-northeast-1.elb.amazonaws.com` |

<details>
<summary>CLI で実行する場合</summary>

```bash
# CloudFront 用証明書（us-east-1）
aws acm request-certificate --domain-name "your-domain.com" \
  --subject-alternative-names "*.your-domain.com" \
  --validation-method DNS --region us-east-1

# ALB 用証明書（ap-northeast-1）
aws acm request-certificate --domain-name "api.your-domain.com" \
  --validation-method DNS --region ap-northeast-1

# ALB に HTTPS リスナーを追加
aws elbv2 create-listener --load-balancer-arn $ALB_ARN \
  --protocol HTTPS --port 443 \
  --certificates CertificateArn=$CERT_ARN_ALB \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN

# HTTP → HTTPS リダイレクト
aws elbv2 modify-listener --listener-arn $LISTENER_ARN \
  --default-actions '[{"Type":"redirect","RedirectConfig":{"Protocol":"HTTPS","Port":"443","StatusCode":"HTTP_301"}}]'
```
</details>

---

## 11. MS8: 動作検証 & 本番調整

### 11.1 デプロイ後の動作確認チェックリスト

#### インフラ確認

- [x] ECS → クラスター → タスクが **RUNNING**
- [x] EC2 → ターゲットグループ → ターゲットが **healthy**
- [x] CloudWatch → ロググループにログが出力されている
- [x] RDS → DB インスタンスが **利用可能**
- [x] ElastiCache → クラスターが **available**

#### アクセス URL の確認方法

機能確認の前に、CloudFront と ALB のドメイン名を調べます。

**CloudFront のドメイン名を調べる：**
```bash
aws cloudfront list-distributions --query 'DistributionList.Items[?Comment==`quiz-app-frontend`].DomainName' --output text
# 出力例: dxxxxxxxxxx.cloudfront.net
```

またはコンソール：
1. CloudFront → ディストリビューション → `quiz-app-frontend`
2. **「ドメイン名」** をコピー

**ALB のドメイン名を調べる：**
```bash
aws elbv2 describe-load-balancers --names quiz-app-alb --region ap-northeast-1 --query 'LoadBalancers[0].DNSName' --output text
# 出力例: quiz-app-alb-xxx.ap-northeast-1.elb.amazonaws.com
```

またはコンソール：
1. EC2 → ロードバランサー → `quiz-app-alb`
2. **「DNS 名」** をコピー

---

#### 機能確認（ユーザ側）

**アクセス URL：**
- **フロント**: `https://（CloudFront のドメイン名）/`
- **API**: `https://（CloudFront のドメイン名）/api/health`
- **WebSocket**: `wss://（ALB のドメイン名）/api/ws`

**チェックリスト：**

- [ ] **API ヘルスチェック**
  ```bash
  curl https://（CloudFront のドメイン名）/api/health
  # 応答: {"status":"ok"} が返れば OK ✅
  ```
  **確認内容：** CloudFront → ALB → ECS のルーティングが正常

- [x] **トップページが HTTPS で表示される**
  - ブラウザで `https://（CloudFront のドメイン名）/` にアクセス
  - React SPA が表示される
  - URL バーに 🔒 マークが表示される

- [x] **WebSocket が接続される（wss://）**
  1. クイズページを開く
  2. Chrome DevTools（F12 キー）→ **ネットワークタブ**
  3. **フィルタ** から **WS** を選択
  4. WebSocket 接続が表示されるか確認
  5. ステータス: **101 Switching Protocols** ✅

  **確認内容：** ALB に直接 WebSocket 接続されている

- [x] **参加コード入力 → 登録 → クイズページへ遷移**
  - 参加コードを入力してフォーム送信
  - API が正常に DB にデータを保存する
  - クイズページに遷移する

- [x] **問題が表示され、回答できる**
  - WebSocket からリアルタイムで問題が配信される
  - 回答選択肢が表示される
  - 回答ボタンで送信できる

- [x] **タイマーが正常に動作する**
  - 制限時間がカウントダウンされる
  - 時間経過でページが更新される

- [x] **結果ページが表示される**
  - イベント終了後、スコア・ランキングが表示される

- [x] **ログアウトが動作する**
  - ログアウトボタンでセッションが破棄される
  - ログイン画面に戻る

#### 機能確認（管理者側）

- [x] 管理者ログインが動作する
- [x] イベント作成が動作する
- [x] 問題の CRUD が動作する
- [ ] 画像アップロードが S3 に保存される
- [x] イベント進行（Start → Next → Close → Reveal → Finish）が動作する
- [x] オートモードが動作する
- [x] CSV エクスポートが動作する

### 11.2 フロントエンドの環境変数設定

`frontend/src/` 内の API 接続先を環境変数で切り替える:

```javascript
// src/api/client.js
const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
const WS_BASE = import.meta.env.VITE_WS_BASE_URL || `ws://${window.location.host}`;
```

ビルド時の環境変数:

```bash
# ローカル開発（デフォルト）
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000

# AWS デプロイ
VITE_API_BASE_URL=https://your-domain.com
VITE_WS_BASE_URL=wss://api.your-domain.com
```

### 11.3 再デプロイ手順

#### バックエンドの再デプロイ

```bash
# 1. Docker イメージをビルド
docker build --platform linux/amd64 -t quiz-app-backend ./backend

# 2. タグ付け & プッシュ
docker tag quiz-app-backend:latest $ECR_URI:latest
docker push $ECR_URI:latest

# 3. ECS サービスを強制再デプロイ（新しいイメージを取得）
aws ecs update-service \
  --cluster quiz-app-cluster \
  --service quiz-app-backend \
  --force-new-deployment

# 4. デプロイ完了を待つ
aws ecs wait services-stable --cluster quiz-app-cluster --services quiz-app-backend
echo "デプロイ完了!"
```

> **コンソールで再デプロイする場合:**
> ECS → クラスター → `quiz-app-backend` サービス → **「サービスを更新」** →
> **「新しいデプロイの強制」** にチェック → **「サービスを更新」**

#### フロントエンドの再デプロイ

```bash
# 1. ビルド
cd frontend && npm run build

# 2. S3 にアップロード
aws s3 sync dist/ s3://quiz-app-frontend-$ACCOUNT_ID/ --delete

# 3. CloudFront キャッシュを無効化
aws cloudfront create-invalidation \
  --distribution-id $CF_DIST_ID \
  --paths "/*"
```

> **コンソールでキャッシュ無効化する場合:**
> CloudFront → ディストリビューション → **「無効化」** タブ → **「無効化を作成」** →
> オブジェクトパス: `/*` → **「無効化を作成」**

### 11.4 スケーリング設定

#### 手動スケーリング

**コンソール操作: ECS → サービス → サービスを更新**

1. ECS → `quiz-app-cluster` → `quiz-app-backend` サービス
2. **「サービスを更新」**
3. **「必要なタスク」** を `2` に変更 → **「サービスを更新」**

#### Auto Scaling の設定

**コンソール操作: ECS → サービス → サービスを更新 → Service auto scaling**

1. **「Service auto scaling」** セクションを展開
2. **「Service auto scaling を使用」** にチェック

| 設定項目 | 値 |
|---|---|
| 最小タスク数 | 1 |
| 最大タスク数 | 4 |

3. **「スケーリングポリシーを追加」**:

| 設定項目 | 値 |
|---|---|
| ポリシータイプ | ターゲットの追跡 |
| ポリシー名 | `quiz-cpu-scaling` |
| ECS サービスメトリクス | `ECSServiceAverageCPUUtilization` |
| ターゲット値 | 70 |
| スケールアウトクールダウン | 60 秒 |
| スケールインクールダウン | 120 秒 |

4. **「サービスを更新」**

<details>
<summary>CLI で実行する場合</summary>

```bash
aws ecs update-service --cluster quiz-app-cluster --service quiz-app-backend --desired-count 2

aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/quiz-app-cluster/quiz-app-backend \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 --max-capacity 4

aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/quiz-app-cluster/quiz-app-backend \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name quiz-cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 120
  }'
```
</details>

### 11.5 監視・アラート

**コンソール操作: CloudWatch → アラーム → アラームの作成**

1. CloudWatch → **「アラーム」** → **「アラームの作成」**
2. **「メトリクスの選択」** → ECS → ClusterName, ServiceName → `RunningTaskCount`
3. 条件: `1 より小さい` → 評価期間: 2
4. アクション: SNS トピック（メール通知）を設定（任意）
5. アラーム名: `quiz-ecs-running-tasks` → **「アラームの作成」**

---

## 12. コスト最適化のヒント

### 12.1 開発 / テスト時

| 項目 | 推奨 |
|---|---|
| RDS | Single-AZ の `db.t4g.micro`（無料利用枠対象の場合あり） |
| ElastiCache | Single Node の `cache.t4g.micro` |
| ECS | タスク数 1、0.25 vCPU / 0.5 GB |
| NAT Gateway | 1 つのみ（Single-AZ） |
| CloudFront | 開発中は ALB 直接でも可（CloudFront 不要） |

### 12.2 使わないときはリソースを停止

**ECS タスクの停止（コンソール）:**

1. ECS → `quiz-app-cluster` → `quiz-app-backend` → **「サービスを更新」**
2. 必要なタスクを **0** に変更 → **更新**

**RDS の一時停止（コンソール）:**

1. RDS → `quiz-app-db` → **「アクション」** → **「一時的に停止」**
2. ※ 最大 7 日間。7 日後に自動で再起動されます。

**再開:**

1. RDS → **「アクション」** → **「起動」**
2. ECS → 必要なタスクを **1** に変更

<details>
<summary>CLI で実行する場合</summary>

```bash
# 停止
aws ecs update-service --cluster quiz-app-cluster --service quiz-app-backend --desired-count 0
aws rds stop-db-instance --db-instance-identifier quiz-app-db

# 再開
aws rds start-db-instance --db-instance-identifier quiz-app-db
aws ecs update-service --cluster quiz-app-cluster --service quiz-app-backend --desired-count 1
```
</details>

---

## 13. リソース削除（クリーンアップ）

全リソースを削除してコスト発生を止める手順です。
**削除順序が重要**（依存関係があるため）。コンソールと CLI を併用するのが最も確実です。

### 重要な注意事項

⚠️ **削除前の確認:**
- すべての作業を**正しいリージョン**で実施してください（例: ap-northeast-1）
- リージョンが違うとリソースが見つからないことがあります
- デフォルトVPCは削除しないでください（将来的に必要になる可能性があります）

⚠️ **課金を早く止めるための優先順位:**
1. **時間課金リソース**: RDS, ElastiCache, NAT Gateway, ECS
2. **ストレージ課金**: S3, ECR
3. **その他**: CloudWatch Logs, IAM（課金なし）

### 削除順序（フェーズ別）

#### **フェーズ1: アプリケーション層（最優先）**

| 順番 | リソース | 操作場所 | 手順 | 注意事項 |
|---|---|---|---|---|
| 1 | **ECS サービス** | ECS コンソール | サービス選択 → 削除 → 「強制削除」にチェック | タスク数が0になることを確認 |
| 2 | **ECS タスク定義** | ECS コンソール | 各リビジョンを登録解除 | 課金対象ではないため急がなくてOK |
| 3 | **ECS クラスター** | ECS コンソール | クラスター → 削除 | サービスが完全に削除されてから |

#### **フェーズ2: ネットワーク/配信層**

| 順番 | リソース | 操作場所 | 手順 | 注意事項 |
|---|---|---|---|---|
| 4 | **ALB** | EC2 コンソール | ロードバランサー → 削除 | リスナーも自動削除される |
| 5 | **ターゲットグループ** | EC2 コンソール | ターゲットグループ → 削除 | ALB削除後に実施 |
| 6 | **CloudFront** | CloudFront コンソール | 無効化 → 15-20分待つ → 削除 | **注意**: 下記の「CloudFront削除の注意点」参照 |

#### **フェーズ3: データ層（時間課金）**

| 順番 | リソース | 操作場所 | 手順 | 注意事項 |
|---|---|---|---|---|
| 7 | **ElastiCache** | ElastiCache コンソール | Redis OSS caches → クラスター削除 | 「最終バックアップを作成」のチェックを外す |
| 8 | **RDS** | RDS コンソール | DB インスタンス → 削除 | スナップショット不要、自動バックアップ保持も無効化 |

#### **フェーズ4: ストレージ/イメージ**

| 順番 | リソース | 操作場所 | 手順 | 注意事項 |
|---|---|---|---|---|
| 9 | **S3 バケット（中身）** | S3 コンソール | バケット内のオブジェクトをすべて削除 | バージョニング有効の場合は全バージョン削除 |
| 10 | **S3 バケット（本体）** | S3 コンソール | 空のバケットを削除 | 2つとも削除（frontend, assets） |
| 11 | **ECR イメージ** | ECR コンソール | リポジトリ内のイメージをすべて削除 | - |
| 12 | **ECR リポジトリ** | ECR コンソール | リポジトリを削除 | `--force`で一括削除も可能 |

#### **フェーズ5: ネットワーク基盤**

| 順番 | リソース | 操作場所 | 手順 | 注意事項 |
|---|---|---|---|---|
| 13 | **セキュリティグループ** | VPC コンソール | セキュリティグループ → 削除 | **注意**: 下記の「セキュリティグループ削除の注意点」参照 |
| 14 | **NAT Gateway** | VPC コンソール | NAT ゲートウェイ → 削除 | **時間課金なので優先度高** |
| 15 | **Elastic IP** | VPC コンソール | NAT Gateway削除後に解放 | NAT Gateway削除の数分後に実施 |
| 16 | **VPCエンドポイント** | VPC コンソール | エンドポイント → 削除 | あれば削除 |
| 17 | **ENI** | EC2 コンソール | ネットワークインターフェイス → 削除 | ステータスが`available`のもののみ |
| 18 | **サブネット** | VPC コンソール | サブネットを削除 | 4つすべて削除 |
| 19 | **ルートテーブル** | VPC コンソール | カスタムルートテーブルを削除 | デフォルトRTは削除不可 |
| 20 | **インターネットゲートウェイ** | VPC コンソール | VPCからデタッチ → 削除 | - |
| 21 | **VPC** | VPC コンソール | VPC を削除 | **カスタムVPCのみ削除**（デフォルトVPCは残す） |

#### **フェーズ6: その他**

| 順番 | リソース | 操作場所 | 手順 | 注意事項 |
|---|---|---|---|---|
| 22 | **CloudWatch ロググループ** | CloudWatch コンソール | ロググループ → 削除 | `/ecs/quiz-app-backend`など |
| 23 | **IAM ロール** | IAM コンソール | ロール → ポリシーをデタッチ → 削除 | ECS用の2つのロール |
| 24 | **Secrets Manager** | Secrets Manager コンソール | シークレット → 削除 | 使用していない場合はスキップ |

---

### CloudFront削除の注意点

**問題**: 無料プラン（Free plan）に加入している場合、以下のエラーが出て削除できません。

```
You can't delete this distribution while it's subscribed to a pricing plan.
After you cancel the pricing plan, you can delete the distribution at the end of monthly billing cycle.
```

**対処法:**

1. **プラン管理画面で確認**
   - CloudFront コンソール → ディストリビューション詳細 → 右側の「Manage plan」をクリック
   - 「Changing to pay-as-you-go in X days」と表示されている場合、その日付まで待つ

2. **削除可能になるタイミング**
   - 月次請求サイクルの終わり（通常は月初）
   - 例: 2026年3月1日以降に削除可能

3. **それまでの対応**
   - ディストリビューションを**無効化**しておく（課金なし）
   - 無料プランなので追加課金は発生しない
   - 他のリソースを優先的に削除

---

### セキュリティグループ削除の注意点

**問題**: セキュリティグループ間の循環参照で削除できない場合があります。

**例**: `quiz-ecs-sg`のインバウンドルールが`quiz-alb-sg`を参照している場合

**対処法:**

1. **インバウンド/アウトバウンドルールを先に削除**
   ```bash
   # UIの場合
   EC2 → セキュリティグループ → quiz-ecs-sg → インバウンドルールを編集 → すべて削除
   ```

2. **ENI（ネットワークインターフェース）を確認**
   ```bash
   # ENIの確認
   aws ec2 describe-network-interfaces \
     --filters "Name=group-id,Values=sg-xxxxx" \
     --query 'NetworkInterfaces[*].[NetworkInterfaceId,Status,Description]'
   ```

3. **ステータスが`available`のENIを削除**
   ```bash
   aws ec2 delete-network-interface --network-interface-id eni-xxxxx
   ```

4. **セキュリティグループ本体を削除**
   - 推奨順序: `quiz-ecs-sg` → `quiz-alb-sg` → `quiz-rds-sg` → `quiz-redis-sg`

---

### 最終確認コマンド

すべてのリソースが削除されたことを確認するコマンド集です。

```bash
# === ECS ===
aws ecs list-clusters
# 期待結果: {"clusterArns": []}

# === RDS ===
aws rds describe-db-instances --query 'DBInstances[*].DBInstanceIdentifier'
# 期待結果: []

# === ElastiCache ===
aws elasticache describe-cache-clusters --query 'CacheClusters[*].CacheClusterId'
# 期待結果: []

# === S3 ===
aws s3 ls
# 期待結果: (空 or クイズアプリ以外のバケットのみ)

# === ECR ===
aws ecr describe-repositories --query 'repositories[*].repositoryName'
# 期待結果: []

# === VPC ===
aws ec2 describe-vpcs --query 'Vpcs[*].[VpcId,IsDefault,Tags[?Key==`Name`].Value|[0]]' --output table
# 期待結果: デフォルトVPCのみ（IsDefault=True）

# === NAT Gateway ===
aws ec2 describe-nat-gateways --filter "Name=state,Values=available"
# 期待結果: {"NatGateways": []}

# === CloudWatch Logs ===
aws logs describe-log-groups --query 'logGroups[?contains(logGroupName, `quiz`)].logGroupName'
# 期待結果: []

# === IAM ロール ===
aws iam list-roles --query 'Roles[?contains(RoleName, `quiz`)].RoleName'
# 期待結果: []
```

**複数リージョンでの確認（推奨）:**

```bash
# すべてのリージョンで残存リソースを確認
for region in us-east-1 ap-northeast-1 ap-northeast-3; do
  echo "=== Region: $region ==="
  aws ec2 describe-instances --region $region --query 'Reservations[*].Instances[*].[InstanceId,State.Name]' --output table
  aws rds describe-db-instances --region $region --query 'DBInstances[*].DBInstanceIdentifier' --output table 2>/dev/null
done
```

---

### デフォルトVPCについて

⚠️ **重要**: 以下のようなVPCは**削除しないでください**

```bash
# VPCの確認
aws ec2 describe-vpcs --vpc-ids vpc-xxxxx --query 'Vpcs[*].[VpcId,IsDefault,CidrBlock]'

# 出力例
# vpc-xxxxx | True | 172.31.0.0/16
```

- `IsDefault = True` のVPCはAWSが各リージョンで自動作成する標準VPC
- 削除すると将来的に他のサービスで問題が発生する可能性があります
- カスタムVPC（クイズアプリ用に作成したVPC）のみ削除してください

---

### 課金確認

削除後、数日以内に以下を確認してください:

1. **AWS Cost Explorer**
   - コスト管理 → Cost Explorer → 日次コストを確認
   - クイズアプリ関連のサービスがゼロになっていることを確認

2. **請求ダッシュボード**
   - 請求 → 請求書 → 今月の請求額を確認
   - 削除前の日割り分のみ請求される

3. **CloudWatch アラーム（オプション）**
   - 予算を超えた場合の通知設定を確認

> **ヒント**: VPC を削除する際に「依存関係があります」エラーが出る場合は、
> VPC 内のリソース（ENI、セキュリティグループ等）が残っていないか確認してください。

<details>
<summary>CLI で全削除する場合</summary>

```bash
# 1. ECS
aws ecs update-service --cluster quiz-app-cluster --service quiz-app-backend --desired-count 0
aws ecs delete-service --cluster quiz-app-cluster --service quiz-app-backend --force
aws ecs delete-cluster --cluster quiz-app-cluster

# 2. ALB & ターゲットグループ
aws elbv2 delete-listener --listener-arn $LISTENER_ARN
aws elbv2 delete-load-balancer --load-balancer-arn $ALB_ARN
sleep 30
aws elbv2 delete-target-group --target-group-arn $TG_ARN

# 3. RDS
aws rds delete-db-instance --db-instance-identifier quiz-app-db --skip-final-snapshot

# 4. ElastiCache
aws elasticache delete-cache-cluster --cache-cluster-id quiz-app-redis

# 5. S3
aws s3 rm s3://quiz-app-frontend-$ACCOUNT_ID --recursive
aws s3 rb s3://quiz-app-frontend-$ACCOUNT_ID
aws s3 rm s3://quiz-app-assets-$ACCOUNT_ID --recursive
aws s3 rb s3://quiz-app-assets-$ACCOUNT_ID

# 6. CloudFront（コンソールから無効化→削除が確実）

# 7. NAT Gateway & Elastic IP
aws ec2 delete-nat-gateway --nat-gateway-id $NAT_GW_ID
sleep 120
aws ec2 release-address --allocation-id $EIP_ALLOC_ID

# 8. ECR
aws ecr delete-repository --repository-name quiz-app-backend --force

# 9. セキュリティグループ
aws ec2 delete-security-group --group-id $REDIS_SG_ID
aws ec2 delete-security-group --group-id $RDS_SG_ID
aws ec2 delete-security-group --group-id $ECS_SG_ID
aws ec2 delete-security-group --group-id $ALB_SG_ID

# 10. サブネット・ルートテーブル・IGW・VPC
aws ec2 delete-subnet --subnet-id $PRIVATE_SUBNET_C
aws ec2 delete-subnet --subnet-id $PRIVATE_SUBNET_A
aws ec2 delete-subnet --subnet-id $PUBLIC_SUBNET_C
aws ec2 delete-subnet --subnet-id $PUBLIC_SUBNET_A
aws ec2 delete-route-table --route-table-id $PRIVATE_RT_ID
aws ec2 delete-route-table --route-table-id $PUBLIC_RT_ID
aws ec2 detach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID
aws ec2 delete-internet-gateway --internet-gateway-id $IGW_ID
aws ec2 delete-vpc --vpc-id $VPC_ID

# 11. Secrets Manager
aws secretsmanager delete-secret --secret-id quiz-app/rds-password --force-delete-without-recovery

# 12. IAM ロール
aws iam delete-role-policy --role-name quiz-ecs-task-role --policy-name S3Access
aws iam delete-role --role-name quiz-ecs-task-role
aws iam delete-role-policy --role-name quiz-ecs-execution-role --policy-name SecretsManagerAccess
aws iam detach-role-policy --role-name quiz-ecs-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
aws iam delete-role --role-name quiz-ecs-execution-role

# 13. CloudWatch
aws logs delete-log-group --log-group-name /ecs/quiz-app-backend
```
</details>

---

## 14. Phase 2 → Phase 3 のコード差分まとめ

| ファイル | 変更内容 |
|---|---|
| `requirements.txt` | `asyncpg`, `redis`, `boto3` を追加 |
| `app/config.py` | `REDIS_URL`, `S3_BUCKET_NAME` 等の環境変数を追加 |
| `app/database.py` | DB URL が `postgresql+asyncpg://` の場合の処理を追加（または変更不要） |
| `app/ws/valkey_manager.py` | 新規作成: Valkey Pub/Sub による WS ブロードキャスト |
| `app/ws/manager.py` | Valkey マネージャーへの切り替え対応 |
| `app/services/image_service.py` | S3 へのアップロードに変更 |
| `app/routers/health.py` | 新規作成: `/api/health` ヘルスチェック |
| `Dockerfile` | `HEALTHCHECK` 追加、`--workers 2` に変更 |
| `frontend/src/api/client.js` | 環境変数で API/WS URL を切り替え |
| `frontend/vite.config.js` | 環境変数の設定 |
| `alembic/` | マイグレーション設定 |

---

## 15. トラブルシューティング

### よくある問題と対処法

| 症状 | 原因 | 対処 |
|---|---|---|
| ECS タスクがすぐ停止する | DB/Redis に接続できない | CloudWatch Logs でエラーログを確認。セキュリティグループの設定を見直す |
| ALB ヘルスチェックが unhealthy | `/api/health` が応答しない | ECS タスクのログを確認。ポート 8000 が正しいか確認 |
| WebSocket が接続できない | ALB の設定不足 | ALB ターゲットグループのスティッキーセッションが有効か確認 |
| 画像がアップロードできない | S3 権限不足 | ECS タスクロールの S3 ポリシーを確認 |
| CORS エラー / Admin API が 401 | `CORS_ORIGINS` がプレースホルダーのまま | `CORS_ORIGINS` 環境変数に CloudFront ドメイン（`https://dxxxxxxxxxx.cloudfront.net`）を設定。CORS 不一致だとブラウザが Cookie を保存できない |
| RDS に接続できない | セキュリティグループ | RDS の SG が ECS の SG からの 5432 を許可しているか確認 |
| ECS タスクが `exec format error` で即停止 | Docker イメージのアーキテクチャ不一致 | Apple Silicon Mac では `docker build --platform linux/amd64` を必ず指定。ECS Fargate は x86_64 で動作する |
| ログイン API が 504 Gateway Timeout | Valkey への TLS 接続失敗 | `REDIS_URL` が `redis://` になっていないか確認。ElastiCache Valkey は TLS がデフォルト有効のため `rediss://`（s が 2 つ）を使用する |
| SPA のページが 2 回目以降のリロードで白くなる | `index.html` が CloudFront にキャッシュされている | S3 上の `index.html` に `Cache-Control: no-cache, no-store, must-revalidate` を設定する。`aws s3 cp` の `--cache-control` オプションで設定可能 |

### ログの確認方法

**コンソール操作: CloudWatch → ロググループ → /ecs/quiz-app-backend**

1. CloudWatch → 左メニュー **「ログ」** → **「ロググループ」**
2. `/ecs/quiz-app-backend` をクリック
3. 最新のログストリームをクリック → エラーメッセージを確認

<details>
<summary>CLI で確認する場合</summary>

```bash
# ログストリーム一覧を確認
aws logs describe-log-streams \
  --log-group-name /ecs/quiz-app-backend \
  --order-by LastEventTime --descending --limit 5

# 直近のログを確認
aws logs get-log-events \
  --log-group-name /ecs/quiz-app-backend \
  --log-stream-name "（ログストリーム名）" \
  --limit 100
```
</details>
