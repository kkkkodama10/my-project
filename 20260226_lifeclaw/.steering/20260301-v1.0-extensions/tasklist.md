# v1.0 拡張タスクリスト

## R2: 天気・気温の自動記録

- [x] Open-Meteo APIの動作確認（curlで横浜市のデータ取得テスト）
- [ ] Notionデータベースにプロパティ追加（天気: Rich Text、最高気温: Number、最低気温: Number）
- [x] WMOウェザーコード → 日本語変換テーブルの実装
- [x] lifelogスキル（SKILL.md）に天気取得ステップを追加
- [x] Notionの当日レコードに天気データが既存かチェックするロジックの実装
- [x] 天気データ取得 → Notion書き込みの実装（未記録時のみ）
- [x] エラーハンドリング（API失敗時のリトライ、天気のみスキップして日記は続行）
- [ ] 動作確認（実データでの1日分記録テスト、2回目送信でスキップ確認）

## R3: Garmin連携による健康データ自動記録

- [ ] Notionデータベースにプロパティ追加（睡眠時間・深い睡眠・浅い睡眠・REM睡眠・歩数・ストレス・Body Battery・HRV）
- [ ] `services/garmin/` ディレクトリ構成の作成
- [ ] `garmin_client.py` を `workout_daily` から移植・調整
- [ ] `config.py` の作成（Garmin認証 + Notion設定）
- [ ] `notion_writer.py` の作成（LifeClaw Notionスキーマ対応、既存データチェック付き）
- [ ] `main.py` の作成（オーケストレーション）
- [ ] Dockerfile の作成
- [ ] docker-compose.yml への garmin サービス追加
- [ ] lifelogスキルからGarminサイドカーを呼び出す方式の確定と実装
- [ ] Notionの当日レコードに健康データが既存かチェックするロジックの実装
- [ ] `.env` にGarmin認証情報を追加
- [ ] 単体テスト（Garminデータ取得の動作確認）
- [ ] 結合テスト（LINE日記送信 → Garminデータ取得 → Notion書き込みの動作確認）
- [ ] 2回目送信時のスキップ動作確認

## R1: ローカルLLM（Ollama）対応

- [ ] OpenClawのOllama対応状況を調査（公式ドキュメント・ソースコード確認）
- [ ] Ollamaのインストールとモデル（gemma3）のセットアップ
- [ ] Docker内からホストのOllamaへの接続テスト
- [ ] OpenClaw設定の変更（LLMプロバイダーをOllamaに切替）
- [ ] 既存SKILL.mdプロンプトでのJSON出力品質検証
- [ ] 出力品質が不十分な場合のプロンプト調整
- [ ] docker-compose.yml の更新（extra_hosts追加）
- [ ] Claude APIフォールバックの検討・実装
- [ ] エンドツーエンドテスト（LINE → Ollama整形 → Notion記録）

## ドキュメント更新

- [ ] `docs/architecture.md` の更新（天気・Garmin・Ollamaの追記）
- [ ] `docs/functional-design.md` の更新（新機能F5〜F7の追加）
- [ ] `docs/product-requirements.md` の更新（v1.0スコープ反映）
- [ ] `docs/repository-structure.md` の更新（services/garmin 追記）
- [ ] `docs/glossary.md` の更新（新用語追加）
- [ ] `README.md` の更新
