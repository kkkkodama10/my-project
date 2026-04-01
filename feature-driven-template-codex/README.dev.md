# Feature-Driven Template (Codex版)

既存リポジトリに新機能を追加するための、Codex CLI駆動開発テンプレートです。

## 想定ユースケース

- AI開発に馴染みがないリポジトリに、Codex CLIで新機能を追加したい
- 設計ドキュメント → 計画 → 実装 → 振り返りのサイクルを自動化したい

## セットアップ

### 1. 既存リポジトリにコピー

```bash
# テンプレートの .codex/, .agents/, ideas/, .steering/, AGENTS.md をコピー
cp -r feature-driven-template-codex/.codex/ your-repo/.codex/
cp -r feature-driven-template-codex/.agents/ your-repo/.agents/
cp -r feature-driven-template-codex/ideas/ your-repo/ideas/
cp -r feature-driven-template-codex/.steering/ your-repo/.steering/
cp feature-driven-template-codex/AGENTS.md your-repo/AGENTS.md
```

### 2. AGENTS.md の技術スタックを更新

`AGENTS.md` の `## 技術スタック` セクションを対象リポジトリに合わせて記載してください。

### 3. アイデアを書く

```bash
mkdir ideas/20260401_awesome-feature
vim ideas/20260401_awesome-feature/idea.md
```

### 4. 設計ドキュメント生成

```
$setup-dev 20260401_awesome-feature
```

以下の3つの設計書が `docs/20260401_awesome-feature/` に生成されます：

| ドキュメント | 内容 |
|---|---|
| `requirements.md` | 要求定義書 |
| `functional-design.md` | 機能設計書 |
| `architecture.md` | アーキテクチャ設計書（既存からの変更差分を明記） |

## 使い方

### 機能実装

```
$add-feature awesome-feature
```

自動的に以下が実行されます：

1. `.steering/YYYYMMDD-awesome-feature/` に作業計画を生成
2. `tasklist.md` に従って実装
3. 品質検証（テスト・lint・型チェック）
4. 振り返り記録

### ドキュメントレビュー

```
$review-docs docs/20260401_awesome-feature/requirements.md
```

完全性・明確性・一貫性・実装可能性・測定可能性の観点でレビュー。

## ワークフロー概要

```
ideas/YYYYMMDD_<feature>/ にアイデアを書く
       |
$setup-dev で3つの設計書を生成
       |
$add-feature で機能を実装
       |
.steering/ に計画 → 実装 → 振り返りを記録
       |
$review-docs で品質チェック
```

## フレームワーク構成

```
├── AGENTS.md                    # フレームワーク定義
├── ideas/                       # アイデアメモ（入力）
│   └── YYYYMMDD_<feature>/
├── docs/                        # 設計ドキュメント（自動生成）
│   └── YYYYMMDD_<feature>/
├── .codex/
│   ├── config.toml              # Codex CLI設定
│   └── agents/                  # サブエージェント
│       ├── doc-reviewer.toml    #   ドキュメント品質レビュー
│       └── implementation-validator.toml # 実装品質検証
├── .agents/
│   └── skills/                  # スキル
│       ├── setup-dev/           #   $setup-dev [feature-dir]
│       ├── add-feature/         #   $add-feature [名前]
│       ├── review-docs/         #   $review-docs [パス]
│       ├── steering/            #   作業計画・進捗管理
│       ├── requirements-writing/#   要求定義書作成
│       ├── functional-design/   #   機能設計書作成
│       └── architecture-design/ #   アーキテクチャ設計書作成
└── .steering/                   # 作業ドキュメント（自動生成）
```
