# 要求定義: MVP基盤構築

## 何をしたいか

LifeClawのMVPを動作可能な状態にする。LINEでメモを送信し、AIが整形してNotionに記録される一連のフローを実現する。

## なぜやるか

現時点ではドキュメントのみでアプリケーションの実装が存在しない。MVPの基盤（Docker環境・lifelogスキル・Notion連携・リマインド設定）を構築し、実際に使い始められる状態にする。

## 完了条件

1. Docker Compose でOpenClaw Gatewayが起動する
2. Tailscale Funnel 経由でLINE Webhookを受信できる
3. LINEでメモを送ると、lifelogスキルがLLMで整形しNotionに書き込む
4. 同一日付の2回目以降の送信で既存レコードに追記される
5. 毎日22:00 JSTにLINEリマインドが届く
6. セキュリティ設計（最小権限）が適用されている
