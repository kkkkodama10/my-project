# Claude駆動開発テンプレート

Claude Codeを活用したスペック駆動開発フレームワークのテンプレートです。

ドキュメントファースト → 作業計画 → 実装 → 検証のサイクルを、Claude Codeのスキル・コマンド・エージェントで自動化します。

## セットアップ

### 1. テンプレートをコピー

```bash
cp -r claude-driven-template/ my-new-project/
cd my-new-project/
git init
```

### 2. アイデアを書く

`docs/ideas/` に自由形式でアイデアメモを配置します。

```bash
# 例
vim docs/ideas/initial-requirements.md
```

ブレスト結果、技術調査メモ、やりたいことリストなど何でもOK。

### 3. プロジェクトセットアップ

Claude Codeを起動して以下を実行：

```
/setup-project
```

`docs/ideas/` の内容をもとに、以下の6つの設計書が対話的に生成されます：

| ドキュメント | 内容 |
|---|---|
| `docs/product-requirements.md` | プロダクト要求定義書（PRD） |
| `docs/functional-design.md` | 機能設計書 |
| `docs/architecture.md` | アーキテクチャ設計書 |
| `docs/repository-structure.md` | リポジトリ構造定義書 |
| `docs/development-guidelines.md` | 開発ガイドライン |
| `docs/glossary.md` | ユビキタス言語（用語集） |

### 4. CLAUDE.md の技術スタックを更新

`/setup-project` 完了後、`CLAUDE.md` の `## 技術スタック` セクションをプロジェクトに合わせて記載してください。

## 使い方

### 機能追加

```
/add-feature ユーザー認証
```

自動的に以下が実行されます：

1. `.steering/YYYYMMDD-add-user-auth/` に作業計画を生成
2. `tasklist.md` に従って実装
3. 品質検証（テスト・lint・型チェック）
4. 振り返り記録

### ドキュメントレビュー

```
/review-docs docs/architecture.md
```

5つの観点（完全性・明確性・一貫性・実装可能性・測定可能性）でレビューレポートを生成。

### 日常的な編集

コマンドを使わず、普通に会話で依頼できます：

```
PRDに新機能を追加してください
architecture.mdのパフォーマンス要件を見直して
glossary.mdに新しいドメイン用語を追加
```

## フレームワーク構成

```
├── CLAUDE.md                    # フレームワーク定義
├── docs/
│   └── ideas/                   # アイデアメモ（入力）
├── .claude/
│   ├── settings.json            # スキル許可設定
│   ├── commands/                # ユーザーコマンド
│   │   ├── setup-project.md     #   /setup-project
│   │   ├── add-feature.md       #   /add-feature [名前]
│   │   └── review-docs.md       #   /review-docs [パス]
│   ├── skills/                  # 内部スキル
│   │   ├── steering/            #   作業計画・進捗管理
│   │   ├── prd-writing/         #   PRD作成
│   │   ├── functional-design/   #   機能設計書作成
│   │   ├── architecture-design/ #   アーキテクチャ設計書作成
│   │   ├── repository-structure/#   リポジトリ構造定義書作成
│   │   ├── development-guidelines/ # 開発ガイドライン作成
│   │   └── glossary-creation/   #   用語集作成
│   └── agents/                  # サブエージェント
│       ├── doc-reviewer.md      #   ドキュメント品質レビュー
│       └── implementation-validator.md # 実装品質検証
└── .steering/                   # 作業ドキュメント（自動生成）
```

## ワークフロー概要

```
docs/ideas/ にアイデアを書く
       ↓
/setup-project で6つの設計書を生成
       ↓
/add-feature で機能を実装
       ↓
.steering/ に計画→実装→振り返りを記録
       ↓
/review-docs で品質チェック
```
