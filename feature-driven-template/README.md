# Feature-Driven Template

既存リポジトリに新機能を追加するための、Claude Code駆動開発テンプレートです。

## 想定ユースケース

- AI開発に馴染みがないリポジトリに、Claude Codeで新機能を追加したい
- 設計ドキュメント → 計画 → 実装 → 振り返りのサイクルを自動化したい

## セットアップ

### 1. 既存リポジトリにコピー

```bash
# テンプレートの .claude/, ideas/, .steering/, CLAUDE.md をコピー
cp -r feature-driven-template/.claude/ your-repo/.claude/
cp -r feature-driven-template/ideas/ your-repo/ideas/
cp -r feature-driven-template/.steering/ your-repo/.steering/
cp feature-driven-template/CLAUDE.md your-repo/CLAUDE.md
```

### 2. CLAUDE.md の技術スタックを更新

`CLAUDE.md` の `## 技術スタック` セクションを対象リポジトリに合わせて記載してください。

### 3. アイデアを書く

```bash
mkdir ideas/20260401_awesome-feature
vim ideas/20260401_awesome-feature/idea.md
```

### 4. 設計ドキュメント生成

```
/setup-dev 20260401_awesome-feature
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
/add-feature awesome-feature
```

自動的に以下が実行されます：

1. `.steering/YYYYMMDD-awesome-feature/` に作業計画を生成
2. `tasklist.md` に従って実装
3. 品質検証（テスト・lint・型チェック）
4. 振り返り記録

### ドキュメントレビュー

```
/review-docs docs/20260401_awesome-feature/requirements.md
```

完全性・明確性・一貫性・実装可能性・測定可能性の観点でレビュー。

## ワークフロー概要

```
ideas/YYYYMMDD_<feature>/ にアイデアを書く
       |
/setup-dev で3つの設計書を生成
       |
/add-feature で機能を実装
       |
.steering/ に計画 → 実装 → 振り返りを記録
       |
/review-docs で品質チェック
```

## フレームワーク構成

```
├── CLAUDE.md                    # フレームワーク定義
├── ideas/                       # アイデアメモ（入力）
│   └── YYYYMMDD_<feature>/
├── docs/                        # 設計ドキュメント（自動生成）
│   └── YYYYMMDD_<feature>/
├── .claude/
│   ├── settings.json            # スキル許可設定
│   ├── commands/                # ユーザーコマンド
│   │   ├── setup-dev.md         #   /setup-dev [feature-dir]
│   │   ├── add-feature.md       #   /add-feature [名前]
│   │   └── review-docs.md       #   /review-docs [パス]
│   ├── skills/                  # 内部スキル
│   │   ├── steering/            #   作業計画・進捗管理
│   │   ├── requirements-writing/#   要求定義書作成
│   │   ├── functional-design/   #   機能設計書作成
│   │   └── architecture-design/ #   アーキテクチャ設計書作成
│   └── agents/                  # サブエージェント
│       ├── doc-reviewer.md      #   ドキュメント品質レビュー
│       └── implementation-validator.md # 実装品質検証
└── .steering/                   # 作業ドキュメント（自動生成）
```
