# Auto Diary

Garminヘルスデータ → Claude API → Notion投稿の日記自動生成アプリ（Python）。

## 技術スタック

Python 3.12+ / python-garminconnect / Claude API (claude-haiku-4-5-20251001) / Notion API / python-dotenv

## ドキュメント構造

- `docs/` - 永続的ドキュメント（要求定義・機能設計・技術仕様・開発ガイドライン等）
- `.steering/YYYYMMDD-タイトル/` - 作業単位ドキュメント（requirements.md / design.md / tasklist.md）

## 開発ワークフロー

1. `.steering/`に作業ディレクトリを作成し requirements.md → design.md → tasklist.md の順で進める
2. 実装はタスクリストに沿って進め、完了したらチェックを入れる
3. 必要に応じて `docs/` を更新する

## ソースコード構成

- `src/main.py` - エントリポイント（オーケストレーション）
- `src/garmin_client.py` - Garminデータ取得（睡眠・歩数・ストレス）
- `src/diary_generator.py` - Claude APIで日記生成
- `src/notion_client.py` - Notion投稿
- `src/config.py` - .env読み込み・バリデーション
- `prompts/diary_prompt.txt` - プロンプトテンプレート

## フェーズ

- **Phase 1（現在）**: Garminデータ + Claude API → Notion投稿
- Phase 2: 写真Exifデータで行動日記に拡張
- Phase 3: デバイス使用時間で知的活動を追加
