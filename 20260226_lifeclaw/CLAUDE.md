# LifeClaw

LINEメモ → AI整形 → Notion自動記録のパーソナルライフログシステム。

## 技術スタック

LINE Messaging API / Tailscale Funnel / Docker / OpenClaw / Claude API / Notion API

## ソースコード構成

- `~/.openclaw/workspace/skills/lifelog/SKILL.md` — lifelogスキル定義（LINEメモ→日報整形→Notion書き込み）
- `~/.openclaw/openclaw.json` — OpenClaw設定（ツール制限・LINE連携・スキル許可リスト）
- `~/.openclaw/.env` — Notion APIトークン・データベースID

## 開発ワークフロー

本プロジェクトはドキュメント駆動で開発を進める。ドキュメントは「永続的ドキュメント」と「作業単位のドキュメント」の2層構造で管理する。

### 永続的ドキュメント（`docs/`）

アプリ全体の「何を作るか」と「どう作るか」を定義する恒久的なドキュメント群。基本設計や方針が変わらない限り更新されない。

| ファイル | 役割 |
|----------|------|
| `docs/product-requirements.md` | プロダクトの要求定義書。ユーザー課題、ゴール、スコープ |
| `docs/functional-design.md` | 機能設計書。各機能の振る舞い、入出力、画面/UIフロー |
| `docs/architecture.md` | 技術仕様書。システム構成、技術スタック、データフロー、API仕様 |
| `docs/repository-structure.md` | リポジトリ構造定義書。ディレクトリ構成とファイルの責務 |
| `docs/development-guidelines.md` | 開発ガイドライン。コーディング規約、命名規則、テスト方針、Git運用 |
| `docs/glossary.md` | ユビキタス言語定義。プロジェクト内で使う用語の意味を統一 |

### 作業単位のドキュメント（`.steering/`）

個別の開発タスクごとに作成する作業用ドキュメント。タスクの開始から完了までのライフサイクルを管理する。

```
.steering/[YYYYMMDD]-[開発タイトル]/
├── requirements.md   # 今回の作業の要求内容（何をしたいか、なぜやるか）
├── design.md         # 変更内容の設計（どう実現するか、影響範囲）
└── tasklist.md       # タスクリスト（チェックボックス形式、進捗管理）
```

### 開発の進め方

1. **作業開始時**: `.steering/`に作業ディレクトリを作成し、`requirements.md`で要求を定義する
2. **設計**: `design.md`に変更内容の設計を書く。必要に応じて永続的ドキュメントを参照する
3. **タスク分解**: `tasklist.md`にタスクをチェックボックス形式で列挙する
4. **実装**: タスクリストに沿って実装を進め、完了したらチェックを入れる
5. **完了時**: 永続的ドキュメントへの反映が必要な場合は`docs/`を更新する

## フェーズ

- **MVP**: lifelogスキル作成、Notionデータベース構築、LINE↔OpenClaw↔Notion連携
- **拡張**: 曜日別リマインド、サマリー自動生成、Apple Health連携、RAG検索、ローカルLLM対応
