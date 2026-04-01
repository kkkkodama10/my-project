---
name: architecture-design
description: アーキテクチャ設計書（変更差分）を作成するための詳細ガイドとテンプレート。アーキテクチャ設計時にのみ使用。
allowed-tools: Read, Write
---

# アーキテクチャ設計スキル（変更差分版）

このスキルは、既存リポジトリに新機能を追加する際のアーキテクチャ変更差分を設計するためのガイドです。

## 前提条件

### 必須ドキュメント

1. `docs/YYYYMMDD_<feature-name>/requirements.md`（要求定義書）
2. `docs/YYYYMMDD_<feature-name>/functional-design.md`（機能設計書）

### 既存アーキテクチャの理解

設計開始前に必ず:
1. 既存コードベースのディレクトリ構造を確認
2. 主要なアーキテクチャパターン（レイヤー構造、依存関係）をGrepで調査
3. 既存の設定ファイル（package.json, tsconfig.json, Makefile 等）を確認

## 新規プロジェクトとの違い

**このスキルは既存アーキテクチャへの「変更差分」を記述します。**

ゼロからのアーキテクチャ定義ではなく:
- 既存アーキテクチャの何を変更するか
- 何を新規追加するか
- 既存部分への影響は何か

を重点的に記述してください。

## 出力先

```
docs/YYYYMMDD_<feature-name>/architecture.md
```

## テンプレートの参照

アーキテクチャ設計書を作成する際は、次のテンプレートを使用してください: ./template.md
