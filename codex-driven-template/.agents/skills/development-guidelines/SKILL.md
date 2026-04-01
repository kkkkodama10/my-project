---
name: development-guidelines
description: チーム全体で統一された開発プロセスとコーディング規約を確立するための包括的なガイドとテンプレート。開発ガイドライン作成時、コード実装時に使用する。
---

# 開発ガイドラインスキル

チーム開発に必要な2つの要素をカバーします:
1. 実装時のコーディング規約 (implementation-guide.md)
2. 開発プロセスの標準化 (process-guide.md)

## 前提条件

### 推奨ドキュメント

1. `docs/architecture.md` (アーキテクチャ設計書) - 技術スタックの確認
2. `docs/repository-structure.md` (リポジトリ構造) - ディレクトリ構造の確認

## 既存ドキュメントの優先順位

**重要**: `docs/development-guidelines.md` に既存の開発ガイドラインがある場合、
以下の優先順位に従ってください:

1. **既存の開発ガイドライン (`docs/development-guidelines.md`)** - 最優先
2. **このスキルのガイド** - 参考資料
   - ./guides/implementation.md: 汎用的なコーディング規約
   - ./guides/process.md: 汎用的な開発プロセス

**新規作成時**: このスキルのガイドとテンプレートを参照
**更新時**: 既存ガイドラインの構造と内容を維持しながら更新

## 出力先

```
docs/development-guidelines.md
```

## クイックリファレンス

### コード実装時
コード実装時のルールと規約: ./guides/implementation.md

### 開発プロセスの参照／策定時
Git運用、テスト戦略、コードレビュー: ./guides/process.md

### テンプレート
開発ガイドライン作成時: ./template.md

## 使用シーン別ガイド

### 新規開発時
1. ./guides/implementation.md で命名規則・コーディング規約を確認
2. ./guides/process.md でブランチ戦略・PR処理を確認
3. テストを先に書く（TDD）

### コードレビュー時
- ./guides/process.md の「コードレビュープロセス」を参照
- ./guides/implementation.md で規約違反がないか確認

### テスト設計時
- ./guides/process.md の「テスト戦略」
- ./guides/implementation.md の「テストコード」

## チェックリスト

- [ ] コーディング規約が具体例付きで定義されている
- [ ] 命名規則が明確である
- [ ] エラーハンドリングの方針が定義されている
- [ ] ブランチ戦略が決まっている
- [ ] コミットメッセージ規約が明確である
- [ ] テストの種類とカバレッジ目標が設定されている
- [ ] コードレビュープロセスが定義されている
- [ ] CI/CDパイプラインが構築されている
