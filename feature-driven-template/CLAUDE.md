# プロジェクトメモリ

## このテンプレートについて

既存リポジトリに新機能を追加するためのClaude駆動開発テンプレートです。
新規プロジェクト用ではなく、すでにコードベースが存在するリポジトリに `.claude/` ディレクトリごとコピーして使います。

## 技術スタック

<!-- 対象リポジトリに合わせて記載してください -->

- 開発環境:
- ランタイム:
- 言語:
- パッケージマネージャー:

## 機能追加の基本フロー

1. **アイデア記述**: `ideas/YYYYMMDD_<feature-name>/` にアイデアを書く
2. **設計ドキュメント作成**: `/setup-dev` で要求定義・機能設計・アーキテクチャ設計（変更差分）を生成
3. **実装**: `/add-feature` で機能を実装
4. **記録**: `.steering/` に計画 → 実装 → 振り返りを記録
5. **品質チェック**: `/review-docs` でドキュメントレビュー

## 重要なルール

### ドキュメント作成時

**1ファイルずつ作成し、必ずユーザーの承認を得てから次に進む**

承認待ちの際は、明確に伝える:
```
「[ドキュメント名]の作成が完了しました。内容を確認してください。
承認いただけたら次のドキュメントに進みます。」
```

### 実装前の確認

新しい実装を始める前に、必ず以下を確認:

1. CLAUDE.mdを読む
2. 関連する設計ドキュメント（`docs/YYYYMMDD_<feature-name>/`）を読む
3. Grepで既存の類似実装を検索
4. 既存パターンを理解してから実装開始

### ステアリングファイル管理

作業ごとに `.steering/YYYYMMDD-<タスク名>/` を作成:

- `requirements.md`: 今回の要求内容
- `design.md`: 実装アプローチ
- `tasklist.md`: 具体的なタスクリスト

**作業計画・実装・検証時は`steering`スキルを使用してください。**

- **作業計画時**: `Skill('steering')`でモード1（ステアリングファイル作成）
- **実装時**: `Skill('steering')`でモード2（実装とtasklist.md更新管理）
- **検証時**: `Skill('steering')`でモード3（振り返り）

## ディレクトリ構造

### アイデア（`ideas/`）

```
ideas/
└── YYYYMMDD_<feature-name>/
    └── idea.md          # 自由形式のアイデアメモ
```

- 壁打ち・ブレインストーミングの成果物
- 技術調査メモ
- `/setup-dev` 実行時に自動的に読み込まれる

### 設計ドキュメント（`docs/`）

```
docs/
└── YYYYMMDD_<feature-name>/
    ├── requirements.md       # 要求定義書
    ├── functional-design.md  # 機能設計書
    └── architecture.md       # アーキテクチャ設計書（変更差分を明記）
```

- 機能追加ごとにサブディレクトリを作成
- アーキテクチャ設計書は既存アーキテクチャからの変更差分を重点的に記述

### 作業単位のドキュメント（`.steering/`）

```
.steering/
└── YYYYMMDD-<タスク名>/
    ├── requirements.md   # 作業の要求内容
    ├── design.md         # 変更内容の設計
    └── tasklist.md       # タスクリスト
```

## 使い方

```bash
# 1. アイデアを書く
ideas/20260401_awesome-feature/idea.md

# 2. 設計ドキュメント生成
> /setup-dev 20260401_awesome-feature

# 3. 機能実装
> /add-feature awesome-feature

# 4. ドキュメントレビュー
> /review-docs docs/20260401_awesome-feature/requirements.md
```
